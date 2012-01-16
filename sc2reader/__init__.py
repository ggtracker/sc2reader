from __future__ import absolute_import

import os
from sc2reader import utils
from sc2reader import readers
from sc2reader import data
from sc2reader import exceptions
from sc2reader.replay import Replay
from collections import defaultdict

class SC2Reader(object):

    default_options = dict(
        # General use
        verbose=False,
        debug=False,

        # Related to the SC2Reader class only
        register_defaults=True,

        # Related to creating new replay objects
        autoplay=True,
        complete=True,

        # Related to passing paths into load_replay(s)
        directory='',

        # Related to passing a directory to load_replays
        depth=-1,
        exclude=[],
        followlinks=False
    )

    def __init__(self, **options):
        self.registered_readers = defaultdict(list)
        self.registered_datapacks = list()
        self.registered_listeners = defaultdict(list)

        self.options = utils.AttributeDict(utils.merged_dict(self.default_options, options))

        if self.options.register_defaults:
            self.register_defaults()

    def load_replays(self, replay_collection, options=None, **new_options):
        options = options or utils.merged_dict(self.options, new_options)
        if isinstance(replay_collection, basestring):
            directory = os.path.join(options.get('directory',''), replay_collection)
            del options['directory'] # don't need this anymore on this request
            for replay_path in utils.get_replay_files(directory, **options):
                with open(replay_path) as replay_file:
                    try:
                        yield self.load_replay(replay_file, options=options)
                    except exceptions.MPQError as e:
                        print e

        else:
            for replay_file in replay_collection:
                yield self.load_replay(replay_file, options=options)

    def load_replay(self, replay_file, options=None, **new_options):
        options = options or utils.merged_dict(self.options, new_options)
        complete = options.get('complete',True)
        autoplay = options.get('autoplay',True)


        if isinstance(replay_file, basestring):
            location = os.path.join(options.get('directory',''), replay_file)
            with open(location, 'rb') as replay_file:
                return self.load_replay(replay_file, options=options)

        if options['verbose']:
            print replay_file.name

        replay = Replay(replay_file, **options)

        for data_file in ('replay.initData',
                          'replay.details',
                          'replay.attributes.events',
                          'replay.message.events',):
            reader = self.get_reader(data_file, replay)
            replay.read_data(data_file, reader)

        replay.load_details()
        replay.load_players()

        if complete:
            for data_file in ('replay.game.events',):
                reader = self.get_reader(data_file, replay)
                replay.read_data(data_file, reader)

            replay.load_events(self.get_datapack(replay))

            if autoplay:
                replay.listeners = self.get_listeners(replay)
                replay.start()

        return replay


    def get_reader(self, data_file, replay):
        for callback, reader in self.registered_readers[data_file]:
            if callback(replay):
                return reader

    def get_datapack(self, replay):
        for callback, datapack in self.registered_datapacks:
            if callback(replay):
                return datapack
        return None

    def get_listeners(self, replay):
        listeners = defaultdict(list)
        for event_class in self.registered_listeners.keys():
            for callback, listener in self.registered_listeners[event_class]:
                if callback(replay):
                    listeners[event_class].append(listener)
        return listeners


    def register_listener(self, event_class, listener, callback=lambda r: True):
        self.registered_listeners[event_class].append((callback, listener))

    def register_reader(self, data_file, reader, callback=lambda r: True):
        self.registered_readers[data_file].insert(0,(callback, reader))

    def register_datapack(self, datapack, callback=lambda r: True):
        self.registered_datapacks.insert(0,(callback, datapack))


    def register_defaults(self):
        self.register_default_readers()
        self.register_default_datapacks()
        self.register_default_listeners()

    def register_default_readers(self):
        self.register_reader('replay.details', readers.DetailsReader_Base())
        self.register_reader('replay.initData', readers.InitDataReader_Base())
        self.register_reader('replay.message.events', readers.MessageEventsReader_Base())
        self.register_reader('replay.attributes.events', readers.AttributesEventsReader_Base(), lambda r: r.build <  17326)
        self.register_reader('replay.attributes.events', readers.AttributesEventsReader_17326(), lambda r: r.build >= 17326)
        self.register_reader('replay.game.events', readers.GameEventsReader_Base(), lambda r: r.build <  16561)
        self.register_reader('replay.game.events', readers.GameEventsReader_16561(), lambda r: 16561 <= r.build < 18574)
        self.register_reader('replay.game.events', readers.GameEventsReader_18574(), lambda r: 18574 <= r.build < 19595)
        self.register_reader('replay.game.events', readers.GameEventsReader_19595(), lambda r: 19595 <= r.build)

    def register_default_datapacks(self):
        self.register_datapack(data.Data_16561, lambda r: 16561 <= r.build < 17326)
        self.register_datapack(data.Data_17326, lambda r: 17326 <= r.build < 18317)
        self.register_datapack(data.Data_18317, lambda r: 18317 <= r.build < 19595)
        self.register_datapack(data.Data_19595, lambda r: 19595 <= r.build)

    def register_default_listeners(self):
        #self.register_listener(Event, PrintEventListener())
        pass


__defaultSC2Reader = SC2Reader()

register_datapack = __defaultSC2Reader.register_datapack
register_listener = __defaultSC2Reader.register_listener
register_reader = __defaultSC2Reader.register_reader

get_listeners = __defaultSC2Reader.get_listeners
get_datapack = __defaultSC2Reader.get_datapack
get_reader = __defaultSC2Reader.get_reader

load_replay = __defaultSC2Reader.load_replay
load_replays = __defaultSC2Reader.load_replays