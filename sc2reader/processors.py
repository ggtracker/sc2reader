from collections import defaultdict
from .objects import *
from .utils import key_in_bases, windows_to_unix, Length
from datetime import datetime
from .constants import REGIONS

def Full(replay):
    # Populate replay with details
    # TODO: Test this with different levels of file read.
    # TODO: Change config.py to work with this
    # TODO: remove legacy code, restructure config.py: just one processor now
    if 'initData' in replay.raw and replay.raw.initData.map_data:
        replay.gateway = replay.raw.initData.map_data[0].gateway

    if 'details' in replay.raw:
        replay.map = replay.raw.details.map
        replay.file_time = replay.raw.details.file_time
        replay.unix_timestamp = windows_to_unix(replay.file_time)
        replay.date = datetime.fromtimestamp(replay.unix_timestamp)
        replay.utc_date = datetime.utcfromtimestamp(replay.unix_timestamp)

    if 'attributes_events' in replay.raw:
        # Organize the attribute data to be useful
        attribute_data = defaultdict(dict)
        for attr in replay.raw.attributes_events:
            attribute_data[attr.player][attr.name] = attr.value

        # Populate replay with attributes
        replay.speed = attribute_data[16]['Game Speed']
        replay.category = attribute_data[16]['Category']
        replay.type = attribute_data[16]['Game Type']
        replay.is_ladder = (replay.category == "Ladder")
        replay.is_private = (replay.category == "Private")

    #If we don't atleast have details and attributes_events we can go no further
    if not ('details' in replay.raw and 'attributes_events' in replay.raw):
        return replay

    # Create and add the players based on attribute and details information
    player_index, observer_index, default_region = 0, 0, ''
    player_data = replay.raw.details.players
    for pid, attributes in sorted(attribute_data.iteritems()):

        # We've already processed the global attributes
        if pid == 16: continue

        # Open Slots are skipped because it doesn't seem useful to store
        # an "Open" player to fill a spot that would otherwise be empty.
        if attributes['Player Type'] == 'Open': continue

        # Get the player data from the details file, increment the index to
        # Keep track of which player we are processing
        pdata = player_data[player_index]
        player_index += 1

        # If this is a human player, push back the initial observer index in
        # the list of all human players we gathered from the initdata file.
        if attributes['Player Type'] == 'Human':
            observer_index += 1

        # Create the player using the current pid and the player name from
        # The details file. This works because players are stored in order
        # of pid intside of the details file. Attributes and Details must be
        # processed together because Details doesn't index players by or
        # store their player ids; Attributes can provide that information
        # and allow for accurate pid mapping even with computers, observers,
        # and open open slots.
        #
        # General information re: each player comes from the following files
        #   * replay.initData
        #   * replay.details
        #   * replay.attribute.events
        #
        # TODO: recognize current locale and use that instead of western
        # TODO: fill in the LOCALIZED_RACES table
        player = Player(pid,pdata.name,replay)

        # Cross reference the player and team lookups
        team_number = attributes['Teams'+replay.type]
        if not team_number in replay.team:
            replay.team[team_number] = Team(team_number)
            replay.teams.append(replay.team[team_number])
        replay.team[team_number].players.append(player)
        player.team = replay.team[team_number]

        # Do basic win/loss processing from details data
        if   pdata.result == 1: player.team.result = "Win"
        elif pdata.result == 2: player.team.result = "Loss"

        player.pick_race = attributes['Race']
        player.play_race = LOCALIZED_RACES.get(pdata.race, pdata.race)
        player.difficulty = attributes['Difficulty']
        player.type = attributes['Player Type']
        player.uid = pdata.bnet.uid
        player.subregion = pdata.bnet.subregion
        player.handicap = pdata.handicap

        # We need initData for the gateway which is required to build the url!
        if 'initData' in replay.raw and replay.gateway:
            player.gateway = replay.gateway
            if player.type == 'Human':
                player.region = REGIONS[replay.gateway][player.subregion]
                default_region = player.region

        # Conversion instructions to the new color object:
        #   color_rgba is the color object itself
        #   color_hex is color.hex
        #   color is str(color)
        player.color = Color(**pdata.color._asdict())

        # Each player can be referenced in a number of different ways,
        # primarily for convenience of access in any given situation.
        replay.people.append(player)
        replay.players.append(player)
        replay.player[pid] = player
        replay.person[pid] = player

    #Create an store an ordered lineup string
    for team in replay.teams:
        team.lineup = sorted(player.play_race[0].upper() for player in team)

    if 'initData' in replay.raw:
        # Assign the default region to computer players for consistency
        # We know there will be a default region because there must be
        # atleast 1 human player or we wouldn't have a replay.
        for player in replay.players:
            if player.type == 'Computer':
                player.region = default_region

        # Create observers out of the leftover names gathered from initData
        all_players = replay.raw.initData.player_names
        for i in range(observer_index,len(all_players)):
            observer = Observer(i+1,all_players[i],replay)
            replay.observers.append(observer)
            replay.people.append(observer)
            replay.person[i+1] = observer

    # Miscellenious people processing
    replay.humans = filter(lambda p: p.type == 'Human', replay.people)

    if 'message_events' in replay.raw:
        # Process the packets
        for time, pid, flags, data in replay.raw.message_events.packets:
            replay.packets.append(Packet(time, replay.person[pid], data))

        # Process the messages
        # TODO: process the message into the Message class
        for time, pid, flags, target, text in replay.raw.message_events.messages:
            message = Message(time, replay.person[pid], target, text)
            replay.messages.append(message)

        # Figure out recorder
        packet_senders = map(lambda p: p.player, replay.packets)
        recorders = list(set(replay.humans) - set(packet_senders))
        if len(recorders) == 1:
            replay.recorder = recorders[0]
            replay.recorder.recorder = True
        else:
            raise ValueError("Get Recorder algorithm is broken!")

    #If we don't have game events, this is as far as we can go
    if not 'game_events' in replay.raw:
        return replay

    # Copy the events over
    # TODO: the events need to be fixed both on the reader and processor side
    replay.events = replay.raw.game_events
    for event in replay.events:
        if event.is_local:
            # Set up the object cross references
            event.player = replay.person[event.pid]
            event.player.events.append(event)

        event.apply()
        l = replay.events_by_type[event.name]
        l.append(event)

    # Gather data for APM measurements
    for event in replay.events:
        if event.is_local and event.is_player_action:
            player = event.player
            if not player.is_observer:
                # Count up the APS, APM
                second, minute = event.second, event.second/60
                player.aps[event.second] += 1
                player.apm[minute] += 1
                player.avg_apm += 1

    # Average the APM for actual players
    for player in replay.players:
        if player.events:
            event_minutes = player.events[-1].second/60.0
            if event_minutes:
                player.avg_apm /= event_minutes

    # If the details file didn't have all the results, try to figure them out.
    # Our first approach simulates the teams losing one by one by stepping
    # through the recorded player leave events and marking losses as the teams
    # run out of players.
    #
    # TODO: See if this ever tells us more than details file does by default!
    if filter(lambda t: t.result == "Unknown", replay.teams):

        #Get the total players for each team so we can start the count down
        pcount = dict([team.number, len(team.players)] for team in replay.teams)

        for event in replay.events_by_type['PlayerLeave']:
            team = replay.player[event.pid].team

            # Observer leave events are recorded too, filter them out
            if event.pid in replay.player:

                # If this was the last person on the team, that team loses
                if pcount[team.number] == 1:
                    team.result = "Loss"
                    del pcount[team.number]

                    #If only one team has players left, they have won!
                    if len(pcount) == 1:
                        replay.team[pcount.keys()[0]].result = "Win"
                        break

                else:
                    pcount[team.number] -= 1

        # Our player-leave approach didn't determine a winner. If there are only
        # two remaining teams and the recorder is the only player on one of them
        # then his team must have lost since his leave event isn't recorded.
        #
        # The above definitely true if another there are two or more teams left
        # or the other team has two people left. If there is one team left with
        # only one person remaining then, if he wins by destroying all the
        # opponent's buildings it doesn't generate leave events for the other
        # player.
        #
        # Also if there is a tie in any situation there may not be leave events.
        #
        # TODO: Figure out how to handle ties, if we even can
        # TODO: Find some replays that actually have ties?
        else:
            #We can't determine anything else without the recorder
            if 'message_events' in replay.raw:

                # If the recorder is the last person on his team, this obviously
                # doesn't apply for recorders who are observers
                team = replay.recorder.team
                if replay.recorder.pid in replay.players and pcount[team.number] == 1:

                    # Get all other teams with at least 2 players left:
                    conditions = lambda p: p[0] != team.number and p[1] > 1
                    big_teams = filter(conditions, pcount.iteritems())

                    # If there are any big teams left or more than one 1 person
                    # team left this is definitely either a loss or a really
                    # akward tie between 3 or more people on 2 or more teams.
                    #
                    # Since I don't think ties can be detected, ignore that case
                    if len(pcount) > 2 or big_teams:
                        replay.recorder.team.result = "Loss"
                        del pcount[replay.recorder.team.number]

                        # If that leaves only one team left standing, they won!
                        if len(pcount) == 1:
                            replay.team[pcount.keys()[0]].result = "Win"

                    # Since there were only two teams of 1 person each remaining
                    # we can't know if this was a win by building destruction,
                    # loss, or a tie, so leave them as unknown result for now.
                    # TODO: verify that this is the right thing to do
                    else:
                        pass

    return replay

"""
def PeopleProcessor(replay):
    obs_players = list(replay.player_names)
    for player in replay.players:
        try:
            obs_players.remove(player.name)
        except ValueError:
            pass #Must be a computer player!!

    for pid,name in enumerate(obs_players):
        replay.observers.append(Observer(pid+len(replay.players)+1,name,replay))

    for person in replay.observers+replay.players:
        replay.people.append(person)
        replay.person[person.pid] = person

    return replay

def AttributeProcessor(replay):
    data = defaultdict(dict)
    for attr in replay.attributes:
        data[attr.player][attr.name] = attr.value

    #Get global settings first
    replay.speed = data[16]['Game Speed']

    #TODO: Do we need the category variable at this point?
    replay.category = data[16]['Category']
    replay.is_ladder = (replay.category == "Ladder")
    replay.is_private = (replay.category == "Private")

    replay.type = data[16]['Game Type']

    #Set player attributes as available, requires already populated player list
    for pid, attributes in data.iteritems():
        if pid != 16:
            if attributes['Player Type'] == 'Open':
                print "Open Player {0}".format(pid)

            if attributes['Player Type'] == 'Computer':
                print "Computer Player {0}".format(pid)
                player = Player(pid,"Player {0}".format(pid),replay)
                replay.people.append(player)
                replay.person[pid] = player

            if attributes['Player Type'] in ('Human','Computer'):
                player = replay.person[pid]
                player.color_text = attributes['Color']
                player.team = attributes['Teams'+replay.type]
                player.choosen_race = attributes['Race']
                player.difficulty = attributes['Difficulty']
                player.type = attributes['Player Type']

    print repr(replay.person.keys())
    return replay

def RecorderProcessor(replay):
    recorders = list(replay.people)
    for person in list(replay.people):
        if person.pid in replay.other_people:
            recorders.remove(person)

    if len(recorders) == 1:
        replay.recorder = recorders[0]
        replay.recorder.recorder = True

    return replay

def MessageProcessor(replay):
    for message in replay.messages:
        try:
            message.sender = replay.person[message.sender_id]
        except KeyError:
            #Some sites will add messages as a non-existant player
            #In this instances, just drop the messages
            pass

    return replay

def TeamsProcessor(replay):
    for player in replay.players:
        replay.teams[player.team].append(player)

    return replay

def EventProcessor(replay):
    replay.events_by_type = defaultdict(list)
    for event in replay.events:
        if event.is_local:
            person = replay.person[event.pid]
            event.player = person
            person.events.append(event)

        event.apply()
        replay.events_by_type[event.name].append(event)

    return replay

#####################################################

def ApmProcessor(replay):
    # Set up needed variables
    for player in replay.players:
        player.avg_apm = 0
        player.aps = dict() # Doesn't contain seconds with zero actions
        player.apm = dict() # Doesn't contain minutes with zero actions
    # Gather data
    for event in replay.events:
        if event.is_local and event.is_player_action:
            person = event.player
            if not person.is_observer:
                # Calculate APS, APM and average
                if event.second in person.aps:
                    person.aps[event.second] += 1
                else:
                    person.aps[event.second] = 1

                minute = event.second/60
                if minute in person.apm:
                    person.apm[minute] += 1
                else:
                    person.apm[minute] = 1

                person.avg_apm += 1

    # Average the APM for actual players
    for player in replay.players:
        if player.events:
            event_minutes = player.events[-1].second/60.0
            if event_minutes:
                player.avg_apm /= event_minutes
            else:
                player.avg_apm = 0
        else:
            player.avg_apm = 0

    return replay

#####################################################

def ResultsProcessor(replay):
    def process_results(replay):
        #Knowing the team results, map results to the players as well
        for player in replay.players:
            player.result = replay.results[player.team]

    # Check if replay file has recorded the winner
    remaining = set()
    for player in replay.players:
        if player.result == 1:
            replay.results[player.team] = "Won"
        elif player.result == 2:
            replay.results[player.team] = "Lost"
        else:
            remaining.add(player.team)
    if len(remaining) == 0:
        process_results(replay)
        return replay

    #Remove players from the teams as they drop out of the game
    replay.results = dict([team, len(players)] for team, players in replay.teams.iteritems())

    for event in replay.events_by_type['PlayerLeave']:
        #Some observer actions seem to be recorded, they aren't on teams anyway
        #Their pid will always be higher than the players
        if event.pid <= len(replay.players):
            team = replay.person[event.pid].team
            replay.results[team] -= 1

    #mark all teams with no players left as losing, save the rest of the teams
    remaining = set()
    for team, count in replay.results.iteritems():
        if count == 0:
            replay.results[team] = "Lost"
        else:
            remaining.add(team)

    #If, at the end, only one team remains then that team has won
    if len(remaining) == 1:
        replay.results[remaining.pop()] = "Won"

    #Because you can also end the game by destroying all buildings, games
    #with 1 player teams can't be known unless all other players leave
    #we also can't do this if replay.recorder is unknown
    elif replay.type != 'FFA' and replay.type != '1v1' and replay.recorder:
        #The other results are unknown except in the (common) case that the
        #recorder is the last one on his team to leave. In this case, the
        #result for his team can be known
        for team in set(remaining):
            #the new set above is important because you shouldn't modify
            #elements in collections that you are currently looping over
            if team == replay.recorder.team and replay.results[team] == 1:
                replay.results[team] = "Lost"
                remaining.remove(team)
            else:
                replay.results[team] = "Unknown"

        #If, at the end, only one team remains then that team has won
        if len(remaining) == 1:
            replay.results[remaining.pop()] = "Won"
            replay.winner_known = True

    #If the winner can't be known mark all remaining player.result as unknown
    else:
        for team in remaining:
            replay.results[team] = "Unknown"

    process_results(replay)

    return replay
"""
