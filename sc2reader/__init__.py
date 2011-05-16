import os

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
except ImportError:
    from sys import exit
    exit("OrderedDict required: Upgrade to python2.7 or `pip install ordereddict`")
    
from mpyq import MPQArchive
from utils import ReplayBuffer, LITTLE_ENDIAN
from objects import Replay
from processors import *
from readers import *

__version__ = "0.3.0"

#Library configuration and constants
FULL = 1
PARTIAL = 2
CUSTOM = 3

FILES_FULL = ['replay.initData','replay.details','replay.attributes.events','replay.message.events','replay.game.events']
FILES_PARTIAL = ['replay.initData','replay.details','replay.attributes.events','replay.message.events']

PROCESSORS_FULL = [
            PeopleProcessor(),
            AttributeProcessor(),
            TeamsProcessor(),
            MessageProcessor(),
            RecorderProcessor(),
            EventProcessor(),
            ApmProcessor(),
            ResultsProcessor()
        ]
        
PROCESSORS_PARTIAL = [
            PeopleProcessor(),
            AttributeProcessor(),
            TeamsProcessor(),
            MessageProcessor(),
            RecorderProcessor(),
        ]
READERS = OrderedDict([
        ('replay.initData', [ReplayInitDataReader()]),
        ('replay.details', [ReplayDetailsReader()]),
        ('replay.attributes.events', [AttributeEventsReader_17326(), AttributeEventsReader()]),
        ('replay.message.events', [MessageEventsReader()]),
        ('replay.game.events', [GameEventsReader()]),
    ])
    
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
    def __init__(self, parse=FULL, directory="", processors=[], debug=False, files=None):
        #Check that arguments are consistent with expectations up front
        #Easier to debug issues this way
        if parse == FULL: 
            files = FILES_FULL
            processors = PROCESSORS_FULL + processors
        elif parse == PARTIAL:
            files = FILES_PARTIAL
            processors = PROCESSORS_PARTIAL + processors
        elif parse == CUSTOM:
            if not files:
                raise ValueError("Custom parsing requires specification the files arguments")
        else:
            raise ValueError("parse must be either FULL, PARTIAL, or CUSTOM")
        
        #Update the class configuration
        self.__dict__.update(locals())
    
    def read(self, location):
        #account for the directory option
        if self.directory: location = os.path.join(self.directory,location)
        
        if not os.path.exists(location):
            raise ValueError("Location must exist")
        
        #If its a directory, read each subfile/directory and combine the lists
        if os.path.isdir(location):
            replays = list()
            for filename in os.listdir(location):
                replay = self.read(os.path.join(location,filename))
                if isinstance(replay,list):
                    replays.extend(replay)
                else:
                    replays.append(replay)
            return replays
            
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
                for file,readers in READERS.iteritems():
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
                
    def configure(self,**options):
        self.__dict__.update(options)
        
        
#Prepare the lightweight interface
__defaultSC2Reader = SC2Reader()

def configure(**options):
    __defaultSC2Reader.configure(options)

def read(location):
    return __defaultSC2Reader.read(location)
