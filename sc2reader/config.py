try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from sc2reader.objects import Replay
from sc2reader.processors import *
from sc2reader.readers import *

class DefaultConfig(object):
    def __init__(self):
        self.ReplayClass = Replay
        
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

class NoEventsConfig(object):
    def __init__(self):
        self.ReplayClass = Replay
        self.readers = OrderedDict()
        self.readers['replay.initData'] = [ ReplayInitDataReader() ]
        self.readers['replay.details'] = [ ReplayDetailsReader() ]
        self.readers['replay.attributes.events'] = [ AttributeEventsReader_17326(), AttributeEventsReader() ]
        self.readers['replay.message.events'] = [ MessageEventsReader() ]

        self.processors = [
            PeopleProcessor,
            AttributeProcessor,
            TeamsProcessor,
            MessageProcessor,
            RecorderProcessor,
        ]
