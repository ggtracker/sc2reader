try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
except ImportError:
    from sys import exit
    exit("OrderedDict required: Upgrade to python2.7 or `pip install ordereddict`")

from sc2reader.objects import Replay
from sc2reader.processors import *
from sc2reader.readers import *
from sc2reader.utils import key_in_bases

#####################################################
# Metaclass used to help enforce the usage contract
#####################################################
class MetaConfig(type):
    def __new__(meta, class_name, bases, class_dict):
        if class_name != 'Config': #Parent class is exempt from checks
            assert 'ReplayClass' in class_dict or key_in_bases('ReplayClass',bases), \
                "%s must specify 'ReplayClass' to be the class acting as a replay container" % class_name

            assert 'readers' in class_dict or key_in_bases('readers',bases), \
                "%s must specify 'dict<string,list<Reader>> readers'" % class_name

            assert 'processors' in class_dict or key_in_bases('processors',bases), \
                "%s must specify 'list<Processor> processors'" % class_name

        return type.__new__(meta, class_name, bases, class_dict)

class Config(object):
    __metaclass__ = MetaConfig

#####################################################

class DefaultConfig(Config):
    ReplayClass = Replay

    ''' The dict([ (key1,value1),(key2,value2).... ]) method has been applied
        here in order to keep the reading order intact
    '''
    readers = OrderedDict([
            ('replay.initData', [ReplayInitDataReader()]),
            ('replay.details', [ReplayDetailsReader()]),
            ('replay.attributes.events', [AttributeEventsReader_17326(), AttributeEventsReader()]),
            ('replay.message.events', [MessageEventsReader()]),
            ('replay.game.events', [GameEventsReader()]),
        ])

    processors = [
            PeopleProcessor(),
            AttributeProcessor(),
            TeamsProcessor(),
            MessageProcessor(),
            RecorderProcessor(),
            EventProcessor(),
            ApmProcessor(),
            ResultsProcessor()
        ]

#####################################################

class NoEventsConfig(DefaultConfig):

    readers = OrderedDict([
            ('replay.initData', [ReplayInitDataReader()]),
            ('replay.details', [ReplayDetailsReader()]),
            ('replay.attributes.events', [AttributeEventsReader_17326(), AttributeEventsReader()]),
            ('replay.message.events', [MessageEventsReader()]),       
        ])

    processors = [
            PeopleProcessor(),
            AttributeProcessor(),
            TeamsProcessor(),
            MessageProcessor(),
            RecorderProcessor(),
        ]

#########################################################

class IntegrationConfig(Config):
    ReplayClass = Replay
    readers = OrderedDict([
            ('replay.initData', [ReplayInitDataReader()]),
            ('replay.details', [ReplayDetailsReader()]),
            ('replay.attributes.events', [AttributeEventsReader_17326(), AttributeEventsReader()]),
            ('replay.message.events', [MessageEventsReader()]),
            ('replay.game.events', [GameEventsReader()]),
        ])
        
    processors = []
