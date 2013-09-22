# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from sc2reader.events.base import Event
from sc2reader.utils import Length
from sc2reader.log_utils import loggable


@loggable
class MessageEvent(Event):
    name = 'MessageEvent'

    def __init__(self, frame, pid):
        self.pid = pid
        self.frame = frame
        self.second = frame >> 4

    def _str_prefix(self):
        player_name = self.player.name if getattr(self, 'pid', 16) != 16 else "Global"
        return "%s\t%-15s " % (Length(seconds=int(self.frame/16)), player_name)

    def __str__(self):
        return self._str_prefix() + self.name


@loggable
class ChatEvent(MessageEvent):
    name = 'ChatEvent'

    def __init__(self, frame, pid, target, text):
        super(ChatEvent, self).__init__(frame, pid)
        self.target = target
        self.text = text
        self.to_all = (self.target == 0)
        self.to_allies = (self.target == 2)
        self.to_observers = (self.target == 4)


@loggable
class PacketEvent(MessageEvent):
    name = 'PacketEvent'

    def __init__(self, frame, pid, info):
        super(PacketEvent, self).__init__(frame, pid)
        self.info = info


@loggable
class PingEvent(MessageEvent):
    name = 'PingEvent'

    def __init__(self, frame, pid, target, x, y):
        super(PingEvent, self).__init__(frame, pid)

        #: The numerical target type. 0 = to all; 2 = to allies; 4 = to observers.
        self.target = target

        #: Flag marked true of message was to all.
        self.to_all = (self.target == 0)

        #: Flag marked true of message was to allies.
        self.to_allies = (self.target == 2)

        #: Flag marked true of message was to observers.
        self.to_observers = (self.target == 4)

        #: The x coordinate of the target location
        self.x = x

        #: The y coordinate of the target location
        self.y = y

        #: The (x,y) coordinate of the target location
        self.location = (self.x, self.y)
