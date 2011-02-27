# Run tests with "py.test" in the project root dir

# TODO:
#   - Performance tests to measure the effect of optimizations
import os, sys
from timeit import Timer
import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../"))
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

def test_1():
    replay = Replay("test_replays/build17811/1.sc2replay")

#    assert replay.date == "20 Feb 2011 22:44:48"
    assert replay.length == (32, 47)
    assert replay.map == "Lost Temple"
    assert replay.build == 17811
    assert replay.release_string == "1.2.2.17811"
    assert replay.speed == "Faster"
    assert replay.type == "1v1"
    assert replay.category == "Ladder"

    assert len(replay.players) == 2
    assert replay.player[1].name == "Emperor"
    assert replay.player[2].name == "Boom"
    emperor = find(lambda player: player.name == "Emperor", replay.players)
    assert emperor.team == 1
    assert emperor.choosen_race == "Protoss"
    assert emperor.actual_race == "Protoss"
    assert emperor.recorder == False

    boom = find(lambda player: player.name == "Boom", replay.players)
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

# Uncathegorized tests

def proxy():
    file_list = []
    rootdir = "test_replays/"
    for root, sub_folders, files in os.walk(rootdir):
        for file in files:
            if (os.path.splitext(file)[1].lower() == ".sc2replay"):
                file_list.append(os.path.join(root,file))

    for file in file_list:
        try:
            replay = Replay(file)
        except ValueError as e:
            print e
        except ParseError as e:
            print e

# Is there a way to print things out when a test passes? pytest seems to ignore
# Stdout when tests are passing.

# Do we need to use a proxy function to use timeit? Also, timeit doesn't seem to
# find proxy() for some reason.

# timeit over other python time functions, because it should provide more consistent results
# across different platforms.
# http://docs.python.org/library/timeit.html
def test_performace():

    t = Timer("proxy()")
    print t.timeit()
    
    assert 1 == 0