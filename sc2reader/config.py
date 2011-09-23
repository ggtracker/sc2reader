from .processors import *
from .readers import *
from .utils import AttributeDict

ALL_FILES = [
    'replay.initData',
    'replay.details',
    'replay.attributes.events',
    'replay.message.events',
    'replay.game.events'
]

files = AttributeDict(
    all=[
        'replay.initData',
        'replay.details',
        'replay.attributes.events',
        'replay.message.events',
        'replay.game.events'],

    partial=[
        'replay.initData',
        'replay.details',
        'replay.attributes.events',
        'replay.message.events',],

    basic=[
        'replay.initData',
        'replay.details',
        'replay.attributes.events'],

    minimal=[
        'replay.initData',],

    none=[]
)

default_options = AttributeDict(
    directory="",
    processors=[],
    debug=False,
    verbose=False,
    parse_events=True,
    include_regex=None,
    exclude_dirs=[],
    recursive=True,
    depth=-1,
    follow_symlinks=True,
    files=files.all,
    apply=False
)

class ReaderMap(dict):
    def __init__(self):
        self.set1 = {
                'replay.initData': InitDataReader(),
                'replay.details': DetailsReader(),
                'replay.attributes.events': AttributeEventsReader(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader(),
            }

        self.set2 = {
                'replay.initData': InitDataReader(),
                'replay.details': DetailsReader(),
                'replay.attributes.events': AttributeEventsReader(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader_16561(),
            }

        self.set3 = {
                'replay.initData': InitDataReader(),
                'replay.details': DetailsReader(),
                'replay.attributes.events': AttributeEventsReader_17326(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader_16561(),
            }

        self.set4 = {
                'replay.initData': InitDataReader(),
                'replay.details': DetailsReader(),
                'replay.attributes.events': AttributeEventsReader_17326(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader_18574(),
        }

        self.set5 = {
                'replay.initData': InitDataReader(),
                'replay.details': DetailsReader(),
                'replay.attributes.events': AttributeEventsReader_17326(),
                'replay.message.events': MessageEventsReader(),
                'replay.game.events': GameEventsReader_19595(),
        }

        # 1.0.0-3
        for key in (16117,16195,16223,16291):
            self[key] = self.set1

        # 1.1.0-3
        for key in (16561,16605,16755,16939):
            self[key] = self.set2

        # 1.2.0-1.3.2
        for key in (17326,17682,17811,18092,18221,18317):
            self[key] = self.set3

        # 1.3.3-1.3.6
        for key in (18574,18701,19132,19269):
            self[key] = self.set4

        # 1.4beta, 1.4.0
        for key in (19595,19679):
            self[key] = self.set5

    def __getitem__(self,key):
        try:
            return super(ReaderMap,self).__getitem__(key)
        # Keep using the latest dict for all newer replay versions
        except KeyError:
            return self.set5

readers = ReaderMap()
