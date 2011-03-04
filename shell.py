import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay
from mpyq import MPQArchive
from datetime import datetime
from time import gmtime

# replay = Replay("test_replays/build17811/1.sc2replay")
# print replay.type
# print replay.players[0].rgba
# print "%02X%02X%02X" % (replay.players[0].rgba['r'], replay.players[0].rgba['g'], replay.players[0].rgba['b'])