# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from sc2reader import objects, utils


def GameHeartNormalizer(replay):
    """
    normalize a GameHeart replay to:
    1) reset frames to the game start
    2) remove observing players
    3) fix race selection
    4) fix team selection
    If a replay is not a GameHeart replay, it should be left untouched
    Hopefully, the changes here will also extend to other replays that use
    in-game lobbies

    This makes a few assumptions
    1) 1v1 game
    """

    PRIMARY_BUILDINGS = set (['Hatchery', 'Nexus', 'CommandCenter'])
    start_frame = -1
    actual_players = {}

    if not replay.tracker_events:
        return replay  # necessary using this strategy

    for event in replay.tracker_events:
        if start_frame != -1 and event.frame > start_frame + 5:  # fuzz it a little
            break
        if event.name == 'UnitBornEvent' and event.control_pid and \
                event.unit_type_name in PRIMARY_BUILDINGS:
            if event.frame == 0:  # it's a normal, legit replay
                return replay
            start_frame = event.frame
            actual_players[event.control_pid] = event.unit.race

    # set game length starting with the actual game start
    replay.frames -= start_frame
    replay.game_length = utils.Length(seconds=replay.frames / 16)

    # this should cover events of all types
    # not nuking entirely because there are initializations that may be relevant
    for event in replay.events:
        if event.frame < start_frame:
            event.frame = 0
            event.second = 0
        else:
            event.frame -= start_frame
            event.second = event.frame >> 4

    # replay.humans is okay because they're all still humans
    # replay.person and replay.people is okay because the mapping is still true

    # add observers
    # not reinitializing because players appear to have the properties of observers
    # TODO in a better world, these players would get reinitialized
    replay.observers += [player for player in replay.players if not player.pid in actual_players]
    for observer in replay.observers:
        observer.is_observer = True
        observer.team_id = None

    # reset team
    # reset teams
    replay.team = {}
    replay.teams = []

    # reset players
    replay.players = [player for player in replay.players if player.pid in actual_players]
    for i, player in enumerate(replay.players):
        race = actual_players[player.pid]
        player.pick_race = race
        player.play_race = race

        team = objects.Team(i + 1)
        team.players.append(player)
        team.result = player.result
        player.team = team
        replay.team[i + 1] = team
        replay.teams.append(team)

        # set winner
        if team.result == 'Win':
            replay.winner = team

    # clear observers out of the players list
    for pid in replay.player.keys():
        if not pid in actual_players:
            del replay.player[pid]

    return replay
