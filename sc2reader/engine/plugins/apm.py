from collections import Counter

class APMTracker(object):

    def handleInitGame(self, event, replay):
        for player in replay.players:
            player.apm = Counter()
            player.aps = Counter()
            player.seconds_played = replay.length.seconds

    def handlePlayerActionEvent(self, event, replay):
        event.player.aps[event.second] += 1
        event.player.apm[event.second/60] += 1

    def handlePlayerLeaveEvent(self, event, replay):
        event.player.seconds_played = event.second

    def handleEndGame(self, event, replay):
        print "Handling End Game"
        for player in replay.players:
            if len(player.apm.keys()) > 0:
                player.avg_apm = sum(player.apm.values())/float(player.seconds_played)*60
            else:
                player.avg_apm = 0
