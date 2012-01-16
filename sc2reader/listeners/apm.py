from __future__ import absolute_import

from collections import defaultdict

class APMTracker(object):

    def setup(self, replay):
        for player in replay.players
            player.aps = defaultdict(int)
            player.apm = defaultdict(int)
            player.avg_apm = 0

    def __call__(self, event, replay):
        if event.is_local and event.is_player_action:
            player = event.player
            if not player.is_observer:
                # Count up the APS, APM
                minute =  event.second/60.0
                player.aps[event.second] += 1
                player.apm[int(minutes)] += 1
                player.avg_apm = sum(player.apm.values())/minutes