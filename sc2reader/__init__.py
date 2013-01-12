from __future__ import absolute_import

import sys

# import submodules
from sc2reader import plugins, data, scripts

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
    module.load_map_infos = factory.load_map_infos
    module.load_map_info = factory.load_map_info
    module.load_map_histories = factory.load_map_headers
    module.load_map_history = factory.load_map_header

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

setFactory(factories.SC2Factory())


