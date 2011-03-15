from mpyq import MPQArchive
from utils import ByteStream
from objects import Replay
from readers import *
from processors import *
from collections import OrderedDict

__version__ = "0.1.0"

import os

class DefaultConfig(object):
    def __init__(self):
        self.readers = OrderedDict()
        self.readers['replay.initData'] = [ ReplayInitDataReader() ]
        self.readers['replay.details'] = [ ReplayDetailsReader() ]
        self.readers['replay.attributes.events'] = [ AttributeEventsReader_17326(), AttributeEventsReader() ]
        self.readers['replay.message.events'] = [ MessageEventsReader() ]
        self.readers['replay.game.events'] = [ GameEventsReader_17326(), GameEventsReader_16561(), GameEventsReader() ]
        
        self.processors = [
                PeopleProcessor,
                AttributeProcessor,
                TeamsProcessor,
                MessageProcessor,
                RecorderProcessor,
                EventProcessor,
                ApmProcessor,
                ResultsProcessor
            ]

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
        replay = Replay(filename,release,frames)
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
    
def read_header(file):
    source = ByteStream(file.read())
    
    #Check the file type for the MPQ header bytes
    if source.get_hex(4).upper() != "4D50511B":
        raise ValueError("File '%s' is not an MPQ file" % file.name)
    
    #Extract replay header data, we don't actually use this for anything
    max_data_size = source.get_little_32() #possibly data max size
    header_offset = source.get_little_32() #Offset of the second header
    data_size = source.get_little_32()     #possibly data size
    
    #Extract replay attributes from the mpq
    data = source.parse_serialized_data()
    
    #return the release and frames information
    return data[1],data[3]
        
__all__ = [DefaultConfig,read,read_file]