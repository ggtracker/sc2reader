from __future__ import absolute_import

import os
import re

import urllib2
from cStringIO import StringIO

from collections import defaultdict


from sc2reader import readers
from sc2reader import data
from sc2reader import exceptions
from sc2reader import utils
from sc2reader import log_utils
from sc2reader.resources import Replay, Map, GameSummary, MapInfo, MapHeader

class SC2Factory(object):
    """
    The primary interface to the sc2reader library. Acts as a configurable
    factory for :class:`Replay` objects. Maintains a set of registered readers,
    datapacks, and listeners with filterfuncs that allow the factory to apply
    a replay specific context to each replay as it loads.

    #TODO:  Include some examples here...

    See the specific functions below for details.

    :param True register_defaults: Automatically registers default readers
        and datapacks. Only disable if you know what you are doing.

    :param True load_events: Enables parsing of game events. If you are do
        not need this information setting to false will reduce replay load
        time.

    :param True autoplay: Enables auto playing of replays after loading game
        events. Playing events triggers enables registered listeners to add
        new data features to replays. Option ignored if load_events is false.

    :param False load_map: Triggers downloading and parsing of map files
        associated with replays as they are loaded. When false, only the map
        url and name are available.

    :param False verbose: Causes many steps in the replay loading process
        to produce more verbose output.

    :param string directory: Specifies a base directory to prepend to all paths
        before attempting to load the replay.

    :param -1 depth: Indicates the maximum search depth when loading replays
        from directories. -1 indicates no limit, 0 turns recursion off.

    :param list exclude: A list of directory names (not paths) to exclude when
        performing recursive searches while loading replays from directories.

    :param False followlinks: Enables symlink following when recursing through
        directories to load replay files.

    """

    default_options = dict(
        # General use
        debug=False,

        # Related to the SC2Reader class only
        register_defaults=True,

        # Related to creating new replay objects
        autoplay=True,
        load_events=True,
        load_map=False,

        # Related to passing paths into load_replay(s)
        directory='',

        # Related to passing a directory to load_replays
        depth=-1,
        exclude=[],
        followlinks=False
    )

    def __init__(self, **options):
        self.reset()
        self.configure(**options)
        self.logger = log_utils.get_logger(self.__class__)

        if self.options.get('register_defaults',None):
            self.register_defaults()


    def configure(self, **new_options):
        """
        Update the factory settings with the specified overrides.

        See :class:`SC2Reader` for a list of available options.

        :param new_options: Option values to override current factory settings.
        """
        self.options.update(new_options)

    def reset(self):
        """
        Resets the current factory to default settings and removes all
        registered readers, datapacks, and listeners.
        """
        self.options = utils.AttributeDict(self.default_options)
        self.registered_readers = defaultdict(list)
        self.registered_datapacks = list()
        self.registered_listeners = list()

    def load_resources(self, resources, resource_loader, options=None, **new_options):
        """
        Loads the specified set of resources using the current factory settings
        with specified overrides.

        :param resources: Either a path/url or a mixed collection of
            directories, paths/urls, and open file objects.

        :param None options: When options are passed directly into the options
            parameter the current factory settings are ignored and only the
            specified options are used during replay load.

        :param new_options: Options values to override current factory settings
            for the collection of replays to be loaded.

        :rtype: generator(Resource)
        """
        options = options or utils.merged_dict(self.options, new_options)

        # Path to a resource?
        if isinstance(resources, basestring):
            if re.match(r'https?://',resources):
                yield resource_loader(resources, options=options)
            else:
                for resource in utils.get_files(resources, **options):
                    try:
                        yield resource_loader(resource, options=options)
                    except Exception as e:
                        print "\n\n\nFAILURE!!!\n\n\n"
                        yield None

        # File like object?
        elif hasattr(resources,'read'):
            yield resource_loader(resources, options=options)

        # Collection of the above
        else:
            for resource in resources:
                yield resource_loader(resource, options=options)

    def load_resource(self, resource, options=None, **new_options):
        options = options or utils.merged_dict(self.options, new_options)

        if isinstance(resource, basestring):
            if re.match(r'https?://',resource):
                self.logger.info("Fetching remote resource: "+resource)
                contents = urllib2.urlopen(resource).read()

            else:
                directory = options.get('directory','')
                location = os.path.join(directory, resource)

                # Extract the contents so we can close the file
                with open(location, 'rb') as resource_file:
                    contents = resource_file.read()

            # StringIO implements a fuller file-like object
            resource_name = resource
            resource = StringIO(contents)

        else:
            # Totally not designed for large files!!
            # We need a multiread resource, so wrap it in StringIO
            if not hasattr(resource,'seek'):
                resource = StringIO(resource.read())

            resource_name = getattr(resource, 'name', 'Unknown')

        return (resource, resource_name)

    def load_game_summaries(self, gs, options=None, **new_options):
        """
        Loads a collection of game summaries. See load_resources for detailed parameter
        documentation.

        :rtype: generator(:class:`GameSummary`)
        """
        for s in self.load_resources(gs, self.load_game_summary, options=options, extensions=['.s2gs'], **new_options):
            yield s

    def load_game_summary(self, summary_file, options=None, **new_options):
        """
        Loads the specified summary using the current factory settings with the
        specified overrides.

        :param summary_file: An open file object or path/url to a single file

        :param None options: When options are passed directly into the options
            parameter the current factory settings are ignored and only the
            specified options are used during replay load.

        :param new_options: Options values to override current factory settings
            while loading this map.

        :rtype: :class:`GameSummary`
        """
        options = options or utils.merged_dict(self.options, new_options)
        resource, name = self.load_resource(summary_file, options=options)
        s2gs = GameSummary(resource, name, **options)

        # Load summary procedure here!
        #

        return s2gs

    def load_map_infos(self, infos, options=None, **new_options):
        """
        Loads a collection of MapInfos. See load_resources for detailed
        parameter documentation.

        :rtype: generator(:class:`MapInfo`)
        """
        for s2mi in self.load_resources(infos, self.load_map_info, options=options, extensions=['.s2mi'], **new_options):
            yield s2mi

    def load_map_info(self, info_file, options=None, **new_options):
        """
        Loads the specified map info using the current factory settings with
        the specified overrides.

        :param info_file: An open file object or path/url to a single file

        :param None options: When options are passed directly into the options
            parameter the current factory settings are ignored and only the
            specified options are used during replay load.

        :param new_options: Options values to override current factory settings
            while loading this map.

        :rtype: :class:`MapInfo`
        """
        options = options or utils.merged_dict(self.options, new_options)
        resource, name = self.load_resource(info_file, options=options)
        s2mi = MapInfo(resource, name, **options)

        # Load summary procedure here!
        #

        return s2mi

    def load_map_headers(self, headers, options=None, **new_options):
        """
        Loads a collection of map header files. See load_resources for
        detailed parameter documentation.

        :rtype: generator(:class:`MapHeader`)
        """
        for s2mh in self.load_resources(headers, self.load_map_header, options=options, extensions=['.s2mh'], **new_options):
            yield s2mh

    def load_map_header(self, header_file, options=None, **new_options):
        """
        Loads the specified match info using the current factory settings with
        the specified overrides.

        :param header_file: An open file object or path/url to a single file

        :param None options: When options are passed directly into the options
            parameter the current factory settings are ignored and only the
            specified options are used during replay load.

        :param new_options: Options values to override current factory settings
            while loading this map.

        :rtype: :class:`MapHeader`
        """
        options = options or utils.merged_dict(self.options, new_options)
        resource, name = self.load_resource(header_file, options=options)
        print name
        s2mh = MapHeader(resource, name, **options)

        # Load summary procedure here!
        #

        return s2mh

    def load_maps(self, maps, options=None, **new_options):
        """
        Loads a collection of replays. See load_resources for detailed parameter
        documentation.

        :rtype: generator(:class:`Map`)
        """
        for m in self.load_resources(maps, self.load_map, options=options, extensions=['.s2ma'], **new_options):
            yield m

    def load_map(self, map_file, options=None, **new_options):
        """
        Loads the specified map using the current factory settings with the
        specified overrides.

        :param map_file: An open file object or path/url to a single file

        :param None options: When options are passed directly into the options
            parameter the current factory settings are ignored and only the
            specified options are used during replay load.

        :param new_options: Options values to override current factory settings
            while loading this map.

        :rtype: :class:`Replay`
        """
        options = options or utils.merged_dict(self.options, new_options)
        resource, name = self.load_resource(map_file, options=options)
        m = Map(resource, name, **options)

        # Build different parts of the map!
        #

        return m


    def load_replays(self, replays, options=None, **new_options):
        """
        Loads a collection of replays. See load_resources for detailed parameter
        documentation.

        :rtype: generator(:class:`Replay`)
        """
        for r in self.load_resources(replays, self.load_replay, options=options, extensions=['.sc2replay'], **new_options):
            yield r

    def load_replay(self, replay_file, options=None, **new_options):
        """
        Loads the specified replay using current factory settings with the
        specified overrides.

        :param replay_file: An open file object or a path/url to a single file.

        :param None options: When options are passed directly into the options
            parameter the current factory settings are ignored and only the
            specified options are used during replay load.

        :param new_options: Options values to override current factory settings
            while loading this replay.

        :rtype: :class:`Replay`
        """
        self.logger.info("Reading {0}".format(replay_file))
        options = options or utils.merged_dict(self.options, new_options)
        resource, name = self.load_resource(replay_file, options=options)
        replay = Replay(resource, name, **options)

        load_events = options.get('load_events',True)
        load_map = options.get('load_map',False)
        autoplay = options.get('autoplay',True)

        for data_file in ('replay.initData',
                          'replay.details',
                          'replay.attributes.events',
                          'replay.message.events',):
            reader = self.get_reader(data_file, replay)
            replay.read_data(data_file, reader)

        replay.load_details()
        replay.load_players()

        if load_map:
            map_url = Map.get_url(replay.gateway, replay.map_hash)
            replay.map = self.load_map(map_url, gateway=replay.gateway, map_hash=replay.map_hash)

        if load_events:
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
        listeners = list()
        for callback, listener in self.registered_listeners:
            if callback(replay):
                listeners.append(listener)
        return listeners


    def register_listener(self, listener, filterfunc=lambda r: True):
        """
        Allows you to specify event listeners for adding new features to the
        :class:`Replay` objects on :meth:`~Replay.play`. sc2reader comes with a
        small collection of :class:`Listener` classes that you can apply to your
        replays as needed. Events are sent to listeners in registration order as
        they come up. See the tutorials for more information.

        :param listener: The :class:`Listener` object you want events sent to.
            You must pass an instanciated object NOT a class. This gives you an
            opportunity to configure the listener before registration.

        :param filterfunc: A function that accepts a partially loaded
            :class:`Replay` object as an argument and returns true if the
            reader should be used on this replay.
        """
        self.registered_listeners.append((filterfunc, listener))

    def register_reader(self, data_file, reader, filterfunc=lambda r: True):
        """
        Allows you to specify your own reader for use when reading the data
        files packed into the .SC2Replay archives. Datapacks are checked for
        use with the supplied filterfunc in reverse registration order to give
        user registered datapacks preference over factory default datapacks.

        Don't use this unless you know what you are doing.

        :param data_file: The full file name that you would like this reader to
            parse.

        :param reader: The :class:`Reader` object you wish to use to read the
            data file.

        :param filterfunc: A function that accepts a partially loaded
            :class:`Replay` object as an argument and returns true if the
            reader should be used on this replay.
        """
        self.registered_readers[data_file].insert(0,(filterfunc, reader))

    def register_datapack(self, datapack, filterfunc=lambda r: True):
        """
        Allows you to specify your own datapacks for use when loading replays.
        Datapacks are checked for use with the supplied filterfunc in reverse
        registration order to give user registered datapacks preference over
        factory default datapacks.

        This is how you would add mappings for your favorite custom map.

        :param datapack: A :class:`BaseData` object to use for mapping unit
            types and ability codes to their corresponding classes.

        :param filterfunc: A function that accepts a partially loaded
            :class:`Replay` object as an argument and returns true if the
            datapack should be used on this replay.
        """
        self.registered_datapacks.insert(0,(filterfunc, datapack))


    def register_defaults(self):
        """Registers all factory default objects."""
        self.register_default_readers()
        self.register_default_datapacks()

    def register_default_readers(self):
        """Registers factory default readers."""
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
        """Registers factory default datapacks."""
        self.register_datapack(data.Data_16561, lambda r: 16561 <= r.build < 17326)
        self.register_datapack(data.Data_17326, lambda r: 17326 <= r.build < 18317)
        self.register_datapack(data.Data_18317, lambda r: 18317 <= r.build < 19595)
        self.register_datapack(data.Data_19595, lambda r: 19595 <= r.build)

class SC2Cache(SC2Factory):

    def __init__(self, **options):
        super(SC2Cache, self).__init__(self, **options)
        self.cache = IntitializeCache(**options)

    def load_map(self, map_file, options=None, **new_options):
        options = options or utils.merged_dict(self.options, new_options)

        if self.cache.has(map_file):
            return self.cache.get(map_file)
        else:
            map = super(SC2Cache, self).load_map(map_file, options=options)
            self.cache.set(map_file, map)
            return map

    def load_replay(self, replay_file, options=None, **new_options):
        options = options or utils.merged_dict(self.options, new_options)

        if self.cache.has(replay_file):
            return self.cache.get(replay_file)
        else:
            replay = super(SC2Cache, self).load_replay(replay_file, options=options)
            self.cache.set(replay_file, replay)
            return replay
