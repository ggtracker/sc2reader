# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from collections import defaultdict
from sc2reader.constants import LOTV_SPEEDUP, GAME_SECONDS_PER_SECOND


class APMTracker(object):
    """
    Builds ``player.aps`` and ``player.apm`` dictionaries where an action is
    any Selection, Hotkey, or Ability event.

    Also provides ``player.avg_apm`` which is defined as the sum of all the
    above actions divided by the number of seconds played by the player (not
    necessarily the whole game) multiplied by 60.

    APM is 0 for games under 1 minute in length.
    """
    name = 'APMTracker'

    def handleInitGame(self, event, replay):
        for human in replay.humans:
            human.apm = defaultdict(int)
            human.aps = defaultdict(int)
            human.seconds_played = replay.length.seconds

    def handlePlayerActionEvent(self, event, replay):
        speed_multiplier = 1
        if replay.expansion == 'LotV':
            speed_multiplier = LOTV_SPEEDUP

        game_seconds_per_second = GAME_SECONDS_PER_SECOND[replay.expansion]

        game_second = int(event.second/speed_multiplier)
        event.player.aps[game_second] += game_seconds_per_second
        event.player.apm[int(game_second/60)] += game_seconds_per_second

    def handlePlayerLeaveEvent(self, event, replay):
        event.player.seconds_played = event.second

    def handleEndGame(self, event, replay):
        for human in replay.humans:
            if len(human.apm.keys()) > 0:
                human.avg_apm = sum(human.aps.values())/float(human.seconds_played)*60
            else:
                human.avg_apm = 0
