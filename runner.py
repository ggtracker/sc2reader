from objects.replay import Replay
from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

replay = Replay(r'C:\Users\graylinkim\Documents\StarCraft II\Accounts\55711209\1-S2-1-2358439\Replays\Unsaved\Arid Wastes.SC2Replay')

for player in replay.players[1:]:
	print "%s: %s" % (player,player.result)