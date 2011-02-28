# Run tests with "py.test" in the project root dir
import os, sys
import pytest

#sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../")))
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../")))

from sc2reader import Replay
from sc2reader.exceptions import ParseError

# Parsing should fail for an empty file.
def test_empty():
    # Todo: Are we happy with it raising a ValueError? Should it be rather ParseError or something else?
    # Maybe a "production" mode would be nice to have, so that it simply returns a status of the parse without
    # raising an exception.
    with pytest.raises(ValueError):
        Replay("test_replays/corrupted/empty.sc2replay")

# Tests for build 17811 replays

def test_1():
    replay = Replay("test_replays/build17811/1.sc2replay")

#    assert replay.date == "20 Feb 2011 22:44:48"
    assert replay.length == (32, 47)
    assert replay.map == "Lost Temple"
    assert replay.build == 17811
    assert replay.release_string == "1.2.2.17811"
    assert replay.speed == "Faster"
    assert replay.type == "1v1"

    assert replay.is_ladder == True
    assert replay.is_private == False

    assert len(replay.players) == 2
    assert replay.player[1].name == "Emperor"
    assert replay.player[2].name == "Boom"
    emperor = replay.player['Emperor']
    assert emperor.team == 1
    assert emperor.choosen_race == "Protoss"
    assert emperor.actual_race == "Protoss"
    assert emperor.recorder == False

    boom = replay.player['Boom']
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
        assert msg.sent_to_all == True
        
def test_private_category():
    replay = Replay("test_replays/build17811/2.sc2replay")
    
    assert replay.is_private == True
    assert replay.is_ladder == False
    
def test_3v3():
    replay = Replay("test_replays/build17811/3.sc2replay")
    
    assert replay.type == "3v3"
    
    # Because it's a 3v3 and all of the members of Team 2 quit, we should know the winner.
    assert replay.results[1] == "Won"
    assert replay.results[2] == "Lost"


def test_random_player():
    replay = Replay("test_replays/build17811/3.sc2replay")

    gogeta = replay.player['Gogeta']
    assert gogeta.choosen_race == "Random"
    assert gogeta.actual_race == "Terran"
    
def test_us_realm():
    replay = Replay("test_replays/build17811/5.sc2replay")
    
    assert replay.player['ShadesofGray'].url == "http://us.battle.net/sc2/en/profile/2358439/1/ShadesofGray/"
    assert replay.player['reddawn'].url == "http://us.battle.net/sc2/en/profile/2198663/1/reddawn/"

    
def test_encrypted():
    replay = Replay("test_replays/build17811/4.sc2replay")
    
#TODO: Test 2v2, 4v4 and FFA