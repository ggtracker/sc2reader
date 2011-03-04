import os,sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sc2reader import Replay
from mpyq import MPQArchive
from datetime import datetime
from time import gmtime

# replay = Replay("1.sc2replay")
# 
# print replay.player["Nexpacisor"].avg_apm
# print replay.player["dblrainbow"].apm

replay = Replay("f.sc2replay", True, False)
print replay.date
print datetime.utcfromtimestamp((replay.file_time-116444735995904000)/10000000)
print datetime.fromtimestamp((replay.file_time-116444735995904000)/10000000)