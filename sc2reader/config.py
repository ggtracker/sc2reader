from __future__ import absolute_import

from sc2reader import readers as r
from sc2reader.utils import AttributeDict, RangeMap
from sc2reader import data

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


readers = RangeMap()
readers.add_range(0, 16561, {
        'replay.initData': r.InitDataReader(),
        'replay.details': r.DetailsReader(),
        'replay.attributes.events': r.AttributeEventsReader(),
        'replay.message.events': r.MessageEventsReader(),
        'replay.game.events': r.GameEventsReader(),
    })

readers.add_range(16561, 17326, {
        'replay.initData': r.InitDataReader(),
        'replay.details': r.DetailsReader(),
        'replay.attributes.events': r.AttributeEventsReader(),
        'replay.message.events': r.MessageEventsReader(),
        'replay.game.events': r.GameEventsReader_16561(),
    })

readers.add_range(17326, 18574, {
        'replay.initData': r.InitDataReader(),
        'replay.details': r.DetailsReader(),
        'replay.attributes.events': r.AttributeEventsReader_17326(),
        'replay.message.events': r.MessageEventsReader(),
        'replay.game.events': r.GameEventsReader_16561(),
    })

readers.add_range(18574, 19595, {
        'replay.initData': r.InitDataReader(),
        'replay.details': r.DetailsReader(),
        'replay.attributes.events': r.AttributeEventsReader_17326(),
        'replay.message.events': r.MessageEventsReader(),
        'replay.game.events': r.GameEventsReader_18574(),
    })

readers.add_range(19595, None, {
        'replay.initData': r.InitDataReader(),
        'replay.details': r.DetailsReader(),
        'replay.attributes.events': r.AttributeEventsReader_17326(),
        'replay.message.events': r.MessageEventsReader(),
        'replay.game.events': r.GameEventsReader_19595(),
    })

build_data = RangeMap()

#Use the only data dict we've got for now
build_data.add_range(0, None, data.Data_120_131)

#Uncommenting all of these would make them use the correct data dicts
#build_data.add_range(16561, 17326, data.Data_110_112)
#build_data.add_range(17326, 18317, data.Data_120_131)
#build_data.add_range(18317, 19595, data.Data_132_136)
#build_data.add_range(19595, None, data.Data_140_)