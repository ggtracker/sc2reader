import cProfile
from pstats import Stats

import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay


cProfile.run("Replay('test_replays/build17811/1.sc2replay')","replay_profile")
stats = Stats("replay_profile")
stats.strip_dirs().sort_stats("time").print_stats(15)

# file_list = []
# rootdir = "test_replays/"
# for root, sub_folders, files in os.walk(rootdir):
#     for file in files:
#         if (os.path.splitext(file)[1].lower() == ".sc2replay"):
#             file_list.append(os.path.join(root,file))
# 
# for file in file_list:
#     try:
#         replay = Replay(file)
#     except ValueError as e:
#         print e
#     except ParseError as e:
#         print e