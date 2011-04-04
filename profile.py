import cProfile
from pstats import Stats
import time

import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sc2reader

skipnames = ('empty','footman')

def parse_replays():
    # Run four times to dampen noise
    for run in range(1,4):
        file_list = []
        rootdir = "test_replays/build17811/"
        for root, sub_folders, files in os.walk(rootdir):
            for file in files:
                basename, extension = os.path.splitext(file)
                if (basename not in skipnames and extension.lower() == ".sc2replay"):
                    file_list.append(os.path.join(root,file))

        for file in file_list:
            print file
            replay = sc2reader.read(file)

# Use the results of this function when comparing performance with other libraries.
def benchmark_with_timetime():
    start = time.time()
    parse_replays()
    diff = time.time() - start
    print diff

def profile():
    cProfile.run("parse_replays()","replay_profile")
    stats = Stats("replay_profile")
    stats.strip_dirs().sort_stats("time").print_stats(30)  


#benchmark_with_timetime()
profile()
