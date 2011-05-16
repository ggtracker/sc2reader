import os

from mpyq import MPQArchive
import config
from objects import Replay
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

class SC2Reader(object):

    def __init__(self, parse=config.FULL, directory="", processors=[], debug=False, files=None):
        #Check that arguments are consistent with expectations up front
        #Easier to debug issues this way
        if parse == config.FULL: 
            files = config.FILES_FULL
            processors = config.PROCESSORS_FULL + processors
        elif parse == config.PARTIAL:
            files = config.FILES_PARTIAL
            processors = config.PROCESSORS_PARTIAL + processors
        elif parse == config.CUSTOM:
            if not files:
                raise ValueError("Custom parsing requires specification the files arguments")
        else:
            raise ValueError("parse must be either FULL, PARTIAL, or CUSTOM")
        
        #Update the class configuration
        self.__dict__.update(locals())
    
    def read(self, location):
        #account for the directory option
        location = os.path.join(self.directory,location)
        
        if not os.path.exists(location):
            raise ValueError("Location must exist")
        
        #If its a directory, read each subfile/directory and combine the lists
        if os.path.isdir(location):
            return sum(map(self.read, os.list_files(location)),[])
            
        #The primary replay reading routine
        else:
            if(os.path.splitext(location)[1].lower() != '.sc2replay'):
                raise TypeError("Target file must of the SC2Replay file extension")
        
            with open(location) as replay_file:
                #Use the MPQ Header information to initialize the replay
                release,frames = read_header(replay_file)
                replay = Replay(location,release,frames)
                archive = MPQArchive(location,listfile=False)
                
                #Extract and Parse the relevant files based on parse level
                for file,readers in config.READERS.iteritems():
                    if file in self.files:
                        for reader in readers:
                            if reader.reads(replay.build):
                                reader.read(ReplayBuffer(archive.read_file(file)),replay)
                                break
                        else:
                            raise NotYetImplementedError("No parser was found that accepted the replay file;check configuration")
                
                #Do cleanup and post processing
                for processor in self.processors:
                    replay = processor.process(replay)
                
                return replay
                
#Prepare the lightweight interface
__defaultSC2Reader = SC2Reader()

def configure(parse=config.FULL, directory=None, processors=[], debug=False, files=None):
    __defaultSC2Reader.__dict__.update(locals())

def read(location):
    return __defaultSC2Reader.read(location)
        
__all__ = [read,config,SC2Reader]
__version__ = "0.3.0"
