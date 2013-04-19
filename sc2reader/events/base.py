# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sc2reader.log_utils import loggable

@loggable
class Event(object):
    name = 'Event'

    def __init__(self, frame, pid):
        self.pid = pid
        self.frame = frame
        self.second = frame >> 4
        # This is sorta expensive considering no one uses it
        # self.time = Length(seconds=self.second)

    def load_context(self, replay):
        if replay.versions[1]==1 or (replay.versions[1]==2 and replay.build < 24247):
            if self.pid <= len(replay.people):
                self.player = replay.person[self.pid]
            elif self.pid != 16:
                self.logger.error("Bad pid ({0}) for event {1} at {2}.".format(self.pid, self.__class__, Length(seconds=self.second)))
            else:
                pass # This is a global event

        else:
            if self.pid < len(replay.clients):
                self.player = replay.client[self.pid]
            elif self.pid != 16:
                self.logger.error("Bad pid ({0}) for event {1} at {2}.".format(self.pid, self.__class__, Length(seconds=self.second)))
            else:
                pass # This is a global event

    def _str_prefix(self):
        player_name = self.player.name if getattr(self,'pid', 16)!=16 else "Global"
        return "%s\t%-15s " % (Length(seconds=int(self.frame/16)), player_name)

    def __str__(self):
        return self._str_prefix() + self.name
