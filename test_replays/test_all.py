# Encoding: UTF-8

# Run tests with "py.test" in the project root dir
import os
import sys
import pytest
import datetime
import json

root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../")
sys.path.insert(0, os.path.normpath(root_dir))

import sc2reader
from sc2reader.plugins.replay import APMTracker, SelectionTracker, toJSON

sc2reader.log_utils.log_to_console("INFO")


def test_standard_1v1():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/1.SC2Replay")

    assert replay.expansion == "WoL"
    assert str(replay.length) == "32.47"
    assert str(replay.game_length) == "32.47"
    assert str(replay.real_length) == "23.25"
    assert replay.map_name == "Lost Temple"
    assert replay.build == 17811
    assert replay.release_string == "1.2.2.17811"
    assert replay.speed == "Faster"
    assert replay.type == "1v1"

    assert replay.is_ladder is True
    assert replay.is_private is False

    assert len(replay.players) == 2
    assert replay.person[1].name == "Emperor"
    assert replay.person[2].name == "Boom"
    emperor = replay.person[1]
    assert emperor.team.number == 1
    assert emperor.pick_race == "Protoss"
    assert emperor.play_race == "Protoss"
    assert emperor.recorder is False

    boom = replay.person[2]
    assert boom.team.number == 2
    assert boom.pick_race == "Terran"
    assert boom.play_race == "Terran"
    assert boom.recorder is True

    for player in replay.players:
        assert player.is_human is True

    # Because it is a 1v1 and the recording player quit, we should know the winner.
    assert emperor.result == "Win"
    assert boom.result == "Loss"

    assert emperor.url == "http://eu.battle.net/sc2/en/profile/520049/1/Emperor/"
    assert boom.url == "http://eu.battle.net/sc2/en/profile/1694745/1/Boom/"

    assert len(replay.messages) == 12
    assert replay.messages[0].text == "hf"
    assert replay.messages[0].player.name == "Emperor"
    assert replay.messages[1].text == "HEYA"
    assert replay.messages[1].player.name == "Boom"
    assert replay.messages[2].text == "gl hf"
    assert replay.messages[2].player.name == "Boom"
    assert replay.messages[3].text == "sry for caps"
    assert replay.messages[3].player.name == "Boom"
    assert replay.messages[4].text == "^^"
    assert replay.messages[4].player.name == "Emperor"
    assert replay.messages[5].text == "noppe"
    assert replay.messages[5].player.name == "Emperor"
    assert replay.messages[6].text == "you greedy bastard"
    assert replay.messages[6].player.name == "Boom"
    assert replay.messages[7].text == "ggg"
    assert replay.messages[7].player.name == "Boom"
    assert replay.messages[8].text == "WG"
    assert replay.messages[8].player.name == "Emperor"
    assert replay.messages[9].text == "wg? :)"
    assert replay.messages[9].player.name == "Boom"
    assert replay.messages[10].text == "wipe"
    assert replay.messages[10].player.name == "Emperor"
    assert replay.messages[11].text == "huh?"
    assert replay.messages[11].player.name == "Boom"

    for msg in replay.messages:
        assert msg.to_all is True


def test_private_category():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
    assert replay.expansion == "WoL"
    assert replay.is_private == True
    assert replay.is_ladder == False

def test_3v3():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
    assert replay.type == "3v3"

    # Because it"s a 3v3 and all of the members of Team 2 quit, we should know the winner.
    assert replay.team[1].result == "Win"
    assert replay.team[2].result == "Loss"


def test_4v4():
    replay = sc2reader.load_replay("test_replays/1.2.0.17326/9.SC2Replay")
    assert replay.type == "4v4"


def test_2v2():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/7.SC2Replay")
    assert replay.type == "2v2"


def test_ffa():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/8.SC2Replay")
    assert replay.type == "FFA"

    assert replay.winner.players[0].name == "Boom"


def test_unknown_winner():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/10.SC2Replay")

    # Recording player (Boom) left second in a 4v4, so the winner shouldn"t be known
    assert replay.winner is None


def test_random_player():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")

    gogeta = next(player for player in replay.players if player.name == "Gogeta")
    assert gogeta.pick_race == "Random"
    assert gogeta.play_race == "Terran"


def test_random_player2():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/6.SC2Replay")
    permafrost = next(player for player in replay.players if player.name == "Permafrost")
    assert permafrost.pick_race == "Random"
    assert permafrost.play_race == "Protoss"


def test_us_realm():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/5.SC2Replay")
    shadesofgray = next(player for player in replay.players if player.name == "ShadesofGray")
    reddawn = next(player for player in replay.players if player.name == "reddawn")
    assert shadesofgray.url == "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/"
    assert reddawn.url == "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/"


# TODO: Current problem.. both players are set as the recording players
# Waiting for response https://github.com/arkx/mpyq/issues/closed#issue/7
def test_kr_realm_and_tampered_messages():
    replay = sc2reader.load_replay("test_replays/1.1.3.16939/11.SC2Replay")
    assert replay.expansion == "WoL"

    first = next(player for player in replay.players if player.name == "명지대학교")
    second = next(player for player in replay.players if player.name == "티에스엘사기수")

    assert first.url == "http://kr.battle.net/sc2/en/profile/258945/1/명지대학교/"
    assert second.url == "http://kr.battle.net/sc2/en/profile/102472/1/티에스엘사기수/"

    assert replay.messages[0].text == "sc2.replays.net"
    assert replay.messages[5].text == "sc2.replays.net"

    print replay.players[1].pick_race
    print replay.players[1].play_race

    print replay.players[0].pick_race
    print replay.players[0].play_race

    print replay.map_name


# TODO: Failing with
# TypeError: Unknown event: 0x4 - 0xe3 at 16
def test_referee():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/14.SC2Replay")


def test_encrypted():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/4.SC2Replay")


def test_observers():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/13.SC2Replay",debug=True)


def test_datetimes():
    # Ignore seconds in comparisons, because they are off by one what is reported by Windows.
    # This might be a little nuance worth investigating at some point.

    # Played at 20 Feb 2011 22:44:48 UTC+2
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/1.SC2Replay")
    assert replay.end_time == datetime.datetime(2011, 2, 20, 20, 44, 47)

    # Played at 21 Feb 2011 00:42:13 UTC+2
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
    assert replay.end_time == datetime.datetime(2011, 2, 20, 22, 42, 12)

    # Played at 25 Feb 2011 16:36:28 UTC+2
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
    assert replay.end_time == datetime.datetime(2011, 2, 25, 14, 36, 26)


def test_hots_pids():
    for replayfilename in [
        "test_replays/2.0.3.24764/Akilon Wastes (10).SC2Replay",
        "test_replays/2.0.3.24764/Antiga Shipyard (3).SC2Replay",
        "test_replays/2.0.0.24247/molten.SC2Replay",
        "test_replays/2.0.0.23925/Akilon Wastes.SC2Replay",
        ]:
        print "Processing {fname}".format(fname=replayfilename)
        replay = sc2reader.load_replay(replayfilename)

        assert replay.expansion == "HotS"

        player_pids = set([player.pid for player in replay.players if player.is_human])
        ability_pids = set([event.player.pid for event in replay.events if "AbilityEvent" in event.name])

        assert ability_pids == player_pids


def test_wol_pids():
    replay = sc2reader.load_replay("test_replays/1.5.4.24540/ggtracker_1471849.SC2Replay")

    assert replay.expansion == "WoL"

    ability_pids = set([event.player.pid for event in replay.events if "AbilityEvent" in event.name])
    player_pids = set([player.pid for player in replay.players])

    assert ability_pids == player_pids


def test_hots_hatchfun():
    replay = sc2reader.load_replay("test_replays/2.0.0.24247/molten.SC2Replay")
    player_pids = set([ player.pid for player in replay.players])
    spawner_pids = set([ event.player.pid for event in replay.events if "TargetAbilityEvent" in event.name and event.ability.name == "SpawnLarva"])
    print "player_pids = {player_pids}, spawner_pids = {spawner_pids}".format(player_pids=player_pids, spawner_pids=spawner_pids)
    assert spawner_pids.issubset(player_pids)


def test_hots_vs_ai():
    replay = sc2reader.load_replay("test_replays/2.0.0.24247/Cloud Kingdom LE (13).SC2Replay")
    assert replay.expansion == "HotS"
    replay = sc2reader.load_replay("test_replays/2.0.0.24247/Korhal City (19).SC2Replay")
    assert replay.expansion == "HotS"


def test_oracle_parsing():
    replay = sc2reader.load_replay("test_replays/2.0.3.24764/ggtracker_1571740.SC2Replay")
    assert replay.expansion == "HotS"
    oracles = [unit for unit in replay.objects.values() if unit.name=="Oracle"]
    assert len(oracles) == 2


def test_resume_from_replay():
    replay = sc2reader.load_replay("test_replays/2.0.3.24764/resume_from_replay.SC2Replay")


def test_clan_players():
    replay = sc2reader.load_replay("test_replays/2.0.4.24944/Lunar Colony V.SC2Replay")
    assert replay.expansion == "WoL"
    assert len(replay.people) == 4


def test_WoL_204():
    replay = sc2reader.load_replay("test_replays/2.0.4.24944/ggtracker_1789768.SC2Replay")
    assert replay.expansion == "WoL"
    assert len(replay.people) == 2


def test_send_resources():
    replay = sc2reader.load_replay("test_replays/2.0.4.24944/Backwater Complex (15).SC2Replay")


def test_cn_replays():
    replay = sc2reader.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")
    assert replay.gateway == "cn"
    assert replay.expansion == "WoL"


def test_plugins():
    factory = sc2reader.factories.SC2Factory()
    factory.register_plugin("Replay", APMTracker())
    factory.register_plugin("Replay", SelectionTracker())
    factory.register_plugin("Replay", toJSON())
    replay = factory.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")

    # Load and quickly check the JSON output consistency
    result = json.loads(replay)
    assert result["map_name"] == u"生化实验区"
    assert result["players"][2]["name"] == "ImYoonA"
    assert result["players"][2]["avg_apm"] == 84.52332657200812
    assert result["release"] == "2.0.5.25092"
    assert result["game_length"] == 986
    assert result["real_length"] == 704
    assert result["gateway"] == "cn"
    assert result["game_fps"] == 16.0
    assert result["is_ladder"] is True
