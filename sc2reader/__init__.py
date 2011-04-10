import os

from mpyq import MPQArchive
from config import DefaultConfig
from utils import ReplayBuffer, LITTLE_ENDIAN

def read_header(file):
    buffer = ReplayBuffer(file)
    
    #Check the file type for the MPQ header bytes
    if buffer.read_hex(4).upper() != "4D50511B":
        print "Header Hex was: %s" % buffer.read_hex(4).upper()
        raise ValueError("File '%s' is not an MPQ file" % file.name)
    
    #Extract replay header data, we don't actually use this for anything
    max_data_size = buffer.read_int(LITTLE_ENDIAN) #possibly data max size
    header_offset = buffer.read_int(LITTLE_ENDIAN) #Offset of the second header
    data_size = buffer.read_int(LITTLE_ENDIAN)     #possibly data size
    
    #Extract replay attributes from the mpq
    data = buffer.read_data_struct()
    
    #return the release and frames information
    return data[1],data[3]
    
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
                    reader.read(ReplayBuffer(archive.read_file(file)),replay)
                    break
            else:
                raise NotYetImplementedError("No parser was found that accepted the replay file;check configuration")

        #Do cleanup and post processing
        for processor in config.processors:
            replay = processor.process(replay)
            
        return replay
        
__all__ = [DefaultConfig,read,read_file]
__version__ = "0.1.0"
