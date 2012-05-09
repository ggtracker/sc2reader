from __future__ import absolute_import

# import submodules
from sc2reader import listeners, data, scripts

from sc2reader import factories, log_utils

# setup the library logging
log_utils.setup()

# For backwards compatibility
SC2Reader = factories.SC2Factory

# Expose a nice module level interface
__defaultSC2Reader = factories.SC2Factory()

load_replays = __defaultSC2Reader.load_replays
load_replay = __defaultSC2Reader.load_replay
load_maps = __defaultSC2Reader.load_maps
load_map = __defaultSC2Reader.load_map
load_game_summaries = __defaultSC2Reader.load_game_summaries
load_game_summary = __defaultSC2Reader.load_game_summary
load_map_infos = __defaultSC2Reader.load_map_infos
load_map_info = __defaultSC2Reader.load_map_info
load_map_histories = __defaultSC2Reader.load_map_headers
load_map_history = __defaultSC2Reader.load_map_header

configure = __defaultSC2Reader.configure
reset = __defaultSC2Reader.reset
