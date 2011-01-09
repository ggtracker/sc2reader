from objects.replay import Replay
from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

replay = Replay(r'/home/graylin/SC2/Stats/2v2-deadghosty-girlsparts-mcdiddler-pwnzzer.sc2replay')

pprint(sorted(replay.__dict__.keys()))
