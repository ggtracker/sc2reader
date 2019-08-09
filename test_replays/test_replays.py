# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
from xml.dom import minidom

# Newer unittest features aren't built in for python 2.6
import sys

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest
# StringIO was changed in python 3
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import sc2reader
from sc2reader.exceptions import CorruptTrackerFileError
from sc2reader.events.game import GameEvent
from sc2reader.objects import Player

sc2reader.log_utils.log_to_console("INFO")


class TestReplays(unittest.TestCase):
    def test_teams(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/13.SC2Replay")
        self.assertNotEqual(replay.player[1].team.number, replay.player[2].team.number)

        replay = sc2reader.load_replay("test_replays/2.0.8.25604/mlg1.SC2Replay")
        self.assertNotEqual(replay.player[1].team.number, replay.player[2].team.number)

    def test_private_category(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
        self.assertEqual(replay.expansion, "WoL")
        self.assertTrue(replay.is_private, True)
        self.assertFalse(replay.is_ladder, False)

    def test_standard_1v1(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/1.SC2Replay")

        self.assertEqual(replay.expansion, "WoL")
        self.assertEqual(str(replay.length), "32.47")
        self.assertEqual(str(replay.game_length), "32.47")
        self.assertEqual(str(replay.real_length), "23.25")
        self.assertEqual(replay.map_name, "Lost Temple")
        self.assertEqual(replay.build, 17811)
        self.assertEqual(replay.release_string, "1.2.2.17811")
        self.assertEqual(replay.speed, "Faster")
        self.assertEqual(replay.type, "1v1")

        self.assertTrue(replay.is_ladder)
        self.assertFalse(replay.is_private)

        self.assertEqual(len(replay.players), 2)
        self.assertEqual(replay.person[1].name, "Emperor")
        self.assertEqual(replay.person[2].name, "Boom")

        emperor = replay.person[1]
        self.assertEqual(emperor.team.number, 1)
        self.assertEqual(emperor.pick_race, "Protoss")
        self.assertEqual(emperor.play_race, "Protoss")
        # self.assertFalse(emperor.recorder)

        boom = replay.person[2]
        self.assertEqual(boom.team.number, 2)
        self.assertEqual(boom.pick_race, "Terran")
        self.assertEqual(boom.play_race, "Terran")
        # self.assertTrue(boom.recorder)

        for player in replay.players:
            self.assertTrue(player.is_human)

        # Because it is a 1v1 and the recording player quit, we should know the winner.
        self.assertEqual(emperor.result, "Win")
        self.assertEqual(boom.result, "Loss")

        self.assertEqual(
            emperor.url, "http://eu.battle.net/sc2/en/profile/520049/1/Emperor/"
        )
        self.assertEqual(
            boom.url, "http://eu.battle.net/sc2/en/profile/1694745/1/Boom/"
        )

        self.assertEqual(len(replay.messages), 12)
        self.assertEqual(replay.messages[0].text, "hf")
        self.assertEqual(replay.messages[0].player.name, "Emperor")
        self.assertEqual(replay.messages[1].text, "HEYA")
        self.assertEqual(replay.messages[1].player.name, "Boom")
        self.assertEqual(replay.messages[2].text, "gl hf")
        self.assertEqual(replay.messages[2].player.name, "Boom")
        self.assertEqual(replay.messages[3].text, "sry for caps")
        self.assertEqual(replay.messages[3].player.name, "Boom")
        self.assertEqual(replay.messages[4].text, "^^")
        self.assertEqual(replay.messages[4].player.name, "Emperor")
        self.assertEqual(replay.messages[5].text, "noppe")
        self.assertEqual(replay.messages[5].player.name, "Emperor")
        self.assertEqual(replay.messages[6].text, "you greedy bastard")
        self.assertEqual(replay.messages[6].player.name, "Boom")
        self.assertEqual(replay.messages[7].text, "ggg")
        self.assertEqual(replay.messages[7].player.name, "Boom")
        self.assertEqual(replay.messages[8].text, "WG")
        self.assertEqual(replay.messages[8].player.name, "Emperor")
        self.assertEqual(replay.messages[9].text, "wg? :)")
        self.assertEqual(replay.messages[9].player.name, "Boom")
        self.assertEqual(replay.messages[10].text, "wipe")
        self.assertEqual(replay.messages[10].player.name, "Emperor")
        self.assertEqual(replay.messages[11].text, "huh?")
        self.assertEqual(replay.messages[11].player.name, "Boom")

        for msg in replay.messages:
            self.assertTrue(msg.to_all)

    def test_2v2(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/7.SC2Replay")
        self.assertEqual(replay.type, "2v2")

    def test_3v3(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
        self.assertEqual(replay.type, "3v3")

        # Because it"s a 3v3 and all of the members of Team 2 quit, we should know the winner.
        self.assertEqual(replay.team[1].result, "Win")
        self.assertEqual(replay.team[2].result, "Loss")

    def test_4v4(self):
        replay = sc2reader.load_replay("test_replays/1.2.0.17326/9.SC2Replay")
        self.assertEqual(replay.type, "4v4")

    def test_ffa(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/8.SC2Replay")
        self.assertEqual(replay.type, "FFA")
        self.assertEqual(replay.winner.players[0].name, "Boom")

    def test_unknown_winner(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/10.SC2Replay")

        # Recording player (Boom) left second in a 4v4, so the winner shouldn"t be known
        self.assertEqual(replay.winner, None)

    def test_random_player(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
        gogeta = next(player for player in replay.players if player.name == "Gogeta")
        self.assertEqual(gogeta.pick_race, "Random")
        self.assertEqual(gogeta.play_race, "Terran")

        replay = sc2reader.load_replay("test_replays/1.2.2.17811/6.SC2Replay")
        permafrost = next(
            player for player in replay.players if player.name == "Permafrost"
        )
        self.assertEqual(permafrost.pick_race, "Random")
        self.assertEqual(permafrost.play_race, "Protoss")

    def test_us_realm(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/5.SC2Replay")
        shadesofgray = [
            player for player in replay.players if player.name == "ShadesofGray"
        ][0]
        reddawn = [player for player in replay.players if player.name == "reddawn"][0]
        self.assertEqual(
            shadesofgray.url,
            "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/",
        )
        self.assertEqual(
            reddawn.url, "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/"
        )

    def test_kr_realm_and_tampered_messages(self):
        """
        # TODO: Current problem.. both players are set as the recording players
        # Waiting for response https://github.com/arkx/mpyq/issues/closed#issue/7
        """
        replay = sc2reader.load_replay("test_replays/1.1.3.16939/11.SC2Replay")
        self.assertEqual(replay.expansion, "WoL")
        first = [player for player in replay.players if player.name == "명지대학교"][0]
        second = [player for player in replay.players if player.name == "티에스엘사기수"][0]
        self.assertEqual(
            first.url, "http://kr.battle.net/sc2/en/profile/258945/1/명지대학교/"
        )
        self.assertEqual(
            second.url, "http://kr.battle.net/sc2/en/profile/102472/1/티에스엘사기수/"
        )
        self.assertEqual(replay.messages[0].text, "sc2.replays.net")
        self.assertEqual(replay.messages[5].text, "sc2.replays.net")

    def test_referee(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/14.SC2Replay")

    def test_encrypted(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/4.SC2Replay")

    def test_observers(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/13.SC2Replay")

    def test_datetimes(self):
        # Ignore seconds in comparisons, because they are off by one what is reported by Windows.
        # This might be a little nuance worth investigating at some point.

        # Played at 20 Feb 2011 22:44:48 UTC+2
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/1.SC2Replay")
        self.assertEqual(replay.end_time, datetime.datetime(2011, 2, 20, 20, 44, 47))

        # Played at 21 Feb 2011 00:42:13 UTC+2
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
        self.assertEqual(replay.end_time, datetime.datetime(2011, 2, 20, 22, 42, 12))

        # Played at 25 Feb 2011 16:36:28 UTC+2
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
        self.assertEqual(replay.end_time, datetime.datetime(2011, 2, 25, 14, 36, 26))

    def test_hots_pids(self):
        for replayfilename in [
            "test_replays/2.0.3.24764/Akilon Wastes (10).SC2Replay",
            "test_replays/2.0.3.24764/Antiga Shipyard (3).SC2Replay",
            "test_replays/2.0.0.24247/molten.SC2Replay",
            "test_replays/2.0.0.23925/Akilon Wastes.SC2Replay",
        ]:

            replay = sc2reader.load_replay(replayfilename)
            self.assertEqual(replay.expansion, "HotS")
            player_pids = set(
                [player.pid for player in replay.players if player.is_human]
            )
            ability_pids = set(
                [
                    event.player.pid
                    for event in replay.events
                    if "CommandEvent" in event.name
                ]
            )
            self.assertEqual(ability_pids, player_pids)

    def test_wol_pids(self):
        replay = sc2reader.load_replay(
            "test_replays/1.5.4.24540/ggtracker_1471849.SC2Replay"
        )
        self.assertEqual(replay.expansion, "WoL")
        ability_pids = set(
            [
                event.player.pid
                for event in replay.events
                if "CommandEvent" in event.name
            ]
        )
        player_pids = set([player.pid for player in replay.players])
        self.assertEqual(ability_pids, player_pids)

    def test_hots_hatchfun(self):
        replay = sc2reader.load_replay("test_replays/2.0.0.24247/molten.SC2Replay")
        player_pids = set([player.pid for player in replay.players])
        spawner_pids = set(
            [
                event.player.pid
                for event in replay.events
                if "TargetUnitCommandEvent" in event.name
                and event.ability.name == "SpawnLarva"
            ]
        )
        self.assertTrue(spawner_pids.issubset(player_pids))

    def test_hots_vs_ai(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.0.24247/Cloud Kingdom LE (13).SC2Replay"
        )
        self.assertEqual(replay.expansion, "HotS")
        replay = sc2reader.load_replay(
            "test_replays/2.0.0.24247/Korhal City (19).SC2Replay"
        )
        self.assertEqual(replay.expansion, "HotS")

    def test_oracle_parsing(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.3.24764/ggtracker_1571740.SC2Replay"
        )
        self.assertEqual(replay.expansion, "HotS")
        oracles = [unit for unit in replay.objects.values() if unit.name == "Oracle"]
        self.assertEqual(len(oracles), 2)

    def test_resume_from_replay(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.3.24764/resume_from_replay.SC2Replay"
        )
        self.assertTrue(replay.resume_from_replay)
        self.assertEqual(replay.resume_method, 0)

    def test_clan_players(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.4.24944/Lunar Colony V.SC2Replay"
        )
        self.assertEqual(replay.expansion, "WoL")
        self.assertEqual(len(replay.people), 4)

    def test_WoL_204(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.4.24944/ggtracker_1789768.SC2Replay"
        )
        self.assertEqual(replay.expansion, "WoL")
        self.assertEqual(len(replay.people), 2)

    def test_send_resources(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.4.24944/Backwater Complex (15).SC2Replay"
        )

    def test_cn_replays(self):
        replay = sc2reader.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")
        self.assertEqual(replay.region, "cn")
        self.assertEqual(replay.expansion, "WoL")

    def test_unit_types(self):
        """ sc2reader#136 regression test """
        replay = sc2reader.load_replay("test_replays/2.0.8.25604/issue136.SC2Replay")
        hellion_times = [
            u.started_at for u in replay.players[0].units if u.name == "Hellion"
        ]
        hellbat_times = [
            u.started_at for u in replay.players[0].units if u.name == "BattleHellion"
        ]
        self.assertEqual(hellion_times, [5180, 5183])
        self.assertEqual(hellbat_times, [6736, 6741, 7215, 7220, 12004, 12038])

    @unittest.expectedFailure
    def test_outmatched_pids(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.8.25604/issue131_arid_wastes.SC2Replay"
        )
        self.assertEqual(replay.players[0].pid, 1)
        self.assertEqual(replay.players[1].pid, 3)
        self.assertEqual(replay.players[2].pid, 4)

        replay = sc2reader.load_replay("test_replays/2.0.8.25604/issue135.SC2Replay")
        self.assertEqual(replay.players[0].pid, 1)
        self.assertEqual(replay.players[1].pid, 2)
        self.assertEqual(replay.players[2].pid, 4)

        replay = sc2reader.load_replay("test_replays/2.0.8.25604/mlg1.SC2Replay")
        self.assertEqual(replay.players[0].pid, 1)
        self.assertEqual(replay.players[1].pid, 2)
        self.assertEqual(len(replay.players), 2)
        self.assertEqual(len(replay.people), 3)

    @unittest.expectedFailure
    def test_map_info(self):
        replay = sc2reader.load_replay(
            "test_replays/1.5.3.23260/ggtracker_109233.SC2Replay", load_map=True
        )
        self.assertEqual(replay.map.map_info.tile_set, "Avernus")
        self.assertEqual(replay.map.map_info.fog_type, "Dark")
        self.assertEqual(replay.map.map_info.width, 176)
        self.assertEqual(replay.map.map_info.height, 160)
        self.assertEqual(replay.map.map_info.camera_top, 134)
        self.assertEqual(replay.map.map_info.camera_left, 14)
        self.assertEqual(replay.map.map_info.camera_right, 162)
        self.assertEqual(replay.map.map_info.camera_bottom, 14)
        controllers = [(p.pid, p.control) for p in replay.map.map_info.players]
        self.assertEqual(controllers, [(0, 3), (1, 1), (2, 1), (15, 4)])

    def test_engine_plugins(self):
        from sc2reader.engine.plugins import ContextLoader, APMTracker, SelectionTracker

        replay = sc2reader.load_replay(
            "test_replays/2.0.5.25092/cn1.SC2Replay",
            engine=sc2reader.engine.GameEngine(
                plugins=[ContextLoader(), APMTracker(), SelectionTracker()]
            ),
        )

        code, details = replay.plugins["ContextLoader"]
        self.assertEqual(code, 0)
        self.assertEqual(details, dict())

    @unittest.expectedFailure
    def test_factory_plugins(self):
        from sc2reader.factories.plugins.replay import (
            APMTracker,
            SelectionTracker,
            toJSON,
        )

        factory = sc2reader.factories.SC2Factory()
        factory.register_plugin("Replay", APMTracker())
        factory.register_plugin("Replay", SelectionTracker())
        factory.register_plugin("Replay", toJSON())
        replay = factory.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")

        # Load and quickly check the JSON output consistency
        result = json.loads(replay)
        self.assertEqual(result["map_name"], "生化实验区")
        self.assertEqual(result["players"][2]["name"], "ImYoonA")
        self.assertEqual(result["players"][2]["avg_apm"], 84.52332657200812)
        self.assertEqual(result["release"], "2.0.5.25092")
        self.assertEqual(result["game_length"], 986)
        self.assertEqual(result["real_length"], 704)
        self.assertEqual(result["region"], "cn")
        self.assertEqual(result["game_fps"], 16.0)
        self.assertTrue(result["is_ladder"])

    def test_gameheartnormalizer_plugin(self):
        from sc2reader.engine.plugins import GameHeartNormalizer

        sc2reader.engine.register_plugin(GameHeartNormalizer())

        # Not a GameHeart game!
        replay = sc2reader.load_replay("test_replays/2.0.0.24247/molten.SC2Replay")
        player_pids = set([player.pid for player in replay.players])
        spawner_pids = set(
            [
                event.player.pid
                for event in replay.events
                if "TargetUnitCommandEvent" in event.name
                and event.ability.name == "SpawnLarva"
            ]
        )
        self.assertTrue(spawner_pids.issubset(player_pids))

        replay = sc2reader.load_replay("test_replays/gameheart/gameheart.SC2Replay")
        self.assertEqual(replay.events[0].frame, 0)
        self.assertEqual(replay.game_length.seconds, 636)
        self.assertEqual(len(replay.observers), 5)
        self.assertEqual(replay.players[0].name, "SjoWBBII")
        self.assertEqual(replay.players[0].play_race, "Terran")
        self.assertEqual(replay.players[1].name, "Stardust")
        self.assertEqual(replay.players[1].play_race, "Protoss")
        self.assertEqual(len(replay.teams), 2)
        self.assertEqual(replay.teams[0].players[0].name, "SjoWBBII")
        self.assertEqual(replay.teams[1].players[0].name, "Stardust")
        self.assertEqual(replay.winner, replay.teams[1])

        replay = sc2reader.load_replay("test_replays/gameheart/gh_sameteam.SC2Replay")
        self.assertEqual(replay.events[0].frame, 0)
        self.assertEqual(replay.game_length.seconds, 424)
        self.assertEqual(len(replay.observers), 5)
        self.assertEqual(replay.players[0].name, "EGJDRC")
        self.assertEqual(replay.players[0].play_race, "Zerg")
        self.assertEqual(replay.players[1].name, "LiquidTaeJa")
        self.assertEqual(replay.players[1].play_race, "Terran")
        self.assertEqual(len(replay.teams), 2)
        self.assertEqual(replay.teams[0].players[0].name, "EGJDRC")
        self.assertEqual(replay.teams[1].players[0].name, "LiquidTaeJa")
        self.assertEqual(replay.winner, replay.teams[0])

    def test_replay_event_order(self):
        replay = sc2reader.load_replay("test_replays/event_order.SC2Replay")

    def test_creepTracker(self):
        from sc2reader.engine.plugins import CreepTracker

        for replayfilename in [
            "test_replays/2.0.8.25605/ggtracker_3621322.SC2Replay",
            "test_replays/2.0.8.25605/ggtracker_3621402.SC2Replay",
            "test_replays/2.0.8.25605/ggtracker_3663861.SC2Replay",
            "test_replays/2.0.8.25605/ggtracker_3695400.SC2Replay",
            "test_replays/3.1.2/6494799.SC2Replay",
        ]:
            factory = sc2reader.factories.SC2Factory()
            pluginEngine = sc2reader.engine.GameEngine(plugins=[CreepTracker()])
            replay = factory.load_replay(
                replayfilename, engine=pluginEngine, load_map=True, load_level=4
            )

            for player_id in replay.player:
                if replay.player[player_id].play_race == "Zerg":
                    assert replay.player[player_id].max_creep_spread[1] > 0
                    assert replay.player[player_id].creep_spread_by_minute[0] > 0
        #                print("MCS", replay.player[player_id].max_creep_spread)
        #                print("CSBM", replay.player[player_id].creep_spread_by_minute)

        replay = factory.load_replay(
            "test_replays/2.0.8.25605/ggtracker_3621402.SC2Replay",
            load_map=True,
            engine=pluginEngine,
            load_level=4,
        )
        assert replay.player[2].max_creep_spread == (840, 24.83)
        assert replay.player[2].creep_spread_by_minute[420] == 9.4
        assert replay.player[2].creep_spread_by_minute[780] == 22.42

    def test_bad_unit_ids(self):
        with self.assertRaises(CorruptTrackerFileError):
            replay = sc2reader.load_replay(
                "test_replays/2.0.11.26825/bad_unit_ids_1.SC2Replay", load_level=4
            )
        with self.assertRaises(CorruptTrackerFileError):
            replay = sc2reader.load_replay(
                "test_replays/2.0.9.26147/bad_unit_ids_2.SC2Replay", load_level=4
            )

    def test_daedalus_point(self):
        replay = sc2reader.load_replay(
            "test_replays/2.0.11.26825/DaedalusPoint.SC2Replay"
        )

    def test_reloaded(self):
        replay = sc2reader.load_replay(
            "test_replays/2.1.3.28667/Habitation Station LE (54).SC2Replay"
        )

    def test_214(self):
        replay = sc2reader.load_replay(
            "test_replays/2.1.4/Catallena LE.SC2Replay", load_level=4
        )

    def test_lotv1(self):
        replay = sc2reader.load_replay("test_replays/lotv/lotv1.SC2Replay")
        self.assertEqual(replay.expansion, "LotV")
        replay = sc2reader.load_replay("test_replays/lotv/lotv2.SC2Replay")
        self.assertEqual(replay.expansion, "LotV")

    def test_lotv_creepTracker(self):
        from sc2reader.engine.plugins import CreepTracker

        for replayfilename in ["test_replays/4.0.0.59587/1.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            pluginEngine = sc2reader.engine.GameEngine(plugins=[CreepTracker()])
            replay = factory.load_replay(
                replayfilename, engine=pluginEngine, load_map=True
            )

            is_at_least_one_zerg_in_game = False
            for player_id in replay.player:
                if replay.player[player_id].play_race == "Zerg":
                    is_at_least_one_zerg_in_game = True
                    assert replay.player[player_id].max_creep_spread != 0
                    assert replay.player[player_id].creep_spread_by_minute
            assert is_at_least_one_zerg_in_game

    def test_lotv_map(self):
        for replayfilename in ["test_replays/4.0.0.59587/1.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename, load_level=1, load_map=True)

    def test_30(self):
        replay = sc2reader.load_replay("test_replays/3.0.0.38215/first.SC2Replay")
        replay = sc2reader.load_replay("test_replays/3.0.0.38215/second.SC2Replay")
        replay = sc2reader.load_replay("test_replays/3.0.0.38215/third.SC2Replay")

    def test_31(self):
        for i in range(1, 5):
            print("DOING {}".format(i))
            replay = sc2reader.load_replay("test_replays/3.1.0/{}.SC2Replay".format(i))

    def test_30_map(self):
        for replayfilename in ["test_replays/3.0.0.38215/third.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename, load_level=1, load_map=True)

    def test_30_apms(self):
        from sc2reader.factories.plugins.replay import (
            APMTracker,
            SelectionTracker,
            toJSON,
        )

        factory = sc2reader.factories.SC2Factory()
        factory.register_plugin("Replay", APMTracker())
        replay = factory.load_replay("test_replays/3.0.0.38215/fourth.SC2Replay")
        for player in replay.players:
            if player.name == "Owl":
                print(player.name, player.avg_apm)
                self.assertTrue(player.avg_apm > 110)

    def test_38749(self):
        replay = sc2reader.load_replay("test_replays/3.0.0.38749/1.SC2Replay")
        self.assertEqual(replay.expansion, "HotS")
        replay = sc2reader.load_replay("test_replays/3.0.0.38749/2.SC2Replay")
        self.assertEqual(replay.expansion, "HotS")

    def test_38996(self):
        replay = sc2reader.load_replay("test_replays/3.0.0.38996/1.SC2Replay")
        self.assertEqual(replay.expansion, "LotV")
        replay = sc2reader.load_replay("test_replays/3.0.0.38996/2.SC2Replay")
        self.assertEqual(replay.expansion, "LotV")

    def test_funny_minerals(self):
        replay = sc2reader.load_replay("test_replays/3.1.0/centralprotocol.SC2Replay")
        replay.load_map()
        xmldoc = minidom.parseString(replay.map.archive.read_file("Objects"))
        itemlist = xmldoc.getElementsByTagName("ObjectUnit")
        mineralPosStrs = [
            ou.attributes["Position"].value
            for ou in itemlist
            if "MineralField" in ou.attributes["UnitType"].value
        ]
        mineralFieldNames = list(
            set(
                [
                    ou.attributes["UnitType"].value
                    for ou in itemlist
                    if "MineralField" in ou.attributes["UnitType"].value
                ]
            )
        )
        # print(mineralFieldNames)
        self.assertTrue(len(mineralPosStrs) > 0)

    def test_dusk(self):
        replay = sc2reader.load_replay("test_replays/3.1.0/dusktowers.SC2Replay")
        self.assertEqual(replay.expansion, "LotV")

    def test_32(self):
        replay = sc2reader.load_replay("test_replays/3.2.0/1.SC2Replay")
        self.assertTrue(replay is not None)

    def test_33(self):
        for replaynum in range(1, 4):
            replay = sc2reader.load_replay(
                "test_replays/3.3.0/{}.SC2Replay".format(replaynum)
            )
            self.assertTrue(replay is not None)

    def test_33_shift_click_calldown_mule(self):
        replay = sc2reader.load_replay("test_replays/3.3.0/ggissue48.SC2Replay")

        def efilter(e):
            return hasattr(e, "ability") and e.ability_name == "CalldownMULE"

        self.assertEqual(len(list(filter(efilter, replay.events))), 29)

    def test_33_shift_click_spawn_larva(self):
        replay = sc2reader.load_replay("test_replays/3.3.0/ggissue49.SC2Replay")

        def efilter(e):
            return hasattr(e, "ability") and e.ability_name == "SpawnLarva"

        self.assertEqual(len(list(filter(efilter, replay.events))), 23)

    def test_34(self):
        replay = sc2reader.load_replay("test_replays/3.4.0/issueYY.SC2Replay")
        self.assertEqual(replay.expansion, "LotV")

    def test_lotv_time(self):
        replay = sc2reader.load_replay("test_replays/lotv/lotv1.SC2Replay")
        self.assertEqual(replay.length.seconds, 1002)
        self.assertEqual(replay.real_length.seconds, 1002)

    def test_37(self):
        replay = sc2reader.load_replay("test_replays/3.7.0/1.SC2Replay")
        replay = sc2reader.load_replay("test_replays/3.7.0/2.SC2Replay")

    def test_312(self):
        for replayfilename in ["test_replays/3.12/Honorgrounds.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename, load_level=0)
            replay = factory.load_replay(replayfilename, load_level=1)

    def test_316(self):
        for replayfilename in ["test_replays/3.16/AbyssalReef.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_54518(self):
        for replayfilename in [
            "test_replays/3.14.0.54518/1.SC2Replay",
            "test_replays/3.14.0.54518/2.SC2Replay",
            "test_replays/3.14.0.54518/3.SC2Replay",
        ]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_59587(self):
        for replayfilename in ["test_replays/4.0.0.59587/1.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_64469(self):
        for replayfilename in ["test_replays/4.3.0.64469/1.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_coop(self):
        for replayfilename in ["test_replays/coop/CoA.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_65895(self):
        for replayfilename in ["test_replays/4.4.0.65895/1.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_event_print(self):
        replay = sc2reader.load_replay("test_replays/lotv/lotv1.SC2Replay")
        sys.stdout = capturedOutput = StringIO()
        for event in replay.events:
            print(event)
        self.assertIn("PlayerLeaveEvent", capturedOutput.getvalue())
        sys.stdout = sys.__stdout__
        capturedOutput.close()

    def test_70154(self):
        for replayfilename in ["test_replays/4.7.0.70154/1.SC2Replay"]:
            factory = sc2reader.factories.SC2Factory()
            replay = factory.load_replay(replayfilename)

    def test_anonymous_replay(self):
        replayfilename = "test_replays/4.1.2.60604/1.SC2Replay"
        factory = sc2reader.factories.SC2Factory()
        replay = factory.load_replay(replayfilename)

    def test_game_event_string(self):
        time = "00.01"
        # Global
        player = MockPlayer()
        player.name = "TestPlayer"
        player.play_race = "TestRace"
        event = GameEvent(16, 16)
        event.player = player
        self.assertEqual("{0}\t{1:<15} ".format(time, "Global"), event._str_prefix())

        # Player with name
        player = MockPlayer()
        player.name = "TestPlayer"
        player.play_race = "TestRace"
        event = GameEvent(16, 1)
        event.player = player
        self.assertEqual("{0}\t{1:<15} ".format(time, player.name), event._str_prefix())

        # No Player
        player = MockPlayer()
        event = GameEvent(16, 1)
        self.assertEqual("{0}\t{1:<15} ".format(time, "no name"), event._str_prefix())

        # Player without name
        player = MockPlayer()
        player.play_race = "TestRace"
        player.pid = 1
        event = GameEvent(16, 1)
        event.player = player
        self.assertEqual(
            "{0}\tPlayer {1} - ({2}) ".format(time, player.pid, player.play_race),
            event._str_prefix(),
        )


class TestGameEngine(unittest.TestCase):
    class TestEvent(object):
        name = "TestEvent"

        def __init__(self, value):
            self.value = value

        def __str__(self):
            return self.value

    class TestPlugin1(object):
        name = "TestPlugin1"

        def handleInitGame(self, event, replay):
            yield TestGameEngine.TestEvent("b")
            yield TestGameEngine.TestEvent("c")

        def handleTestEvent(self, event, replay):
            if event.value == "d":
                yield sc2reader.engine.PluginExit(
                    self, code=1, details=dict(msg="Fail!")
                )
            else:
                yield TestGameEngine.TestEvent("d")

        def handleEndGame(self, event, replay):
            yield TestGameEngine.TestEvent("g")

    class TestPlugin2(object):
        name = "TestPlugin2"

        def handleInitGame(self, event, replay):
            replay.engine_events = list()

        def handleTestEvent(self, event, replay):
            replay.engine_events.append(event)

        def handlePluginExit(self, event, replay):
            yield TestGameEngine.TestEvent("e")

        def handleEndGame(self, event, replay):
            yield TestGameEngine.TestEvent("f")

    class MockReplay(object):
        def __init__(self, events):
            self.events = events

    def test_plugin1(self):
        engine = sc2reader.engine.GameEngine()
        engine.register_plugin(self.TestPlugin1())
        engine.register_plugin(self.TestPlugin2())
        replay = self.MockReplay([self.TestEvent("a")])
        engine.run(replay)
        self.assertEqual("".join(str(e) for e in replay.engine_events), "bdecaf")
        self.assertEqual(replay.plugin_failures, ["TestPlugin1"])
        self.assertEqual(replay.plugin_result["TestPlugin1"], (1, dict(msg="Fail!")))
        self.assertEqual(replay.plugin_result["TestPlugin2"], (0, dict()))


class MockPlayer(object):
    def __init__(self):
        self.name = None
        self.play_race = None
        self.pid = None


if __name__ == "__main__":
    unittest.main()
