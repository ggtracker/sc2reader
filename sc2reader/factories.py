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
from sc2reader.resources import Resource, Replay, Map, GameSummary, MapInfo, MapHeader

class SC2Factory(object):
    """The SC2Factory class acts as a generic loader interface for all
    available to sc2reader resources. At current time this includes
    :class:`Replay` and :class:`Map` resources. These resources can be
    loaded in both singular and plural contexts with:

        * :method:`load_replay` - :class:`Replay`
        * :method:`load_replays` - generator<:class:`Replay`>
        * :method:`load_map` - :class:`Map`
        * :method:`load_maps` - : generator<:class:`Map`>

    The load behavior can be configured in three ways:

        # Passing options to the factory constructor
        # Using the :method:`configure` method of a factory instance
        # Passing overried options into the load method

    See the :method:`configure` method for more details on configuration
    options.

    sc2reader comes with some post processing capabilities which, depending
    on your needs, may be useful. You can register these plugins to the load
    process with the :method:`register_plugins` method.
    """

    _resource_name_map = dict(replay=Replay,map=Map)

    default_options = {
        Resource: {'debug':False},
        Replay: {'load_level':4, 'load_map':False},
    }

    def __init__(self, **options):
        self.plugins = list()

        # Bootstrap with the default options
        self.options = defaultdict(dict)
        for cls, options in self.default_options.items():
            self.options[cls] = options.copy()


        # Then configure with the options passed in
        self.configure(**options)

    # Primary Interface
    def load_replay(self, source, options=None, **new_options):
        return self.load(Replay, source, options, **new_options)

    def load_replays(self, sources, options=None, **new_options):
        return self.load_all(Replay, sources, options, extension='SC2Replay', **new_options)

    def load_map(self, source, options=None, **new_options):
        return self.load(Map, source, options, **new_options)

    def load_maps(self, sources, options=None, **new_options):
        return self.load_all(Map, sources, options, extension='s2ma', **new_options)

    def load_game_summary(self, source, options=None, **new_options):
        return self.load(GameSummary, source, options, **new_options)

    def load_game_summaries(self, sources, options=None, **new_options):
        return self.load_all(GameSummary, sources, options, extension='s2gs', **new_options)

    def load_map_info(self, source, options=None, **new_options):
        return self.load(MapInfo, source, options, **new_options)

    def load_map_infos(self, sources, options=None, **new_options):
        return self.load_all(MapInfo, sources, options, extension='s2mi', **new_options)

    def load_map_header(self, source, options=None, **new_options):
        return self.load(MapHeader, source, options, **new_options)

    def load_map_headers(self, sources, options=None, **new_options):
        return plugins_all(MapHeader, sources, options, extension='s2mh', **new_options)

    def configure(self, cls=None, **options):
        if isinstance(cls, basestring):
            cls = self._resource_name_map.get[cls.lower()]
        cls = cls or Resource
        self.options[cls].update(options)

    def reset(self):
        self.options = defaultdict(dict)

    def register_plugin(self, cls, plugin):
        if isinstance(cls, basestring):
            cls = self._resource_name_map.get(cls.lower(),Resource)
        self.plugins.append((cls, plugin))


    # Support Functions
    def load(self, cls, source, options=None, **new_options):
        options = options or self._get_options(cls, **new_options)
        resource, filename = self._load_resource(source, options=options)
        return self._load(cls, resource, filename=filename, options=options)

    def load_all(self, cls, sources, options=None, **new_options):
        options = options or self._get_options(cls, **new_options)
        for resource, filename in self._load_resources(sources, options=options):
            yield self._load(cls, resource, filename=filename, options=options)


    # Internal Functions
    def _load(self, cls, resource, filename, options):
        obj = cls(resource, filename=filename, **options)
        for plugin in options.get('plugins',self._get_plugins(cls)):
            # TODO: What if you want to do a transform?
            plugin(obj)
        return obj

    def _get_plugins(self, cls):
        plugins = list()
        for ext_cls, plugin in self.plugins:
            if issubclass(cls, ext_cls):
                plugins.append(plugin)
        return plugins

    def _get_options(self, cls, **new_options):
        options = dict()
        for opt_cls, cls_options in self.options.items():
            if issubclass(cls, opt_cls):
                options.update(cls_options)
        options.update(new_options)
        return options

    def _load_resources(self, resources, options=None, **new_options):
        """Collections of resources or a path to a directory"""
        options = options or self._get_options(Resource, **new_options)

        # Path to a folder, retrieve all relevant files as the collection
        if isinstance(resources, basestring):
            resources = utils.get_files(resources, **options)

        for resource in resources:
            yield self._load_resource(resource, options=options)

    def _load_resource(self, resource, options=None, **new_options):
        """http links, filesystem locations, and file-like objects"""
        options = options or self._get_options(Resource, **new_options)
        print resource
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
