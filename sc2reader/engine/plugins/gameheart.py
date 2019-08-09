# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from datetime import datetime
from sc2reader.utils import Length, get_real_type
from sc2reader.objects import Observer, Team
from sc2reader.engine.events import PluginExit
from sc2reader.constants import GAME_SPEED_FACTOR


class GameHeartNormalizer(object):
    """
    normalize a GameHeart replay to:
    1) reset frames to the game start
    2) remove observing players
    3) fix race selection
    4) fix team selection
    If a replay is not a GameHeart replay, it should be left untouched
    Hopefully, the changes here will also extend to other replays that use
    in-game lobbies

    GameHeart games have some constraints we can use here:
    * They are all 1v1's.
    * You can't random in GameHeart
    """

    name = "GameHeartNormalizer"

    PRIMARY_BUILDINGS = dict(Hatchery="Zerg", Nexus="Protoss", CommandCenter="Terran")

    def handleInitGame(self, event, replay):
        # without tracker events game heart games can't be fixed
        if len(replay.tracker_events) == 0:
            yield PluginExit(self, code=0, details=dict())
            return

        start_frame = -1
        actual_players = {}
        for event in replay.tracker_events:
            if start_frame != -1 and event.frame > start_frame + 5:  # fuzz it a little
                break
            if (
                event.name == "UnitBornEvent"
                and event.control_pid
                and event.unit_type_name in self.PRIMARY_BUILDINGS
            ):
                # In normal replays, starting units are born on frame zero.
                if event.frame == 0:
                    yield PluginExit(self, code=0, details=dict())
                    return
                else:
                    start_frame = event.frame
                    actual_players[event.control_pid] = self.PRIMARY_BUILDINGS[
                        event.unit_type_name
                    ]

        self.fix_entities(replay, actual_players)
        self.fix_events(replay, start_frame)

        replay.frames -= start_frame
        replay.game_length = Length(seconds=replay.frames / 16)
        replay.real_type = get_real_type(replay.teams)
        replay.real_length = Length(
            seconds=int(replay.game_length.seconds / GAME_SPEED_FACTOR[replay.speed])
        )
        replay.start_time = datetime.utcfromtimestamp(
            replay.unix_timestamp - replay.real_length.seconds
        )

    def fix_events(self, replay, start_frame):
        # Set back the game clock for all events
        for event in replay.events:
            if event.frame < start_frame:
                event.frame = 0
                event.second = 0
            else:
                event.frame -= start_frame
                event.second = event.frame >> 4

    def fix_entities(self, replay, actual_players):
        # Change the players that aren't playing into observers
        for p in [p for p in replay.players if p.pid not in actual_players]:
            # Fix the slot data to be accurate
            p.slot_data["observe"] = 1
            p.slot_data["team_id"] = None
            obs = Observer(p.sid, p.slot_data, p.uid, p.init_data, p.pid)

            # Because these obs start the game as players the client
            # creates various Beacon units for them.
            obs.units = p.units

            # Remove all references to the old player
            del replay.player[p.pid]
            del replay.entity[p.pid]
            del replay.human[p.uid]
            replay.players.remove(p)
            replay.entities.remove(p)
            replay.humans.remove(p)

            # Create all the necessary references for the new observer
            replay.observer[obs.uid] = obs
            replay.entity[obs.pid] = obs
            replay.human[obs.uid] = obs
            replay.observers.append(obs)
            replay.entities.append(obs)
            replay.humans.append(obs)

        # Maintain order, just in case someone is depending on it
        replay.observers = sorted(replay.observers, key=lambda o: o.sid)
        replay.entities = sorted(replay.entities, key=lambda o: o.sid)
        replay.humans = sorted(replay.humans, key=lambda o: o.sid)

        # Assume one player per team, should be valid for GameHeart games
        replay.team = dict()
        replay.teams = list()
        for index, player in enumerate(replay.players):
            team_id = index + 1
            team = Team(team_id)
            replay.team[team_id] = team
            replay.teams.append(team)
            player.team = team
            team.result = player.result
            player.pick_race = actual_players[player.pid]
            player.play_race = player.pick_race
            team.players = [player]
            team.result = player.result
            if team.result == "Win":
                replay.winner = team
