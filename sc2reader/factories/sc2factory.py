# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from collections import defaultdict
from io import BytesIO
import os
import sys

try:
    unicode
except NameError:
    basestring = unicode = str

if sys.version_info[0] < 3:
    from urllib2 import urlopen
    from urlparse import urlparse
else:
    from urllib.request import urlopen
    from urllib.parse import urlparse

import re
import time

from sc2reader import utils
from sc2reader import log_utils
from sc2reader.resources import Resource, Replay, Map, GameSummary, Localization


@log_utils.loggable
class SC2Factory(object):
    """
    The SC2Factory class acts as a generic loader interface for all
    available to sc2reader resources. At current time this includes
    :class:`~sc2reader.resources.Replay` and :class:`~sc2reader.resources.Map` resources. These resources can be
    loaded in both singular and plural contexts with:

        * :meth:`load_replay` - :class:`Replay`
        * :meth:`load_replays` - generator<:class:`Replay`>
        * :meth:`load_map` - :class:`Map`
        * :meth:`load_maps` - : generator<:class:`Map`>

    The load behavior can be configured in three ways:

        * Passing options to the factory constructor
        * Using the :meth:`configure` method of a factory instance
        * Passing overried options into the load method

    See the :meth:`configure` method for more details on configuration
    options.

    Resources can be loaded in the singular context from the following inputs:

    * URLs - Uses the built-in package ``urllib``
    * File path - Uses the built-in method ``open``
    * File-like object - Must implement ``.read()``
    * DepotFiles - Describes remote Battle.net depot resources

    In the plural context the following inputs are acceptable:

    * An iterable of the above inputs
    * Directory path - Uses :meth:`~sc2reader.utils.get_files` with the appropriate extension to fine files.

    """

    _resource_name_map = dict(replay=Replay, map=Map)

    default_options = {
        Resource: {"debug": False},
        Replay: {"load_level": 4, "load_map": False},
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
        """
        Loads a single sc2replay file. Accepts file path, url, or file object.
        """
        return self.load(Replay, source, options, **new_options)

    def load_replays(self, sources, options=None, **new_options):
        """
        Loads a collection of sc2replay files, returns a generator.
        """
        return self.load_all(
            Replay, sources, options, extension="SC2Replay", **new_options
        )

    def load_localization(self, source, options=None, **new_options):
        """
        Loads a single s2ml file. Accepts file path, url, or file object.
        """
        return self.load(Localization, source, options, **new_options)

    def load_localizations(self, sources, options=None, **new_options):
        """
        Loads a collection of s2ml files, returns a generator.
        """
        return self.load_all(
            Localization, sources, options, extension="s2ml", **new_options
        )

    def load_map(self, source, options=None, **new_options):
        """
        Loads a single s2ma file. Accepts file path, url, or file object.
        """
        return self.load(Map, source, options, **new_options)

    def load_maps(self, sources, options=None, **new_options):
        """
        Loads a collection of s2ma files, returns a generator.
        """
        return self.load_all(Map, sources, options, extension="s2ma", **new_options)

    def load_game_summary(self, source, options=None, **new_options):
        """
        Loads a single s2gs file. Accepts file path, url, or file object.
        """
        return self.load(GameSummary, source, options, **new_options)

    def load_game_summaries(self, sources, options=None, **new_options):
        """
        Loads a collection of s2gs files, returns a generator.
        """
        return self.load_all(
            GameSummary, sources, options, extension="s2gs", **new_options
        )

    def configure(self, cls=None, **options):
        """
        Configures the factory to use the supplied options. If cls is specified
        the options will only be applied when loading that class
        """
        if isinstance(cls, basestring):
            cls = self._resource_name_map.get[cls.lower()]
        cls = cls or Resource
        self.options[cls].update(options)

    def reset(self):
        """
        Resets the options to factory defaults
        """
        self.options = defaultdict(dict)

    def register_plugin(self, cls, plugin):
        """
        Registers the given Plugin to be run on classes of the supplied name.
        """
        if isinstance(cls, basestring):
            cls = self._resource_name_map.get(cls.lower(), Resource)
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
        obj = cls(resource, filename=filename, factory=self, **options)
        for plugin in options.get("plugins", self._get_plugins(cls)):
            obj = plugin(obj)
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
        """
        Collections of resources or a path to a directory
        """
        options = options or self._get_options(Resource, **new_options)

        # Path to a folder, retrieve all relevant files as the collection
        if isinstance(resources, basestring):
            resources = utils.get_files(resources, **options)

        for resource in resources:
            yield self._load_resource(resource, options=options)

    def load_remote_resource_contents(self, resource, **options):
        self.logger.info("Fetching remote resource: " + resource)
        return urlopen(resource).read()

    def load_local_resource_contents(self, location, **options):
        # Extract the contents so we can close the file
        with open(location, "rb") as resource_file:
            return resource_file.read()

    def _load_resource(self, resource, options=None, **new_options):
        """
        http links, filesystem locations, and file-like objects
        """
        options = options or self._get_options(Resource, **new_options)

        if isinstance(resource, utils.DepotFile):
            resource = resource.url

        if isinstance(resource, basestring):
            if re.match(r"https?://", resource):
                contents = self.load_remote_resource_contents(resource, **options)

            else:
                directory = options.get("directory", "")
                location = os.path.join(directory, resource)
                contents = self.load_local_resource_contents(location, **options)

            # BytesIO implements a fuller file-like object
            resource_name = resource
            resource = BytesIO(contents)

        else:
            # Totally not designed for large files!!
            # We need a multiread resource, so wrap it in BytesIO
            if not hasattr(resource, "seek"):
                resource = BytesIO(resource.read())

            resource_name = getattr(resource, "name", "Unknown")

        if options.get("verbose", None):
            print(resource_name)

        return (resource, resource_name)


class CachedSC2Factory(SC2Factory):
    def get_remote_cache_key(self, remote_resource):
        # Strip the port and use the domain as the bucket
        # and use the full path as the key
        parseresult = urlparse(remote_resource)
        bucket = re.sub(r":.*", "", parseresult.netloc)
        key = parseresult.path.strip("/")
        return (bucket, key)

    def load_remote_resource_contents(self, remote_resource, **options):
        cache_key = self.get_remote_cache_key(remote_resource)
        if not self.cache_has(cache_key):
            resource = super(CachedSC2Factory, self).load_remote_resource_contents(
                remote_resource, **options
            )
            self.cache_set(cache_key, resource)
        else:
            resource = self.cache_get(cache_key)
        return resource

    def cache_has(self, cache_key):
        raise NotImplemented()

    def cache_get(self, cache_key):
        raise NotImplemented()

    def cache_set(self, cache_key, value):
        raise NotImplemented()


class FileCachedSC2Factory(CachedSC2Factory):
    """
    :param cache_dir: Local directory to cache files in.

    Extends :class:`SC2Factory`.

    Caches remote depot resources on the file system in the ``cache_dir``.
    """

    def __init__(self, cache_dir, **options):
        super(FileCachedSC2Factory, self).__init__(**options)
        self.cache_dir = os.path.abspath(cache_dir)
        if not os.path.isdir(self.cache_dir):
            raise ValueError(
                "cache_dir ({0}) must be an existing directory.".format(self.cache_dir)
            )
        elif not os.access(self.cache_dir, os.F_OK | os.W_OK | os.R_OK):
            raise ValueError(
                "Must have read/write access to {0} for local file caching.".format(
                    self.cache_dir
                )
            )

    def cache_has(self, cache_key):
        return os.path.exists(self.cache_path(cache_key))

    def cache_get(self, cache_key, **options):
        return self.load_local_resource_contents(self.cache_path(cache_key), **options)

    def cache_set(self, cache_key, value):
        cache_path = self.cache_path(cache_key)
        bucket_dir = os.path.dirname(cache_path)
        if not os.path.exists(bucket_dir):
            os.makedirs(bucket_dir)

        with open(cache_path, "wb") as out:
            out.write(value)

    def cache_path(self, cache_key):
        return os.path.join(self.cache_dir, *(cache_key))


class DictCachedSC2Factory(CachedSC2Factory):
    """
    :param cache_max_size: The max number of cache entries to hold in memory.

    Extends :class:`SC2Factory`.

    Caches remote depot resources in memory. Does not write to the file system.
    The cache is effectively cleared when the process exits.
    """

    def __init__(self, cache_max_size=0, **options):
        super(DictCachedSC2Factory, self).__init__(**options)
        self.cache_dict = dict()
        self.cache_used = dict()
        self.cache_max_size = cache_max_size

    def cache_set(self, cache_key, value):
        if self.cache_max_size and len(self.cache_dict) >= self.cache_max_size:
            oldest_cache_key = min(self.cache_used.items(), key=lambda e: e[1])[0]
            del self.cache_used[oldest_cache_key]
            del self.cache_dict[oldest_cache_key]
        self.cache_dict[cache_key] = value
        self.cache_used[cache_key] = time.time()

    def cache_get(self, cache_key):
        self.cache_used[cache_key] = time.time()
        return self.cache_dict[cache_key]

    def cache_has(self, cache_key):
        return cache_key in self.cache_dict


class DoubleCachedSC2Factory(DictCachedSC2Factory, FileCachedSC2Factory):
    """
    :param cache_dir: Local directory to cache files in.
    :param cache_max_size: The max number of cache entries to hold in memory.

    Extends :class:`SC2Factory`.

    Caches remote depot resources to the file system AND holds a subset of them
    in memory for more efficient access.
    """

    def __init__(self, cache_dir, cache_max_size=0, **options):
        super(DoubleCachedSC2Factory, self).__init__(
            cache_max_size, cache_dir=cache_dir, **options
        )

    def load_remote_resource_contents(self, remote_resource, **options):
        cache_key = self.get_remote_cache_key(remote_resource)

        if DictCachedSC2Factory.cache_has(self, cache_key):
            return DictCachedSC2Factory.cache_get(self, cache_key)

        if not FileCachedSC2Factory.cache_has(self, cache_key):
            resource = SC2Factory.load_remote_resource_contents(
                self, remote_resource, **options
            )
            FileCachedSC2Factory.cache_set(self, cache_key, resource)
        else:
            resource = FileCachedSC2Factory.cache_get(self, cache_key)

        DictCachedSC2Factory.cache_set(self, cache_key, resource)
        return resource
