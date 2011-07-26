import cProfile, pstats, time

import sc2reader

def parse_replays():
    # Run four times to dampen noise
    for run in range(1,4):
        sc2reader.read("test_replays/1.3.0.18092",verbose=True)

# Use the results of this function when comparing performance with other libraries.
def benchmark_with_timetime():
    start = time.time()
    parse_replays()
    diff = time.time() - start
    print diff

def profile():
    cProfile.run("parse_replays()","replay_profile2")
    stats = pStats.Stats("replay_profile")
    stats.strip_dirs().sort_stats("time").print_stats(30)


if __name__ == '__main__':
    #benchmark_with_timetime()
    profile()
