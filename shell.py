import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay
from mpyq import MPQArchive

# replay = Replay("1.sc2replay")
# 
# print replay.player["Nexpacisor"].avg_apm
# print replay.player["dblrainbow"].apm