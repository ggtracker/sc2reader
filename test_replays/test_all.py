# Encoding: UTF-8

# Run tests with "py.test" in the project root dir
import os, sys
import pytest
import datetime

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../")))

import sc2reader
from sc2reader.exceptions import ParseError
from sc2reader.plugins.replay import APMTracker, SelectionTracker

sc2reader.log_utils.log_to_console('INFO')
# Tests for build 17811 replays

class SC2TestFactory(sc2reader.factories.DoubleCachedSC2Factory):
    def __init__(self, cache_dir, max_cache_size=0, **options):
        """cache_dir must be an absolute path, max_cache_size=0 => unlimited"""
        if not cache_dir:
            raise ValueError("cache_dir is now required.")

        super(SC2TestFactory, self).__init__(cache_dir, max_cache_size, **options)

        self.register_plugin('Replay',APMTracker())
        self.register_plugin('Replay',SelectionTracker())


def test_standard_1v1():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/1.SC2Replay")

    assert replay.expansion == 'WoL'
    assert str(replay.length) == "32.47"
    assert replay.map_name == "Lost Temple"
    assert replay.build == 17811
    assert replay.release_string == "1.2.2.17811"
    assert replay.speed == "Faster"
    assert replay.type == "1v1"

    assert replay.is_ladder == True
    assert replay.is_private == False

    assert len(replay.players) == 2
    assert replay.person[1].name == "Emperor"
    assert replay.person[2].name == "Boom"
    emperor = replay.person[1]
    assert emperor.team.number == 1
    assert emperor.pick_race == "Protoss"
    assert emperor.play_race == "Protoss"
    assert emperor.recorder == False

    boom = replay.person[2]
    assert boom.team.number == 2
    assert boom.pick_race == "Terran"
    assert boom.play_race == "Terran"
    assert boom.recorder == True

    for player in replay.players:
        assert player.is_human == True

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
        assert msg.to_all == True

def test_private_category():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/2.SC2Replay")
    assert replay.expansion == 'WoL'
    assert replay.is_private == True
    assert replay.is_ladder == False

def test_3v3():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")
    assert replay.type == "3v3"

    # Because it's a 3v3 and all of the members of Team 2 quit, we should know the winner.
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

    assert replay.winner.players[0].name == 'Boom'

def test_unknown_winner():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/10.SC2Replay")

    # Recording player (Boom) left second in a 4v4, so the winner shouldn't be known
    assert replay.winner == None

def test_random_player():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/3.SC2Replay")

    gogeta = next(player for player in replay.players if player.name == 'Gogeta')
    assert gogeta.pick_race == "Random"
    assert gogeta.play_race == "Terran"

def test_random_player2():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/6.SC2Replay")
    permafrost = next(player for player in replay.players if player.name == 'Permafrost')
    assert permafrost.pick_race == "Random"
    assert permafrost.play_race == "Protoss"

def test_us_realm():
    replay = sc2reader.load_replay("test_replays/1.2.2.17811/5.SC2Replay")
    shadesofgray = next(player for player in replay.players if player.name == 'ShadesofGray')
    reddawn = next(player for player in replay.players if player.name == 'reddawn')
    assert shadesofgray.url == "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/"
    assert reddawn.url == "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/"

# TODO: Current problem.. both players are set as the recording players
# Waiting for response https://github.com/arkx/mpyq/issues/closed#issue/7
def test_kr_realm_and_tampered_messages():
    replay = sc2reader.load_replay("test_replays/1.1.3.16939/11.SC2Replay")
    assert replay.expansion == 'WoL'

    first = next(player for player in replay.players if player.name == '명지대학교')
    second = next(player for player in replay.players if player.name == '티에스엘사기수')

    assert first.url == "http://kr.battle.net/sc2/en/profile/258945/1/명지대학교/"
    assert second.url == "http://kr.battle.net/sc2/en/profile/102472/1/티에스엘사기수/"

    assert replay.messages[0].text == "sc2.replays.net"
    assert replay.messages[5].text == "sc2.replays.net"

    print replay.players[1].pick_race
    print replay.players[1].play_race

    print replay.players[0].pick_race
    print replay.players[0].play_race

    print replay.map

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

        assert replay.expansion == 'HotS'

        player_pids = set( [ player.pid for player in replay.players if player.is_human] )
        ability_pids = set( [ event.player.pid for event in replay.events if 'AbilityEvent' in event.name ] )

        assert ability_pids == player_pids

def test_wol_pids():
    replay = sc2reader.load_replay("test_replays/1.5.4.24540/ggtracker_1471849.SC2Replay")

    assert replay.expansion == 'WoL'

    ability_pids = set( [ event.player.pid for event in replay.events if 'AbilityEvent' in event.name ] )
    player_pids = set( [ player.pid for player in replay.players ] )

    assert ability_pids == player_pids

def test_hots_hatchfun():
    replay = sc2reader.load_replay("test_replays/2.0.0.24247/molten.SC2Replay")
    player_pids = set( [ player.pid for player in replay.players ] )
    spawner_pids = set( [ event.player.pid for event in replay.events if 'TargetAbilityEvent' in event.name and event.ability.name == 'SpawnLarva' ] )
    print "player_pids = {player_pids}, spawner_pids = {spawner_pids}".format(player_pids=player_pids, spawner_pids=spawner_pids)
    assert spawner_pids.issubset(player_pids)

def test_hots_vs_ai():
    replay = sc2reader.load_replay("test_replays/2.0.0.24247/Cloud Kingdom LE (13).SC2Replay")
    assert replay.expansion == 'HotS'
    replay = sc2reader.load_replay("test_replays/2.0.0.24247/Korhal City (19).SC2Replay")
    assert replay.expansion == 'HotS'

def test_oracle_parsing():
    replay = sc2reader.load_replay("test_replays/2.0.3.24764/ggtracker_1571740.SC2Replay")
    assert replay.expansion == 'HotS'
    oracles = [unit for unit in replay.objects.values() if unit.name=='Oracle']
    assert len(oracles) == 2

def test_resume_from_replay():
    replay = sc2reader.load_replay("test_replays/2.0.3.24764/resume_from_replay.SC2Replay")

def test_clan_players():
    replay = sc2reader.load_replay("test_replays/2.0.4.24944/Lunar Colony V.SC2Replay")
    assert replay.expansion == 'WoL'
    assert len(replay.people) == 4

def test_WoL_204():
    replay = sc2reader.load_replay("test_replays/2.0.4.24944/ggtracker_1789768.SC2Replay")
    assert replay.expansion == 'WoL'
    assert len(replay.people) == 2

def test_send_resources():
    replay = sc2reader.load_replay("test_replays/2.0.4.24944/Backwater Complex (15).SC2Replay")

def test_cn_replays():
    replay = sc2reader.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")
    assert replay.gateway == 'cn'
    assert replay.expansion == 'WoL'

def test_plugins():
    CACHE_DIR = os.environ.get('GGFACTORY_CACHE_DIR',None)
    factory = SC2TestFactory(cache_dir=CACHE_DIR)
    replay = factory.load_replay("test_replays/2.0.5.25092/cn1.SC2Replay")

