import os

from mpyq import MPQArchive
from utils import ReplayBuffer, LITTLE_ENDIAN
from objects import Replay
from processors import *
from readers import *

__version__ = "0.3.0"

FILES = {
    "FULL": [
            'replay.initData',
            'replay.details',
            'replay.attributes.events',
            'replay.message.events',
            'replay.game.events'
        ],
        
    "PARTIAL": [
            'replay.initData',
            'replay.details',
            'replay.attributes.events',
            'replay.message.events'
        ],
}

PROCESSORS = {
    "FULL": [
            PeopleProcessor(),
            AttributeProcessor(),
            TeamsProcessor(),
            MessageProcessor(),
            RecorderProcessor(),
            EventProcessor(),
            ApmProcessor(),
            ResultsProcessor()
        ],
        
    "PARTIAL": [
            PeopleProcessor(),
            AttributeProcessor(),
            TeamsProcessor(),
            MessageProcessor(),
            RecorderProcessor(),
        ],
}

class ReaderMap(object):
    def __getitem__(self,key):
        if int(key) in (16117,16195,16223,16291):
            return {
                'replay.initData': ReplayInitDataReader(),
                'replay.details': ReplayDetailsReader(),
                'replay.attributes.events': AttributeEventsReader(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader_16291(),
            }

        elif int(key) in (16561,16605,16755,16939):
            return {
                'replay.initData': ReplayInitDataReader(),
                'replay.details': ReplayDetailsReader(),
                'replay.attributes.events': AttributeEventsReader(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader(),
            }

        elif int(key) in (17326,17682,17811,18092,18221,18317):
            return {
                'replay.initData': ReplayInitDataReader(),
                'replay.details': ReplayDetailsReader(),
                'replay.attributes.events': AttributeEventsReader_17326(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader(),
            }

        elif int(key) in (18574,):
            return {
                'replay.initData': ReplayInitDataReader(),
                'replay.details': ReplayDetailsReader(),
                'replay.attributes.events': AttributeEventsReader_17326(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader_18574(),
            }
        else:
            raise KeyError(key)

READERS = ReaderMap()
    
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
    def __init__(self, parse="FULL", directory="", processors=[], debug=False, files=None):
        #Sanitize the parse level
        parse = parse.upper()
        if parse not in ("FULL","PARTIAL","CUSTOM"):
            raise ValueError("Unrecognized parse argument `%s`" % parse)
        
        #get our defaults and save preferences
        files = FILES.get(parse,files)
        processors = PROCESSORS.get(parse,processors)
        self.__dict__.update(locals())
    
    def read(self, location):
        #Sanitize the location provided (accounting for directory option)
        if self.directory:
            location = os.path.join(self.directory,location)
        if not os.path.exists(location):
            raise ValueError("Location must exist")
        
        #If its a directory, read each subfile/directory and combine the lists
        if os.path.isdir(location):
            read = lambda file: self.read(os.path.join(location,file))
            tolist = lambda x: [x] if isinstance(x,Replay) else x
            return sum(map(tolist,(read(x) for x in os.listdir(location))),[])
            
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
                for file in self.files:
                    reader = READERS[replay.build][file]
                    reader.read(ReplayBuffer(archive.read_file(file)),replay)
                
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
