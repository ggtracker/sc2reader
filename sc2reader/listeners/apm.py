from __future__ import absolute_import

from sc2reader.events import GameEvent
from sc2reader.listeners.utils import ListenerBase

from collections import defaultdict

class APMTracker(ListenerBase):

    def setup(self, replay):
        for player in replay.players:
            player.aps = defaultdict(int)
            player.apm = defaultdict(int)
            player.avg_apm = 0

    def accepts(self, event):
        return isinstance(sc2reader.events.GameEvent) and event.is_local and event.is_player_action

    def __call__(self, event, replay):
        player = event.player
        if not player.is_observer:
            # Count up the APS, APM
            minute =  event.second/60.0
            player.aps[event.second] += 1
            player.apm[int(minute)] += 1

    def finish(self, replay):
        for player in replay.players:
            player.avg_apm = sum(player.apm.values())/len(player.apm.keys())
