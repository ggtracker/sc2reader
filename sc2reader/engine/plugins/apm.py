from collections import Counter

class APMTracker(object):
    """
    Builds ``player.aps`` and ``player.apm`` dictionaries where an action is
    any Selection, Hotkey, or Ability event.

    Also provides ``player.avg_apm`` which is defined as the sum of all the
    above actions divided by the number of seconds played by the player (not
    necessarily the whole game) multiplied by 60.

    APM is 0 for games under 1 minute in length.
    """

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
                player.avg_apm = sum(player.aps.values())/float(player.seconds_played)*60
            else:
                player.avg_apm = 0
