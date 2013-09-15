# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

__version__ = "0.6.3"

import os
import sys

# import submodules
from sc2reader import engine
from sc2reader import factories, log_utils

# setup the library logging
log_utils.setup()

# For backwards compatibility
SC2Reader = factories.SC2Factory


def setFactory(factory):
    # Expose a nice module level interface
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
    setFactory(factories.FileCachedSC2Factory(cache_dir, **options))


def useDictCache(cache_max_size=0, **options):
    setFactory(factories.DictCachedSC2Factory(cache_max_size, **options))


def useDoubleCache(cache_dir, cache_max_size=0, **options):
    setFactory(factories.DoubleCachedSC2Factory(cache_dir, cache_max_size, **options))


# Allow environment variables to activate caching
cache_dir = os.getenv('SC2READER_CACHE_DIR')
cache_max_size = os.getenv('SC2READER_CACHE_MAX_SIZE')
if cache_dir and cache_max_size:
    useDoubleCache(cache_dir, cache_max_size)
elif cache_dir:
    useFileCache(cache_dir)
elif cache_max_size:
    useDictCache(cache_max_size)
else:
    setFactory(factories.SC2Factory())
