What is sc2reader?
-------------------

sc2reader is a library for extracting game information from Starcraft II
replay files into a replay object. It is based heavily on documentation
from the awesome `phpsc2replay`_ project. 

Example Usage
--------------

	>>>from sc2reader import Replay
	>>>replay = Replay('path/to/replay.sc2replay')
	
	#TODO: more work to be done here
	

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
	
Advanced Install
~~~~~~~~~~~~~~~~~

::

	$ git clone https://github.com/GraylinKim/sc2reader.git
	$ cd sc2reader
	$ python setup.py install

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