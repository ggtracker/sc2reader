import os, copy

import mpyq

import config
from objects import Replay
from utils import ReplayBuffer, AttributeDict

__version__ = "0.3.0"
__author__ = "Graylin Kim <graylin.kim@gmail.com>"


class SC2Reader(object):
    def __init__(self, **options):
        #Set Defaults before configuring with user options
        self.options = AttributeDict(
            directory="",
            processors=[],
            debug=False,
            verbose=False,
            parse_events=True)
        self.configure(**options)

    def read(self, location):
        if self.options.directory:
            location = os.path.join(self.options.directory,location)

        if self.options.verbose: print "Reading: %s" % location

        if os.path.isdir(location):
            #SC2Reader::read each subfile/directory and combine the lists
            read = lambda file: self.read(os.path.join(location,file))
            tolist = lambda x: [x] if isinstance(x,Replay) else x
            return sum(map(tolist,(read(x) for x in os.listdir(location))),[])

        with open(location) as replay_file:
            replay = Replay(replay_file,**self.options.copy())
            archive = mpyq.MPQArchive(location,listfile=False)

            for file in self.files:
                buffer = ReplayBuffer(archive.read_file(file))
                read = config.readers[replay.build][file]
                read(buffer,replay)

            #Handle user processors after internal processors
            for process in self.processors+self.options.processors:
                replay = process(replay)

            return replay

    def configure(self,**options):
        self.options.update(options)

        #Update system configuration
        myconfig = config.full if self.options.parse_events else config.partial
        self.files = myconfig.files
        self.processors = myconfig.processors


'''Package Level Interface'''
__defaultSC2Reader = SC2Reader()

#Allow options on the package level read for one off reads.
def read(location, **options):
    reader = SC2Reader(**options) if options else __defaultSC2Reader
    return reader.read(location)

#Allow package level configuration for lazy people
def configure(**options):
    __defaultSC2Reader.configure(**options)
