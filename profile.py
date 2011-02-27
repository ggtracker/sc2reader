import cProfile
from pstats import Stats

import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay


cProfile.run("Replay('test_replays/build17811/1.sc2replay')","replay_profile")
stats = Stats("replay_profile")
stats.strip_dirs().sort_stats("time").print_stats(15)