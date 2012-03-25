from __future__ import absolute_import

# import submodules
from sc2reader import listeners, data, scripts, processors

from sc2reader import factories, log_utils

# setup the library logging
log_utils.setup()

# For backwards compatibility
SC2Reader = factories.SC2Factory

# Expose a nice module level interface
__defaultSC2Reader = factories.SC2Factory()

register_datapack = __defaultSC2Reader.register_datapack
register_listener = __defaultSC2Reader.register_listener
register_reader = __defaultSC2Reader.register_reader

get_listeners = __defaultSC2Reader.get_listeners
get_datapack = __defaultSC2Reader.get_datapack
get_reader = __defaultSC2Reader.get_reader

load_replays = __defaultSC2Reader.load_replays
load_replay = __defaultSC2Reader.load_replay
load_maps = __defaultSC2Reader.load_maps
load_map = __defaultSC2Reader.load_map

configure = __defaultSC2Reader.configure
reset = __defaultSC2Reader.reset