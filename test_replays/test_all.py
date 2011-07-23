# Encoding: UTF-8

# Run tests with "py.test" in the project root dir
import os, sys
import pytest
import datetime

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../")))

import sc2reader
from sc2reader.exceptions import ParseError

# Tests for build 17811 replays

def test_standard_1v1():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/1.SC2Replay")

    assert replay.length == (32, 47)
    assert replay.map == "Lost Temple"
    assert replay.build == 17811
    assert replay.release_string == "1.2.2.17811"
    assert replay.speed == "Faster"
    assert replay.type == "1v1"

    assert replay.is_ladder == True
    assert replay.is_private == False

    assert len(replay.players) == 2
    assert replay.person[1].name == "Emperor"
    assert replay.person[2].name == "Boom"
    emperor = replay.person['Emperor']
    assert emperor.team.number == 1
    assert emperor.chosen_race == "Protoss"
    assert emperor.actual_race == "Protoss"
    assert emperor.recorder == False

    boom = replay.person['Boom']
    assert boom.team.number == 2
    assert boom.chosen_race == "Terran"
    assert boom.actual_race == "Terran"
    assert boom.recorder == True

    for player in replay.players:
        assert player.type == "Human"

    # Because it is a 1v1 and the recording player quit, we should know the winner.
    assert emperor.result == "Win"
    assert boom.result == "Loss"

    assert emperor.url == "http://eu.battle.net/sc2/en/profile/520049/1/Emperor/"
    assert boom.url == "http://eu.battle.net/sc2/en/profile/1694745/1/Boom/"

    assert len(replay.messages) == 12
    assert replay.messages[0].text == "hf"
    assert replay.messages[0].sender.name == "Emperor"
    assert replay.messages[1].text == "HEYA"
    assert replay.messages[1].sender.name == "Boom"
    assert replay.messages[2].text == "gl hf"
    assert replay.messages[2].sender.name == "Boom"
    assert replay.messages[3].text == "sry for caps"
    assert replay.messages[3].sender.name == "Boom"
    assert replay.messages[4].text == "^^"
    assert replay.messages[4].sender.name == "Emperor"
    assert replay.messages[5].text == "noppe"
    assert replay.messages[5].sender.name == "Emperor"
    assert replay.messages[6].text == "you greedy bastard"
    assert replay.messages[6].sender.name == "Boom"
    assert replay.messages[7].text == "ggg"
    assert replay.messages[7].sender.name == "Boom"
    assert replay.messages[8].text == "WG"
    assert replay.messages[8].sender.name == "Emperor"
    assert replay.messages[9].text == "wg? :)"
    assert replay.messages[9].sender.name == "Boom"
    assert replay.messages[10].text == "wipe"
    assert replay.messages[10].sender.name == "Emperor"
    assert replay.messages[11].text == "huh?"
    assert replay.messages[11].sender.name == "Boom"

    for msg in replay.messages:
        assert msg.sent_to_all == True

def test_private_category():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/2.SC2Replay")
    assert replay.is_private == True
    assert replay.is_ladder == False

def test_3v3():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/3.SC2Replay")
    assert replay.type == "3v3"

    # Because it's a 3v3 and all of the members of Team 2 quit, we should know the winner.
    assert replay.team[1].result == "Win"
    assert replay.team[2].result == "Loss"

def test_4v4():
    replay = sc2reader.read_file("test_replays/1.2.0.17326/9.SC2Replay")
    assert replay.type == "4v4"

def test_2v2():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/7.SC2Replay")
    assert replay.type == "2v2"

def test_ffa():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/8.SC2Replay")
    assert replay.type == "FFA"

    # Player 'Boom' won because the last building of the last player was destroyed,
    # but the winner cannot be parsed because "Player has left" event isn't generated.
    # Unknown result is the best we can do.
    assert replay.winner_known == False

def test_unknown_winner():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/10.SC2Replay")

    # Recording player (Boom) left second in a 4v4, so the winner shouldn't be known
    assert replay.winner_known == False

def test_random_player():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/3.SC2Replay")

    gogeta = replay.person['Gogeta']
    assert gogeta.chosen_race == "Random"
    assert gogeta.actual_race == "Terran"

def test_random_player2():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/6.SC2Replay")
    permafrost = replay.person["Permafrost"]
    assert permafrost.chosen_race == "Random"
    assert permafrost.actual_race == "Protoss"

def test_us_realm():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/5.SC2Replay")
    assert replay.person['ShadesofGray'].url == "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/"
    assert replay.person['reddawn'].url == "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/"

# TODO: Current problem.. both players are set as the recording players
# Waiting for response https://github.com/arkx/mpyq/issues/closed#issue/7
def test_kr_realm_and_tampered_messages():
    replay = sc2reader.read_file("test_replays/1.1.3.16939/11.SC2Replay")
    assert replay.person['명지대학교'].url == "http://kr.battle.net/sc2/en/profile/258945/1/명지대학교/"
    assert replay.person['티에스엘사기수'].url == "http://kr.battle.net/sc2/en/profile/102472/1/티에스엘사기수/"

    assert replay.messages[0].text == "sc2.replays.net"
    assert replay.messages[5].text == "sc2.replays.net"

    print replay.players[1].chosen_race
    print replay.players[1].actual_race

    print replay.players[0].chosen_race
    print replay.players[0].actual_race

    print replay.map

# TODO: Failing with
# TypeError: Unknown event: 0x4 - 0xe3 at 16
def test_referee():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/14.SC2Replay")

def test_encrypted():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/4.SC2Replay")

def test_observers():
    replay = sc2reader.read_file("test_replays/1.2.2.17811/13.SC2Replay",debug=True)

def test_datetimes():
    # Ignore seconds in comparisons, because they are off by one what is reported by Windows.
    # This might be a little nuance worth investigating at some point.

    # Played at 20 Feb 2011 22:44:48 UTC+2
    replay = sc2reader.read_file("test_replays/1.2.2.17811/1.SC2Replay")
    assert replay.utc_date == datetime.datetime(2011, 2, 20, 20, 44, 47)

    # Played at 21 Feb 2011 00:42:13 UTC+2
    replay = sc2reader.read_file("test_replays/1.2.2.17811/2.SC2Replay")
    assert replay.utc_date == datetime.datetime(2011, 2, 20, 22, 42, 12)

    # Played at 25 Feb 2011 16:36:28 UTC+2
    replay = sc2reader.read_file("test_replays/1.2.2.17811/3.SC2Replay")
    assert replay.utc_date == datetime.datetime(2011, 2, 25, 14, 36, 26)
