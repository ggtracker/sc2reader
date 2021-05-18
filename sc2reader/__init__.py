# -*- coding: utf-8 -*-
"""
    sc2reader
    ~~~~~~~~~~~

    A library for loading data from Starcraft II game resources.

    SC2Factory methods called on the package will be delegated to the default
    SC2Factory. To default to a cached factory set one or more of the following
    variables in your environment:

        SC2READER_CACHE_DIR = '/absolute/path/to/existing/cache/directory/'
        SC2READER_CACHE_MAX_SIZE = MAXIMUM_CACHE_ENTRIES_TO_HOLD_IN_MEMORY

    You can also set the default factory via setFactory, useFileCache, useDictCache,
    or useDoubleCache functions.

    :copyright: (c) 2011 by Graylin Kim.
    :license: MIT, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function, unicode_literals, division

__version__ = "1.7.0"

import os
import sys

# import submodules
from sc2reader import engine
from sc2reader import factories, log_utils

# setup the library logging
log_utils.setup()

# For backwards compatibility, goes away in 0.7
SC2Reader = factories.SC2Factory


def setFactory(factory):
    """
    :param factory: The new default factory for the package.

    Links the following sc2reader global methods to the specified factory::

        * sc2reader.load_replay(s)
        * sc2reader.load_map(s)
        * sc2reader.load_game_summar(y|ies)
        * sc2reader.configure
        * sc2reader.reset
        * sc2reader.register_plugin

    These methods when called will delegate to the factory for execution.
    """
    module = sys.modules[__name__]
    module.load_replays = factory.load_replays
    module.load_replay = factory.load_replay
    module.load_maps = factory.load_maps
    module.load_map = factory.load_map
    module.load_game_summaries = factory.load_game_summaries
    module.load_game_summary = factory.load_game_summary

    module.configure = factory.configure
    module.reset = factory.reset

    module.register_plugin = factory.register_plugin
    module._defaultFactory = factory


def useFileCache(cache_dir, **options):
    """
    :param cache_dir: Absolute path to the existing cache directory

    Set the default factory to a new FileCachedSC2Factory with the given cache_dir.
    All remote resources are saved to the file system for faster access times.
    """
    setFactory(factories.FileCachedSC2Factory(cache_dir, **options))


def useDictCache(cache_max_size=0, **options):
    """
    :param cache_max_size: The maximum number of cache entries to hold in memory

    Set the default factory to a new DictCachedSC2Factory with the given cache_dir.
    A limited number of remote resources are cached in memory for faster access times.
    """
    setFactory(factories.DictCachedSC2Factory(cache_max_size, **options))


def useDoubleCache(cache_dir, cache_max_size=0, **options):
    """
    :param cache_dir: Absolute path to the existing cache directory
    :param cache_max_size: The maximum number of cache entries to hold in memory

    Set the default factory to a new DoubleCachedSC2Factory with the given cache_dir.
    A limited number of remote resources are cached in memory for faster access times.
    All remote resources are saved to the file system for faster access times.
    """
    setFactory(factories.DoubleCachedSC2Factory(cache_dir, cache_max_size, **options))


# Allow environment variables to activate caching
cache_dir = os.getenv("SC2READER_CACHE_DIR")
cache_max_size = os.getenv("SC2READER_CACHE_MAX_SIZE")
if cache_dir and cache_max_size:
    useDoubleCache(cache_dir, cache_max_size)
elif cache_dir:
    useFileCache(cache_dir)
elif cache_max_size:
    useDictCache(cache_max_size)
else:
    setFactory(factories.SC2Factory())
