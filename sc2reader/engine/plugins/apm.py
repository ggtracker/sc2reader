# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from collections import defaultdict


class APMTracker(object):
    """
    Builds ``player.aps`` and ``player.apm`` dictionaries where an action is
    any Selection, ControlGroup, or Command event.

    Also provides ``player.avg_apm`` which is defined as the sum of all the
    above actions divided by the number of seconds played by the player (not
    necessarily the whole game) multiplied by 60.

    APM is 0 for games under 1 minute in length.
    """

    name = "APMTracker"

    def handleInitGame(self, event, replay):
        for human in replay.humans:
            human.apm = defaultdict(int)
            human.aps = defaultdict(int)
            human.seconds_played = replay.length.seconds

    def handleControlGroupEvent(self, event, replay):
        event.player.aps[event.second] += 1.4
        event.player.apm[int(event.second / 60)] += 1.4

    def handleSelectionEvent(self, event, replay):
        event.player.aps[event.second] += 1.4
        event.player.apm[int(event.second / 60)] += 1.4

    def handleCommandEvent(self, event, replay):
        event.player.aps[event.second] += 1.4
        event.player.apm[int(event.second / 60)] += 1.4

    def handlePlayerLeaveEvent(self, event, replay):
        event.player.seconds_played = event.second

    def handleEndGame(self, event, replay):
        for human in replay.humans:
            if len(human.apm.keys()) > 0:
                human.avg_apm = (
                    sum(human.aps.values()) / float(human.seconds_played) * 60
                )
            else:
                human.avg_apm = 0
