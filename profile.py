import cProfile
from pstats import Stats
import time

import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay

def parse_replays():
    for run in range(1,4):
        file_list = []
        rootdir = "test_replays/build17811/"
        for root, sub_folders, files in os.walk(rootdir):
            for file in files:
                basename, extension = os.path.splitext(file)
                if (basename != "empty" and extension.lower() == ".sc2replay"):
                    file_list.append(os.path.join(root,file))

        for file in file_list:
            print file
            replay = Replay(file)

# Problem with the profiler is that it adds conciderable amount of overhead
cProfile.run("parse_replays()","replay_profile")
stats = Stats("replay_profile")
stats.strip_dirs().sort_stats("time").print_stats(30)

# start = time.time()
# for run in range(1,4):
#     parse_replays()
# diff = time.time() - start
# print diff

# ========================================
# Results for March 1 2011
# With cProfile

# Tue Mar  1 06:25:22 2011    replay_profile
# 
#          20568477 function calls (20565106 primitive calls) in 37.650 seconds
# 
#    Ordered by: internal time
#    List reduced from 184 to 15 due to restriction <15>
# 
#    ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#   3484431    7.903    0.000    8.559    0.000 utils.py:42(get_big)
#   3057363    5.960    0.000   13.308    0.000 utils.py:89(get_big_int)
#        33    4.828    0.146   35.395    1.073 parsers.py:225(load)
#    472272    2.948    0.000    3.360    0.000 objects.py:98(__init__)
#     42861    2.227    0.000    6.391    0.000 eventparsers.py:154(load)
#    472272    2.222    0.000    3.223    0.000 parsers.py:254(get_parser)
#    114174    1.225    0.000    4.265    0.000 eventparsers.py:50(load)
#    294732    1.224    0.000    3.983    0.000 eventparsers.py:394(load)
#    473916    1.060    0.000    3.568    0.000 utils.py:108(get_timestamp)
#   1142493    0.926    0.000    0.926    0.000 utils.py:66(peek)
#   3965823    0.745    0.000    0.745    0.000 {len}
#      7095    0.705    0.000    0.705    0.000 {method 'upper' of 'str' objects}
#    695461    0.644    0.000    0.644    0.000 {range}
#         1    0.575    0.575   37.571   37.571 profile.py:9(parse_replays)
#    566628    0.491    0.000    0.491    0.000 {method 'rjust' of 'str' objects}


# With time.time()
# 28.2304489613
# ========================================