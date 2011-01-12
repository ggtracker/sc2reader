What is sc2reader?
-------------------

sc2reader is a library for extracting game information from Starcraft II
replay files into a replay object. It is based heavily on documentation
from the awesome `phpsc2replay`_ project. 

Example Usage
--------------

::

	>>> replay = Replay(filename)
	>>> print "\n%s on %s played on %s" % (replay.type,replay.map,replay.date)
	>>>
	>>> #Player[0] is None so that players can be indexed by ID
	>>> for team,players in replay.teams.iteritems():
	>>>		print "\n\tTeam %s: %s" % (team,replay.results[team])
	>>>		for player in players:
	>>>			print "\t\t%s" % player
	
	2v2 on Zwietracht IV played on Mon Dec 27 22:51:59 2010
		
		Team 1: Won
			Player 1 - Pille (Zerg)
			Player 2 - Mort (Zerg)
			
		Team 2: Lost
			Player 3 - HaRib0 (Protoss)
			Player 4 - neosmatrix (Zerg)

The same results can be found using the sc2printer utility script which simply
wraps up the above code as a (simple) demonstration of the libraries utility::

    $ sc2printer game1.sc2replay game2.sc2replay
 
See the sc2replay `wiki`_ for additional usage details. 

Current Status
---------------

sc2reader is written to parse replays where build ``version >= 16561``. This means
that the following information can be extracted:

- Replay details (map, length, version, game type, game speed, ...)
- Player details (name, race, team, color, ...)
- Message details (text, time, player, target, ...)
- Game details (winners, losers, unit abilities,unit selections, ...)

For ``version < 16561``: replay, player, and message details can still be
extracted because their formats do not seem to have changed as far as testing
shows.

Support for older builds may be patched in future releases as development is
on going.

Installation
-------------

Requirements
~~~~~~~~~~~~~

- Python 2.6+, Python 3.0 untested
- The `mpyq`_ MPQ exraction library

Basic Install
~~~~~~~~~~~~~~

::

	$ easy_install sc2reader
	$ sc2printer 'path/to/replay.sc2replay'
	
Advanced Install
~~~~~~~~~~~~~~~~~

::

	$ git clone https://github.com/GraylinKim/sc2reader.git
	$ cd sc2reader
	$ python setup.py install
	$ sc2printer 'path/to/replay.sc2replay'

Issues and Support
-------------------

Until some further infrastructure is set up:

- Please refer to the `wiki`_ for documentation
- Visit `issue tracker`_ to report bugs and request features
- `email me`_ for technical support issues.


.. _email me: mailto:graylin.kim@gmail.com
.. _mpyq: http://pypi.python.org/pypi/mpyq
.. _wiki: https://github.com/GraylinKim/sc2reader/wiki
.. _phpsc2replay: http://code.google.com/p/phpsc2replay/
.. _issue tracker: https://github.com/GraylinKim/sc2reader/issues