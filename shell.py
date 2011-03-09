import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay
from mpyq import MPQArchive
from datetime import datetime
from time import gmtime
from events import EventParser
from utils import MemFile
import cProfile
from pstats import Stats
import time

def test_bp():
    archive = MPQArchive("long.sc2replay", listfile=False)
    events = EventParser(MemFile(archive.read_file('replay.game.events')), 17811)

    for event in list(events):
        print event

def test_sc2():
    replay = Replay("long.sc2replay", False, True)
    print len(replay.events)

test_bp()

#cProfile.run("test_bp()", "replay_profile")
#cProfile.run("test_sc2()", "replay_profile")

#stats = Stats("replay_profile")
#stats.strip_dirs().sort_stats("time").print_stats(30)