# Note: Chose pytest over unittest(2) because of cleaner and more lightweight syntax.
# Run tests with "py.test"

# TODO:
#   - Performance tests to measure the effect of optimizations
import os
import pytest

from sc2reader import Replay
from sc2reader.exceptions import ParseError

# Helper functions
def sent_to_all(msg):
    return msg.target == 0
    
def find(f, seq):
    for item in seq:
        if item is None:
            continue
        if f(item): 
            return item


# Parsing should fail for an empty file.
def test_empty():
    # Todo: Are we happy with it raising a ValueError? Should it be rather ParseError or something else?
    # Maybe a "production" mode would be nice to have, so that it simply returns a status of the parse without
    # raising an exception.
    with pytest.raises(ValueError):
        Replay("test_replays/corrupted/empty.sc2replay")

# Tests for build 17811 replays

# TODO: Realm/region functionality is missing!
def test_1():
    replay = Replay("test_replays/build17811/1.sc2replay")

#    assert replay.date == "20 Feb 2011 22:44:48"
    assert replay.length == (32, 47)
    assert replay.map == "Lost Temple"
    assert replay.build == 17811
    assert replay.releaseString == "1.2.2.17811"
    assert replay.speed == "Faster"
    assert replay.type == "1v1"
    assert replay.category == "Ladder"

#    assert len(replay.players) == 2
    emperor = find(lambda player: player.name == "Emperor", replay.players)
    assert emperor.team == 1
    assert emperor.race == "Protoss"
    assert emperor.recorder == False

    boom = find(lambda player: player.name == "Boom", replay.players)
    assert boom.team == 2
    assert boom.race == "Terran"
    assert boom.recorder == True

    # for player in replay.players:
    #     assert player.type == "Human"
        
    # Because it is a 1v1 and the recording player quit, we should know the winner.
    assert emperor.result == "Won"
    assert boom.result == "Lost"

    # assert emperor.url == "http://eu.battle.net/sc2/en/profile/520049/1/Emperor/"
    # assert boom.url == "http://eu.battle.net/sc2/en/profile/1694745/1/Boom/"

    assert len(replay.messages) == 12
    assert find(lambda player: player.pid == replay.messages[0].player, replay.players).name == "Emperor"
    assert replay.messages[0].text == "hf"
    assert replay.messages[1].text == "HEYA"
    assert replay.messages[2].text == "gl hf"
    assert replay.messages[3].text == "sry for caps"
    assert replay.messages[4].text == "^^"
    assert replay.messages[5].text == "noppe"
    assert replay.messages[6].text == "you greedy bastard"
    assert replay.messages[7].text == "ggg"
    assert replay.messages[8].text == "WG"
    assert replay.messages[9].text == "wg? :)"
    assert replay.messages[10].text == "wipe"
    assert replay.messages[11].text == "huh?"
    assert find(lambda player: player.pid == replay.messages[11].player, replay.players).name == "Boom"
    
    for msg in replay.messages:
        assert sent_to_all(msg) == True