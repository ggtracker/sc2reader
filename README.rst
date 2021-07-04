.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4007376.svg
   :target: https://doi.org/10.5281/zenodo.4007376

What is sc2reader?
====================

sc2reader is a python library for extracting information from various different Starcraft II resources. These resources currently include Replays, Maps, and Game Summaries; we have plans to add support for Battle.net profiles and would gladly accept adapters to the more entrenched SCII sites such as sc2ranks.

There is a pressing need in the SC2 community for better statistics, better analytics, better tools for organizing and searching replays. Better websites for sharing replays and hosting tournaments. These tools can't be created without first being able to open up Starcraft II game files and analyze the data within. Our goal is to give anyone and everyone the power to construct their own tools, do their own analysis, and hack on their own Starcraft II projects under the open MIT license.


Who Uses sc2reader?
======================

sc2reader is currently powering:

* Websites: `gggreplays.com`_, `gamereplays.org`_, `spawningtool.com`_
* Tools: `The Core`_
* Experiments: `Midi Conversion`_

If you use sc2reader and you would like your tool, site, project, or implementation listed above, drop us a line on our `mailing list`_.


.. _gggreplays.com: http://gggreplays.com
.. _gamereplays.org: http://www.gamereplays.org/starcraft2/
.. _spawningtool.com: https://lotv.spawningtool.com
.. _The Core: http://www.teamliquid.net/forum/viewmessage.php?topic_id=341878
.. _Midi Conversion: https://github.com/obohrer/sc2midi


Current Status
=================

sc2reader is production ready at release and under active development on Github. It is currently capable of parsing varying levels of information out of the three primary resource types listed below. For a more detailed and exact description of the information that can be extracted please consult the `documentation`_ hosted on ReadTheDocs.

.. _documentation: http://sc2reader.rtfd.org/


Replays
-------------

Replays can be parsed for the following general types of information:

- Replay details (map, length, version, expansion, datetime, game type/speed, ...)
- Player details (name, race, team, color, bnet url, win/loss, ...)
- Message details (text, time, player, target, pings, ...)
- Unit Selection and Hotkey (Control Group) events.
- Resource Transfers and Requests (but not collection rate or unspent totals!)
- Unfiltered Unit commands (attack, move, train, build, psi storm, etc)
- Camera Movements for all players and observers.

Replays from release 2.0.8 onward make additional state information available:

- Unit states - creation time, positions, and deaths times
- Player resource stats - collection rates/unspent totals
- Player spending stats - resources spent and lost

Further game state information can be extracted from this raw information:

- All unit selections and hotkey values for every frame of the game.
- APM/EPM and its untold variations.
- Supply counts, expansion timings, build orders, etc

We have data dictionaries in place for standard games that make unit meta data
available.  Unit meta data is currently limited to:

- Costs - mineral, vespene, supply
- Classification - army, building, worker

Additionally, abilities that create units/buildings have the built unit linked
with the build time in game seconds.

Unfortunately this information IS NOT currently versioned and is only accurate
for the latest builds of Starcraft. Versioned meta data support will be added
in future releases.


Maps
-------

Maps can be parsed for the following information:

* Minimap and Icon images (tga format)
* enUS localized Name, Author, Description, Website (if available)
* Map Dimensions, Camera Bounds, Tileset
* Player Slot data and Advanced Teams alliance/enemy data.

There is a lot more in here to be had for the adventurous.


Game Summaries
-----------------

Game Summary files are downloaded by the client in order to allow you to view the game summary from your match history. Prior to 2.0.8 they were the only way to get the information from the summary screen. Since the 2.0.8 release you have been able to compute this information yourself from the replay files.

Thank you Prillan and `Team Liquid`_ for helping to decode this file.

* Lobby Properties (game speed, game type, ...)
* Player Information (Race, Team, Result, bnet info, ...)
* Player Graphs & Stats (Army Graph, Income Graph, Avg Unspent Resources, ...)
* URLs to map localization files and images
* Player build orders up to 64 (real) actions

Parsing on these files is now production ready for those that can get them. See the `Team Liquid`_ thread for details on how to go about getting them.

Again, these files are generally unnecessary after the 2.0.8 release.

.. _Team Liquid: http://www.teamliquid.net/forum/viewmessage.php?topic_id=330926


Basic Usage
=====================

..note::

    For example scripts, checkout the docs and the `sc2reader.scripts`_ package on Github or in the source.


Loading Replays
-------------------
For many users, the most basic commands will handle all of their needs::

    import sc2reader
    replay = sc2reader.load_replay('MyReplay', load_map=true)

This will load all replay data and fix GameHeart games. In some cases, you don't need the full extent of the replay data. You can use the load level option to limit replay loading and improve load times::

    # Release version and game length info. Nothing else
    sc2reader.load_replay('MyReplay.SC2Replay', load_level=0)

    # Also loads game details: map, speed, time played, etc
    sc2reader.load_replay('MyReplay.SC2Replay', load_level=1)

    # Also loads players and chat events:
    sc2reader.load_replay('MyReplay.SC2Replay', load_level=2)

    # Also loads tracker events:
    sc2reader.load_replay('MyReplay.SC2Replay', load_level=3)

    # Also loads game events:
    sc2reader.load_replay('MyReplay.SC2Replay', load_level=4)

If you want to load a collection of replays, you can use the plural form. Loading resources in this way returns a replay generator::

    replays = sc2reader.load_replays('path/to/replay/directory')

.. _sc2reader.scripts: https://github.com/ggtracker/sc2reader/tree/upstream/sc2reader/scripts


Loading Maps
----------------

If you have a replay and want the map file as well, sc2reader can download the corresponding map file and load it in one of two ways::

    replay = sc2reader.load_replay('MyReplay.SC2Replay', load_map=true)
    replay.load_map()

If you are looking to only handle maps you can use the map specific load methods::

    map = sc2reader.load_map('MyMap.SC2Map')
    map = sc2reader.load_maps('path/to/maps/directory')


Using the Cache
---------------------

If you are loading a lot of remote resources, you'll want to enable caching for sc2reader. Caching can be configured with the following environment variables:

* SC2READER_CACHE_DIR - Enables caching to file at the specified directory.
* SC2READER_CACHE_MAX_SIZE - Enables memory caching of resources with a maximum number of entries; not based on memory imprint!

You can set these from inside your script with the following code **BEFORE** importing the sc2reader module::

    os.environ['SC2READER_CACHE_DIR'] = "path/to/local/cache"
    os.environ['SC2READER_CACHE_MAX_SIZE'] = 100

    # if you have imported sc2reader anywhere already this won't work
    import sc2reader


Using Plugins
------------------

There are a growing number of community generated plugins that you can take advantage of in your project. See the article on `Creating GameEngine Plugins`_ for details on creating your own. To use these plugins you need to customize the game engine::

    from sc2reader.engine.plugins import SelectionTracker, APMTracker
    sc2reader.engine.register_plugin(SelectionTracker())
    sc2reader.engine.register_plugin(APMTracker())

The new GameHeartNormalizerplugin is registered by default.

.. _Creating GameEngine Plugins: http://sc2reader.readthedocs.org/en/latest/articles/creatingagameengineplugin.html


Installation
================

sc2reader runs on any system with Python 2.6+, 3.2+, or PyPy installed.


From PyPI (stable)
---------------------

Install from the latest release on PyPI with pip::

    pip install sc2reader

or easy_install::

    easy_install sc2reader

or with setuptools (specify a valid x.x.x)::

    wget http://pypi.python.org/packages/source/s/sc2reader/sc2reader-x.x.x.tar.gz
    tar -xzf sc2reader-x.x.x.tar.gz
    cd sc2reader-x.x.x
    python setup.py install

Releases to PyPi can be very delayed (sorry!), for the latest and greatest you are encouraged to install from Github upstream.


From Github
--------------------------

Github upstream is generally stable with development branches more unstable.

We use `circle-ci`_ to provide a record of our `continuous testing`_. Please verify that tests are passing before installing development versions.

Install from the latest source on Github with pip::

    pip install -e git+git://github.com/ggtracker/sc2reader#egg=sc2reader

or with setuptools::

    wget -O sc2reader-upstream.tar.gz https://github.com/ggtracker/sc2reader/tarball/upstream
    tar -xzf sc2reader-upstream.tar.gz
    cd sc2reader-upstream
    python setup.py install

.. _circle-ci: https://circleci.com/
.. _coveralls.io: https://coveralls.io
.. _test coverage: https://coveralls.io/r/GraylinKim/sc2reader
.. _continuous testing: https://circleci.com/gh/ggtracker/sc2reader


For Contributors
-------------------

Contributors should install from an active git repository using setuptools in `develop`_ mode. This will install links to the live code so that local edits are available to external modules automatically::

    git clone https://github.com/ggtracker/sc2reader.git
    cd sc2reader
    python setup.py develop

Please review the `CONTRIBUTING.md`_ file and get in touch with us before doing too much work. It'll make everyone happier in the long run.

.. _develop: http://peak.telecommunity.com/DevCenter/setuptools#development-mode
.. _CONTRIBUTING.md: https://github.com/ggtracker/sc2reader/blob/upstream/CONTRIBUTING.md


Testing
-------------------

We use ``pytest`` for testing. If you don't have it just ``pip install pytest``.

To run the tests, just do::

    pytest


When repeatedly running tests it can be very helpful to make sure you've set a local cache directory to prevent long fetch times from battle.net.
So make some local cache folder::

    mkdir cache

And then run the tests like this::

    SC2READER_CACHE_DIR=./cache pytest

To run just one test:

    SC2READER_CACHE_DIR=./cache pytest test_replays/test_replays.py::TestReplays::test_38749

If you'd like to see which are the 10 slowest tests (to find performance issues maybe)::

    pytest --durations=10

If you want ``pytest`` to stop after the first failing test::

    pytest -x


Have a look at the very fine ``pytest`` docs for more information.

Good luck, have fun!


Community
==============

sc2reader has a small but growing community of people looking to make tools and websites with Starcraft II data. If that sounds like something you'd like to be a part of please join our underused `mailing list`_ and start a conversation or stop by #sc2reader on FreeNode and say 'Hi'. We have members from all over Europe, Australia, and the United States currently, so regardless of the time, you can probably find someone to talk to.


Issues and Support
=====================

We have an `issue tracker`_ on Github that all bug reports and feature requests should be directed to. We have a `mailing list`_ with Google Groups that you can use to reach out for support. We are generally on FreeNode in the #sc2reader and can generally provide live support and address issues there as well.

.. _mailing list: http://groups.google.com/group/sc2reader
.. _issue tracker: https://github.com/ggtracker/sc2reader/issues


Acknowledgements
=======================

Thanks to all the awesome developers in the SC2 community that helped out
and kept this project going.

* Special thanks to the people of the awesome (but abandoned!) `phpsc2replay`_
  project whose public documentation and source code made starting this library
  possible.
* Thanks to `sc2replay-csharp`_ for setting us straight on game events parsing
  and assisting with our v1.5 upgrade.
* Thanks to `ggtracker.com`_ for sponsoring further development and providing
  the thousands of test files used while adding s2gs and HotS support.
* Thanks to Blizzard for supporting development of 3rd party tools and releasing
  their `s2protocol`_ full reference implementation.


.. _ggtracker.com: http://ggtracker.com
.. _phpsc2replay: http://code.google.com/p/phpsc2replay/
.. _sc2replay-csharp: https://github.com/ascendedguard/sc2replay-csharp
.. _s2protocol: https://github.com/Blizzard/s2protocol

