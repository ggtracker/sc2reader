# -*- coding: UTF-8 -*-

import datetime
import json

# Newer unittest features aren't built in for python 2.6
import sys
if sys.version_info[:2] <= (2, 7):
    import unittest2 as unittest
else:
    import unittest

import sc2reader
sc2reader.log_utils.log_to_console("INFO")


class TestReplays(unittest.TestCase):

    @unittest.expectedFailure
    def test_teams(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/13.SC2Replay")
        self.assertNotEqual(replay.player[1].team.number, replay.player[2].team.number)

        replay = sc2reader.load_replay("test_replays/2.0.8.25604/mlg1.SC2Replay")
        self.assertNotEqual(replay.player[1].team.number, replay.player[2].team.number)

    def test_private_category(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
        self.assertEquals(replay.expansion, "WoL")
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

        self.assertEqual(emperor.url, "http://eu.battle.net/sc2/en/profile/520049/1/Emperor/")
        self.assertEqual(boom.url, "http://eu.battle.net/sc2/en/profile/1694745/1/Boom/")

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
        self.assertEquals(replay.type, "2v2")

    def test_3v3(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
        self.assertEquals(replay.type, "3v3")

        # Because it"s a 3v3 and all of the members of Team 2 quit, we should know the winner.
        self.assertEquals(replay.team[1].result, "Win")
        self.assertEquals(replay.team[2].result, "Loss")

    def test_4v4(self):
        replay = sc2reader.load_replay("test_replays/1.2.0.17326/9.SC2Replay")
        self.assertEquals(replay.type, "4v4")

    def test_ffa(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/8.SC2Replay")
        self.assertEquals(replay.type, "FFA")
        self.assertEquals(replay.winner.players[0].name, "Boom")

    def test_unknown_winner(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/10.SC2Replay")

        # Recording player (Boom) left second in a 4v4, so the winner shouldn"t be known
        self.assertEquals(replay.winner, None)

    def test_random_player(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
        gogeta = next(player for player in replay.players if player.name == "Gogeta")
        self.assertEquals(gogeta.pick_race, "Random")
        self.assertEquals(gogeta.play_race, "Terran")

        replay = sc2reader.load_replay("test_replays/1.2.2.17811/6.SC2Replay")
        permafrost = next(player for player in replay.players if player.name == "Permafrost")
        self.assertEquals(permafrost.pick_race, "Random")
        self.assertEquals(permafrost.play_race, "Protoss")

    def test_us_realm(self):
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/5.SC2Replay")
        shadesofgray = [player for player in replay.players if player.name == "ShadesofGray"][0]
        reddawn = [player for player in replay.players if player.name == "reddawn"][0]
        self.assertEquals(shadesofgray.url, "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/")
        self.assertEquals(reddawn.url, "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/")

    def test_kr_realm_and_tampered_messages(self):
        """
        # TODO: Current problem.. both players are set as the recording players
        # Waiting for response https://github.com/arkx/mpyq/issues/closed#issue/7
        """
        replay = sc2reader.load_replay("test_replays/1.1.3.16939/11.SC2Replay")
        self.assertEquals(replay.expansion, "WoL")
        first = [player for player in replay.players if player.name == "명지대학교"][0]
        second = [player for player in replay.players if player.name == "티에스엘사기수"][0]
        self.assertEquals(first.url, "http://kr.battle.net/sc2/en/profile/258945/1/명지대학교/")
        self.assertEquals(second.url, "http://kr.battle.net/sc2/en/profile/102472/1/티에스엘사기수/")
        self.assertEquals(replay.messages[0].text, "sc2.replays.net")
        self.assertEquals(replay.messages[5].text, "sc2.replays.net")

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
        self.assertEquals(replay.end_time, datetime.datetime(2011, 2, 20, 20, 44, 47))

        # Played at 21 Feb 2011 00:42:13 UTC+2
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
        self.assertEquals(replay.end_time, datetime.datetime(2011, 2, 20, 22, 42, 12))

        # Played at 25 Feb 2011 16:36:28 UTC+2
        replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
        self.assertEquals(replay.end_time, datetime.datetime(2011, 2, 25, 14, 36, 26))

    def test_hots_pids(self):
        for replayfilename in [
            "test_replays/2.0.3.24764/Akilon Wastes (10).SC2Replay",
            "test_replays/2.0.3.24764/Antiga Shipyard (3).SC2Replay",
            "test_replays/2.0.0.24247/molten.SC2Replay",
            "test_replays/2.0.0.23925/Akilon Wastes.SC2Replay",
            ]:

            replay = sc2reader.load_replay(replayfilename)
            self.assertEquals(replay.expansion, "HotS")
            player_pids = set([player.pid for player in replay.players if player.is_human])
            ability_pids = set([event.player.pid for event in replay.events if "AbilityEvent" in event.name])
            self.assertEquals(ability_pids, player_pids)

    def test_wol_pids(self):
        replay = sc2reader.load_replay("test_replays/1.5.4.24540/ggtracker_1471849.SC2Replay")
        self.assertEquals(replay.expansion, "WoL")
        ability_pids = set([event.player.pid for event in replay.events if "AbilityEvent" in event.name])
        player_pids = set([player.pid for player in replay.players])
        self.assertEquals(ability_pids, player_pids)

    def test_hots_hatchfun(self):
        replay = sc2reader.load_replay("test_replays/2.0.0.24247/molten.SC2Replay")
        player_pids = set([ player.pid for player in replay.players])
        spawner_pids = set([ event.player.pid for event in replay.events if "TargetAbilityEvent" in event.name and event.ability.name == "SpawnLarva"])
        self.assertTrue(spawner_pids.issubset(player_pids))

    def test_hots_vs_ai(self):
        replay = sc2reader.load_replay("test_replays/2.0.0.24247/Cloud Kingdom LE (13).SC2Replay")
        self.assertEquals(replay.expansion, "HotS")
        replay = sc2reader.load_replay("test_replays/2.0.0.24247/Korhal City (19).SC2Replay")
        self.assertEquals(replay.expansion, "HotS")

    def test_oracle_parsing(self):
        replay = sc2reader.load_replay("test_replays/2.0.3.24764/ggtracker_1571740.SC2Replay")
        self.assertEquals(replay.expansion, "HotS")
        oracles = [unit for unit in replay.objects.values() if unit.name == "Oracle"]
        self.assertEquals(len(oracles), 2)

    def test_resume_from_replay(self):
        replay = sc2reader.load_replay("test_replays/2.0.3.24764/resume_from_replay.SC2Replay")

    def test_clan_players(self):
        replay = sc2reader.load_replay("test_replays/2.0.4.24944/Lunar Colony V.SC2Replay")
        self.assertEquals(replay.expansion, "WoL")
        self.assertEquals(len(replay.people), 4)

    def test_WoL_204(self):
        replay = sc2reader.load_replay("test_replays/2.0.4.24944/ggtracker_1789768.SC2Replay")
        self.assertEquals(replay.expansion, "WoL")
        self.assertEquals(len(replay.people), 2)

    def test_send_resources(self):
        replay = sc2reader.load_replay("test_replays/2.0.4.24944/Backwater Complex (15).SC2Replay")

    def test_cn_replays(self):
        replay = sc2reader.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")
        self.assertEquals(replay.gateway, "cn")
        self.assertEquals(replay.expansion, "WoL")

    def test_plugins(self):
        from sc2reader.plugins.replay import APMTracker, SelectionTracker, toJSON
        factory = sc2reader.factories.SC2Factory()
        factory.register_plugin("Replay", APMTracker())
        factory.register_plugin("Replay", SelectionTracker())
        factory.register_plugin("Replay", toJSON())
        replay = factory.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")

        # Load and quickly check the JSON output consistency
        result = json.loads(replay)
        self.assertEquals(result["map_name"], u"生化实验区")
        self.assertEquals(result["players"][2]["name"], "ImYoonA")
        self.assertEquals(result["players"][2]["avg_apm"], 84.52332657200812)
        self.assertEquals(result["release"], "2.0.5.25092")
        self.assertEquals(result["game_length"], 986)
        self.assertEquals(result["real_length"], 704)
        self.assertEquals(result["gateway"], "cn")
        self.assertEquals(result["game_fps"], 16.0)
        self.assertTrue(result["is_ladder"])


if __name__ == '__main__':
    unittest.main()
