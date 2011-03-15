import os

from mpyq import MPQArchive
from config import DefaultConfig
from utils import read_header

def read(location,config=DefaultConfig()):
    if not os.path.exists(location):
        raise ValueError("Location must exist")
    
    if os.path.isdir(location):
        replays = list()
        for location in os.list_files(location):
            replays.extend(read(location,config))
        return replays
    else:
        return read_file(location,config)
    
def read_file(filename,config=DefaultConfig()):
    if(os.path.splitext(filename)[1].lower() != '.sc2replay'):
        raise TypeError("Target file must of the SC2Replay file extension")
    
    with open(filename) as replay_file:
        release,frames = read_header(replay_file)
        replay = config.ReplayClass(filename,release,frames)
        archive = MPQArchive(filename,listfile=False)
        
        #Extract and Parse the relevant files
        for file,readers in config.readers.iteritems():
            for reader in readers:
                if reader.reads(replay.build):
                    reader.read(archive.read_file(file),replay)
                    break
            else:
                raise NotYetImplementedError("No parser was found that accepted the replay file;check configuration")

        #Do cleanup and post processing
        for process in config.processors:
            replay = process(replay)
            
        return replay
        
__all__ = [DefaultConfig,read,read_file]
__version__ = "0.1.0"