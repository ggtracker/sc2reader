from __future__ import absolute_import

from datetime import datetime

from collections import defaultdict

from sc2reader.constants import REGIONS, LOCALIZED_RACES
from sc2reader.objects import Player, Message, Color, Observer, Team, Packet
from sc2reader.utils import windows_to_unix


def Full(replay):
    # Populate replay with details
    if 'initData' in replay.raw and replay.raw.initData.map_data:
        replay.gateway = replay.raw.initData.map_data[0].gateway

        #Expand this special case mapping
        if replay.gateway == 'sg':
            replay.gateway = 'sea'

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

    #If we don't at least have details and attributes_events we can go no further
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
        # of pid inside of the details file. Attributes and Details must be
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
        # at least 1 human player or we wouldn't have a replay.
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

    # Miscellaneous people processing
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
            replay.player[pid].messages.append(message)

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

        # Because applying the events is slow, make it configurable
        if replay.opt.apply: event.apply()

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
                    # awkward tie between 3 or more people on 2 or more teams.
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
