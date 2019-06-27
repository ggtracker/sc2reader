# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division


class InitGameEvent(object):
    name = "InitGame"


class EndGameEvent(object):
    name = "EndGame"


class PluginExit(object):
    name = "PluginExit"

    def __init__(self, plugin, code=0, details=None):
        self.plugin = plugin
        self.code = code
        self.details = details or {}
