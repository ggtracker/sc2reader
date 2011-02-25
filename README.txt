What is sc2reader?
-------------------

1. sc2reader is a library for extracting game information from Starcraft II
replay files into a replay object. Please join the `mailing list`_ to be
notified of updates and participate in discussion around the replay format.

2. sc2reader is also a format documentation project, documentation is always in
progress and the latest and greatest can be found on the `github wiki`.

Contributions, bugs, and suggestions are always welcome. Please direct them
to the `issue tracker`_ or the `mailing list`_ as appropriate.

*Special thanks to the people of the awesome `phpsc2replay` project whose
public documentation and source code made this library possible.*

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
 
See the sc2replay `wiki`_ for additional usage details (coming soon).

Current Status
---------------

sc2reader is written to parse replays where ``buidl >= 16561`` (generally
version 1.1 replays). This means that the following information can be
extracted:

- Replay details (map, length, version, game type, game speed, ...)
- Player details (name, race, team, color, ...)
- Message details (text, time, player, target, ...)
- Game details (winners, losers, unit abilities,unit selections, ...)

Support for version 1.2 replays has been added and appears to work correctly
on all replays tested. 1.0 support has been added by implementing methods from
the `phpsc2replay`_ project but is completely untested as I don't have any 1.0
replays to test with right now (I'll find some soon).

Installation
-------------

Requirements
~~~~~~~~~~~~~

- Python 2.6+, Python 3.0 untested
- The `mpyq`_ MPQ exraction library
- `pytest`_ testing library (optional)

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
	
Contributors
~~~~~~~~~~~~~

  $ easy_install pytest

In order to run the tests, you need to be in the root directory of sc2reader.
To run the tests:

  $ py.test

Issues and Support
-------------------

Until some further infrastructure is set up:

- Refer to the `wiki`_ for replay format documentation
- Visit `issue tracker`_ to report bugs and request features
- Join the `mailing list`_ to request support and contribute to the effort


.. _mailing list: http://groups.google.com/group/sc2reader
.. _mpyq: http://pypi.python.org/pypi/mpyq
.. _wiki: https://github.com/GraylinKim/sc2reader/wiki
.. _phpsc2replay: http://code.google.com/p/phpsc2replay/
.. _pytest: http://pytest.org/
.. _issue tracker: https://github.com/GraylinKim/sc2reader/issues