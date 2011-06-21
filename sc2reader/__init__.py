import os

import copy

from config import FULL, PARTIAL, CUSTOM, FILES, PROCESSORS, READERS
from mpyq import MPQArchive
from objects import Replay
from utils import ReplayBuffer

__version__ = "0.3.0"
__author__ = "Graylin Kim <graylin.kim@gmail.com>"

class SC2Reader(object):
    ''' Class level interface to sc2reader.
        
        <<usage documentation here>>
    '''

    def __init__(self, parse_type="FULL", directory="", processors=[], debug=False, files=[], verbose=False, copy=copy.copy):
        try:
            #Update and save the reader configuration
            parse_type = parse_type.upper()
            files = FILES.get(parse_type, files)
            processors = PROCESSORS.get(parse_type, processors)
            self.__dict__.update(locals())
        except KeyError:
            raise ValueError("Unrecognized parse_type `%s`" % parse_type)

    def read(self, location):
        if self.directory:
            location = os.path.join(self.directory,location)

        if self.verbose: print "Reading: %s" % location

        if os.path.isdir(location):
            #SC2Reader::read each subfile/directory and combine the lists
            read = lambda file: self.read(os.path.join(location,file))
            tolist = lambda x: [x] if isinstance(x,Replay) else x
            return sum(map(tolist,(read(x) for x in os.listdir(location))),[])

        else:
            with open(location) as replay_file:
                replay = Replay(self.copy(self),replay_file)
                archive = MPQArchive(location,listfile=False)

                for file in self.files:
                    buffer = ReplayBuffer(archive.read_file(file))
                    READERS[replay.build][file].read(buffer,replay)

                for process in self.processors:
                    replay = process(replay)

                return replay

    def configure(self,**options):
        self.__dict__.update(options)


''' The package level interface is just a lightweight wrapper around a default
    SC2Reader class. See the documentation above for usage details '''

__defaultSC2Reader = SC2Reader()

def configure(**options):
    __defaultSC2Reader.configure(**options)

def read(location, **options):
    if options:
        return SC2Reader(**options).read(location)
    else:
        return __defaultSC2Reader.read(location)
