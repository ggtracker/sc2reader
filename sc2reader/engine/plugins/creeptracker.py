# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from collections import defaultdict
from sc2reader.engine.plugins.creeptrackerClass import creep_tracker

class CreepTracker(object):
    '''
    The Creep tracker populates player.max_creep_spread and
    player.creep_spread by minute
    This uses the creep_tracker class to calculate the features
    '''
    def handleInitGame(self, event, replay):
        try:
            replay.tracker_events
        except AttributeError:
            print("Replay does not have tracker events")
            return 
        try:
            replay.map.minimap
        except AttributeError:
            print("Map was not loaded")
            return
        self.creepTracker  = creep_tracker(replay)
        for player in replay.players:
            self.creepTracker.init_cgu_lists(player.pid)

    def handleEvent(self, event, replay):
        self.creepTracker.add_event(event)

    def handleEndGame(self, event, replay):
        for player_id in replay.player:
            self.creepTracker.reduce_cgu_per_minute(player_id)
        for player in replay.players:
            player.creep_spread_by_minute = self.creepTracker.get_creep_spread_area(player.pid)
        for player in replay.players:
            if player.creep_spread_by_minute:
                player.max_creep_spread  = max(player.creep_spread_by_minute.items(),key=lambda x:x[1])
            else:
                player.max_creep_spread  =0
