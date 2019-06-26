import logging
import requests

logging.basicConfig(level=logging.DEBUG)

urls = [
    "http://XX.depot.battle.net:1119/6de41503baccd05656360b6f027db88169fa1989bb6357b1b215a2547939f5fb.s2ma",
    "http://XX.depot.battle.net:1119/421c8aa0f3619b652d23a2735dfee812ab644228235e7a797edecfe8b67da30e.s2ma",
    "http://XX.depot.battle.net:1119/66093832128453efffbb787c80b7d3eec1ad81bde55c83c930dea79c4e505a04.s2ma",
    "http://XX.depot.battle.net:1119/d92dfc48c484c59154270b924ad7d57484f2ab9a47621c7ab16431bf66c53b40.s2ma",
    "http://XX.depot.battle.net:1119/b257a59cfb6d7ff5e596cba41c8b0e6669de29bbe2ce9623472d97a5bf9be5fd.s2ma",
    "http://XX.depot.battle.net:1119/7f41411aa597f4b46440d42a563348bf53822d2a68112f0104f9b891f6f05ae1.s2ma",
    "http://XX.depot.battle.net:1119/252f74a08b05cc250f24b5ca7f88071519c1588c82925561dd8dd51256e7e2ed.s2ma",
]

for url in urls:
    try:
        requests.get(url)
    except Exception as e:
        logging.exception(e)
