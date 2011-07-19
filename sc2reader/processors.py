from collections import defaultdict
from .objects import *
from .utils import key_in_bases, windows_to_unix
from datetime import datetime

def FullProcessor(replay):
    # Populate replay with details
    replay.realm = replay.raw.initData.realm
    replay.map = replay.raw.details.map
    replay.file_time = replay.raw.details.file_time
    replay.unix_timestamp = windows_to_unix(replay.file_time)
    replay.date = datetime.fromtimestamp(replay.unix_timestamp)
    replay.utc_date = datetime.utcfromtimestamp(replay.unix_timestamp)

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

    # Create and add the players based on attribute and details information
    player_index, observer_index = 0, 0
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

        # If this is a human player, push back the initial observer index in the
        # list of all human players we gathered from the initdata file.
        if attributes['Player Type'] == 'Human':
            observer_index += 1

        # Create the player using the current pid and the player name from
        # The details file. This works because players are stored in order
        # of pid intside of the details file. Attributes and Details must be
        # processed together because Details doesn't index players by or store
        # their player ids; Attributes can provide that information and allow
        # for accurate pid mapping even with computers, observers, and open
        # open slots.
        #
        # General information re: each player comes from the following files:
        #   * replay.initData
        #   * replay.details
        #   * replay.attribute.events
        #
        # TODO: get a map of realm,subregion# => subregion in here
        # TODO: recognize current locale and use that instead of western
        # TODO: fill in the LOCALIZED_RACES table
        player = Player(pid,pdata.name,replay)

        player.team = attributes['Teams'+replay.type]
        player.chosen_race = attributes['Race']
        player.difficulty = attributes['Difficulty']
        player.type = attributes['Player Type']
        player.realm = replay.raw.initData.realm
        player.uid = pdata.bnet.uid
        player.subregion = pdata.bnet.subregion
        player.handicap = pdata.handicap
        player.result = pdata.result
        player.actual_race = LOCALIZED_RACES.get(pdata.race, pdata.race)

        # Conversion instructions to the new color object:
        #   color_rgba is the color object itself
        #   color_hex is color.hex
        #   color is str(color)
        player.color = Color(**pdata.color._asdict())

        # Each player can be referenced in a number of different ways,
        # primarily for convenience of access in any given situation.
        replay.people.append(player)
        replay.players.append(player)
        replay.person[pid] = player

    # Create observers out of the leftover names
    all_players = replay.raw.initData.player_names
    for i in range(observer_index,len(all_players)):
        observer = Observer(i+1,all_players[i],replay)
        replay.observers.append(observer)
        replay.people.append(observer)
        replay.person[i+1] = observer

    # Miscellenious people processing
    replay.humans = filter(lambda p: p.type == 'Human', replay.people)

    # Process the packets
    for time, pid, flags, data in replay.raw.message_events.packets:
        replay.packets.append(Packet(time, replay.person[pid], data))

    # Figure out recorder
    packet_senders = map(lambda p: p.player, replay.packets)
    recorders = list(set(replay.humans) - set(packet_senders))
    if len(recorders) == 1:
        replay.recorder = recorders[0]
        replay.recorder.recorder = True
    else:
        raise ValueError("Get Recorder algorithm is broken!")

    # Process the messages
    # TODO: process the message into the Message class
    for message in replay.raw.message_events.messages:
        replay.messages.append(message)

    # Process the teams
    # TODO: Make and use a Team class for this piece
    for player in replay.players:
        replay.teams[player.team].append(player)

    # Copy the events over
    # TODO: the events need to be fixed both on the reader and processor side
    replay.events = replay.raw.game_events
    for event in replay.events:
        if event.is_local:
            # Set up the object cross references
            event.player = replay.person[event.pid]
            event.player.events.append(event)

        # event.apply() #Skip this for now
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

    # TODO: only need to integrate results processing now!
    return replay


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
