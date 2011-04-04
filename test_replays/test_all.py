# Encoding: UTF-8

# Run tests with "py.test" in the project root dir
import os, sys
import pytest
import datetime

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../")))

import sc2reader
from sc2reader.exceptions import ParseError

# Parsing should fail for an empty file.
def test_empty():
    # Todo: Are we happy with it raising a ValueError? Should it be rather ParseError or something else?
    # Maybe a "production" mode would be nice to have, so that it simply returns a status of the parse without
    # raising an exception.
    with pytest.raises(ValueError):
        sc2reader.read("test_replays/corrupted/empty.SC2Replay")

# Tests for build 17811 replays

def test_standard_1v1():
    replay = sc2reader.read("test_replays/build17811/1.SC2Replay")
    
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
    assert emperor.team == 1
    assert emperor.choosen_race == "Protoss"
    assert emperor.actual_race == "Protoss"
    assert emperor.recorder == False

    boom = replay.person['Boom']
    assert boom.team == 2
    assert boom.choosen_race == "Terran"
    assert boom.actual_race == "Terran"
    assert boom.recorder == True

    for player in replay.players:
        assert player.type == "Human"
        
    # Because it is a 1v1 and the recording player quit, we should know the winner.
    assert emperor.result == "Won"
    assert boom.result == "Lost"

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
    replay = sc2reader.read("test_replays/build17811/2.SC2Replay")
    assert replay.is_private == True
    assert replay.is_ladder == False

def test_2v2():
    replay = sc2reader.read("test_replays/build17811/7.SC2Replay")
    assert replay.type == "2v2"

def test_3v3():
    replay = sc2reader.read("test_replays/build17811/3.SC2Replay")
    assert replay.type == "3v3"
    
    # Because it's a 3v3 and all of the members of Team 2 quit, we should know the winner.
    assert replay.results[1] == "Won"
    assert replay.results[2] == "Lost"

def test_4v4():
    replay = sc2reader.read("test_replays/build17811/9.SC2Replay")
    assert replay.type == "4v4"

def test_ffa():
    replay = sc2reader.read("test_replays/build17811/8.SC2Replay")
    assert replay.type == "FFA"
    
    # Player 'Boom' won because the last building of the last player was destroyed,
    # but the winner cannot be parsed because "Player has left" event isn't generated.
    # Unknown result is the best we can do.
    assert replay.winner_known == False

def test_unknown_winner():
    replay = sc2reader.read("test_replays/build17811/10.SC2Replay")
    
    # Recording player (Boom) left second in a 4v4, so the winner shouldn't be known
    assert replay.winner_known == False

def test_random_player():
    replay = sc2reader.read("test_replays/build17811/3.SC2Replay")

    gogeta = replay.person['Gogeta']
    assert gogeta.choosen_race == "Random"
    assert gogeta.actual_race == "Terran"

def test_random_player2():
    replay = sc2reader.read("test_replays/build17811/6.SC2Replay")
    permafrost = replay.person["Permafrost"]
    assert permafrost.choosen_race == "Random"
    assert permafrost.actual_race == "Protoss"
    
def test_us_realm():
    replay = sc2reader.read("test_replays/build17811/5.SC2Replay")
    assert replay.person['ShadesofGray'].url == "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/"
    assert replay.person['reddawn'].url == "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/"

# TODO: Current problem.. both players are set as the recording players
# Waiting for response https://github.com/arkx/mpyq/issues/closed#issue/7
def test_kr_realm_and_tampered_messages():
    replay = sc2reader.read("test_replays/build17811/11.SC2Replay")
    assert replay.person['명지대학교'].url == "http://kr.battle.net/sc2/en/profile/258945/1/명지대학교/"
    assert replay.person['티에스엘사기수'].url == "http://kr.battle.net/sc2/en/profile/102472/1/티에스엘사기수/"
    
    assert replay.messages[0].text == "sc2.replays.net"
    assert replay.messages[5].text == "sc2.replays.net"
    
    print replay.players[1].choosen_race
    print replay.players[1].actual_race    
    
    print replay.players[0].choosen_race
    print replay.players[0].actual_race    

    print replay.map

# TODO: Failing with
# TypeError: Unknown event: 0x4 - 0xe3 at 16
def test_referee():
    replay = sc2reader.read("test_replays/build17811/14.SC2Replay")


# TODO: This currently fails for unknown reasons
# It errors: "TypeError: Unknown event: 0x0 - 0x0 at 0x356F"
# Disabled for now, no plans on fixing
"""
def test_footmen():
    replay = sc2reader.read("test_replays/build17811/footman.SC2Replay")
"""

def test_encrypted():
    replay = sc2reader.read("test_replays/build17811/4.SC2Replay")
    
def test_observers():
    replay = sc2reader.read("test_replays/build17811/13.SC2Replay")

def test_datetimes():
    # Ignore seconds in comparisons, because they are off by one what is reported by Windows.
    # This might be a little nuance worth investigating at some point.
    
    # Played at 20 Feb 2011 22:44:48 UTC+2
    replay = sc2reader.read("test_replays/build17811/1.SC2Replay")
    assert replay.utc_date == datetime.datetime(2011, 2, 20, 20, 44, 47)
    
    # Played at 21 Feb 2011 00:42:13 UTC+2
    replay = sc2reader.read("test_replays/build17811/2.SC2Replay")
    assert replay.utc_date == datetime.datetime(2011, 2, 20, 22, 42, 12)
    
    # Played at 25 Feb 2011 16:36:28 UTC+2
    replay = sc2reader.read("test_replays/build17811/3.SC2Replay")
    assert replay.utc_date == datetime.datetime(2011, 2, 25, 14, 36, 26)

""" 
def test_15():
    replay = sc2reader.read("test_replays/build17811/15.SC2Replay")
    
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    assert 1==0

def test_16():
    replay = sc2reader.read("test_replays/build17811/16.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    assert 1==0
    
def test_17():
    replay = sc2reader.read("test_replays/build17811/17.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0

def test_18():
    replay = sc2reader.read("test_replays/build17811/18.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
    
def test_19():
    replay = sc2reader.read("test_replays/build17811/19.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
    
def test_20():
    replay = sc2reader.read("test_replays/build17811/20.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
    
def test_21():
    replay = sc2reader.read("test_replays/build17811/21.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
    
def test_22():
    replay = sc2reader.read("test_replays/build17811/22.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
    
# TODO: No winner?
def test_two_player_game_without_winner():
    replay = sc2reader.read("test_replays/build17811/23.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    print len(replay.people)
    print replay.players[0].result
    print replay.players[1].result
    print replay.actors[2].result
    print replay.actors[3].result
    assert replay.players[0].result == 'Win' or replay.players[1].result == 'Win'


def test_24():
    replay = sc2reader.read("test_replays/build17811/24.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
    
def test_25():
    replay = sc2reader.read("test_replays/build17811/25.SC2Replay")
    print replay.realm
    print len(replay.players)
    print replay.players[0].actual_race
    print replay.players[1].actual_race
    print replay.players[0].choosen_race
    print replay.players[1].choosen_race
    print replay.players[0].name
    print replay.players[1].name
    assert 1==0
"""
