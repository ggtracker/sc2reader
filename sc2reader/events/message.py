# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sc2reader.events.base import Event
from sc2reader.log_utils import loggable

@loggable
class MessageEvent(Event):
    name = 'MessageEvent'

    def __init__(self, frame, pid, flags):
        super(MessageEvent, self).__init__(frame, pid)
        self.flags=flags

@loggable
class ChatEvent(MessageEvent):
    name = 'ChatEvent'

    def __init__(self, frame, pid, flags, target, text, extension):
        super(ChatEvent, self).__init__(frame, pid, flags)
        self.target = target
        self.extension = extension
        self.text = text
        self.to_all = (self.target == 0)
        self.to_allies = (self.target == 2)
        self.to_observers = (self.target == 4)

@loggable
class PacketEvent(MessageEvent):
    name = 'PacketEvent'

    def __init__(self, frame, pid, flags, info):
        super(PacketEvent, self).__init__(frame, pid, flags)
        self.info = info

@loggable
class PingEvent(MessageEvent):
    name = 'PingEvent'

    def __init__(self, frame, pid, flags, x, y):
        super(PingEvent, self).__init__(frame, pid, flags)
        self.x, self.y = x, y
