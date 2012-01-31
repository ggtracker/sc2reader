from __future__ import absolute_import

from sc2reader.sc2reader import SC2Reader

__defaultSC2Reader = SC2Reader()

register_datapack = __defaultSC2Reader.register_datapack
register_listener = __defaultSC2Reader.register_listener
register_reader = __defaultSC2Reader.register_reader

get_listeners = __defaultSC2Reader.get_listeners
get_datapack = __defaultSC2Reader.get_datapack
get_reader = __defaultSC2Reader.get_reader

load_replay = __defaultSC2Reader.load_replay
load_replays = __defaultSC2Reader.load_replays

configure = __defaultSC2Reader.configure
reset = __defaultSC2Reader.reset