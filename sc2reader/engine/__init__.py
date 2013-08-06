# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import sys
from sc2reader.engine.engine import GameEngine, PluginExit
from sc2reader.engine.utils import GameState
from sc2reader.engine.plugins.apm import APMTracker
from sc2reader.engine.plugins.selection import SelectionTracker
from sc2reader.engine.plugins.context import ContextLoader
from sc2reader.engine.plugins.supply import SupplyTracker
from sc2reader.engine.plugins.creeptracker import CreepTracker


def setGameEngine(engine):
    module = sys.modules[__name__]
    module.run = engine.run
    module.plugins = engine.plugins
    module.register_plugin = engine.register_plugin
    module.register_plugins = engine.register_plugins

_default_engine = GameEngine()
_default_engine.register_plugin(ContextLoader())
setGameEngine(_default_engine)
