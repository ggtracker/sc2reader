What is sc2reader?
====================

sc2reader is a python library for extracting information from various different
Starcraft II resources. These resources currently include Replays, Maps, and
Game Summaries; we may eventually include BNet profiles and possibly adapters
to the more entrenched SCII sites like sc2ranks.

Our goal is to give anyone and everyone the power to construct their own
tools, do their own analysis, and hack on their own Starcraft II projects
under the open MIT license. Currently powering:

* Websites: `ggtracker.com`_, `gamereplays.org`_
* Tools: `The Core`_
* Experiments: `Midi Conversion`_

Our secondary goal is to become a reference implementation for people looking
to implement libraries in other languages. For replays, it implements the 
replay format as specified in Blizzard's `s2protocol`_  project.

The following is a list of partial implementations in other languages:

* C#: `sc2replay-csharp`_ (special thanks for v1.5 help)
* C++: `sc2pp`_
* Javascript: `comsat`_
* PHP: `phpsc2replay`_

Unfortunately sc2reader does not implement a battle.net scraper for profile
information. If you need the information I know of two projects that can get
you started:

* Ruby: `bnet_scraper`_ - Maintained by Agora Games
* Python: `sc2profile`_ - Currently unmaintained, slightly dated.

If you'd like your tool, site, project, or implementation listed above, drop
us a line on our `mailing list`_ or stop by our #sc2reader IRC channel and say hi!


Current Status
=================

sc2reader is currently capable of parsing varying levels of information out of
the three primary resource types listed below. For a more detailed and exact
description of the information that can be extracted please consult the
`documentation`_ hosted on Read the Docs.

The library is production ready and reasonably stable.


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

Replays from release 2.0.8 on ward make additional state information available:

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

Maps are currently parsed in the most minimal way possible and are an area for
big improvement in the future. Currently the Minimap.tga packaged with the map
is made available along with Name, Author, Description for ONLY enUS localized
SCII map files. More robust Map meta data extraction will likely be added in
future releases.

There's a lot more in here to be had for the adventurous.


Game Summaries
-----------------

Game Summary files are downloaded by the client in order to allow you to view
the game summary from your match history. Prior to 2.0.8 they were the only
way to get the information from the summary screen. Since the 2.0.8 release
you have been able to compute this information yourself from the replay files.

Thank you Prillan and `Team Liquid`_ for helping to decode this file.

* Lobby Properties (game speed, game type, ...)
* Player Information (Race, Team, Result, bnet info, ...)
* Player Graphs & Stats (Army Graph, Income Graph, Avg Unspent Resources, ...)
* URLs to map localization files and images
* Player build orders up to 64 (real) actions

Parsing on these files is now production ready for those that can get them. See
the `Team Liquid`_ thread for details on how to go about getting them.

Again, these files are generally unnecessary after the 2.0.8 release.



Example Usage
=====================

To demonstrate how you might use sc2reader in practice I've included some short
contrived scripts below. For more elaborate examples, checkout the docs and the
`sc2reader.scripts`_ package on Github or in the source.


Downloading Maps
--------------------

Save all the minimaps for all the games you've ever played::

    import sc2reader, os, sys

    if not os.path.exists('minimaps'):
        os.makedirs('minimaps')

    # Only load details file (level 1) and fetch the map file from bnet
    for replay in sc2reader.load_replays(sys.argv[1:], load_map=True, load_level=1):
        minimap_path = os.path.join('minimaps', replay.map_name.replace(' ','_')+'.tga')
        if not os.path.exists(minimap_path):
            with open(minimap_path, 'w') as file_out:
                file_out.write(replay.map.minimap)
            print("Saved Map: {0} [{1}]".format(replay.map_name, replay.map_hash))


Organizing Replays
----------------------

Organizing your 1v1 replays by race played and matchup and sortable by length::

    import sc2reader, os, shutil, sys

    sorted_base = 'sorted'
    path_to_replays = 'my/replays'

    for replay in sc2reader.load_replays(sys.argv[1], load_level=2):
        if replay.real_type != '1v1':
            continue

        try:
            me = replay.player.name('ShadesofGray')
            you = team[(me.team.number+1)%2].players[0]

            matchup = "{0}v{1}".format(me.play_race[0], you.play_race[1])

            sorted_path = os.path.join(sorted_base,me.play_race[0],matchup)
            if not os.path.exists(sorted_path):
                os.makedirs(sorted_path)

            filename = "{0} - {1}".format(replay.game_length, replay.filename)
            src = os.join(path_to_replays,replay.filename)
            dst = os.join(sorted_path, filename)
            shutil.copyfile(src, dst)

        except KeyError as e:
            continue # A game I didn't play in!


Installation
================



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

Releases to PyPi can be very delayed, for the latest and greatest you are encouraged
to install from Github master which is **usually** kept quite stable.


From Github
--------------------------

Github master is generally stable with development branches more unstable.

Install from the latest source on github with pip::

    pip install -e git+git://github.com/GraylinKim/sc2reader#egg=sc2reader

or with setuptools::

    wget -O sc2reader-master.tar.gz https://github.com/GraylinKim/sc2reader/tarball/master
    tar -xzf sc2reader-master.tar.gz
    cd sc2reader-master
    python setup.py install


For Contributors
-------------------

Contributors should install from an active git repository using setuptools in
`develop`_ mode. This will install links to the live code so that local edits
are available to external modules automatically::

    git clone https://github.com/GraylinKim/sc2reader.git
    cd sc2reader
    python setup.py develop

Please review the CONTRIBUTING.md file and get in touch with us before doing
too much work. It'll make everyone happier in the long run.


Testing
-------------------

We use py.test for testing. You can install it via pip/easy_install::

    pip install pytest
    easy_install pytest

To run the tests just use::

    py.test               # Runs all the tests
    py.test test_replays  # Only run tests on replays
    py.test test_s2gs     # Only run tests on summary files

When repeatedly running tests it can be very helpful to make sure you've
set a local cache directory to prevent long fetch times from battle.net::

    export SC2READER_CACHE_DIR=local_cache
    # or
    SC2READER_CACHE_DIR=local_cache py.test

Good luck, have fun!


Community
==============

sc2reader has a small but growing community of people looking to make tools and
websites with Starcraft II data. If that sounds like something you'd like to be
a part of please join our underused `mailing list`_ and start a conversation
or stop by #sc2reader on FreeNode and say 'Hi'. We have members from all over
Europe, Australia, and the United States currently, so regardless of the time,
you can probably find someone to talk to.


Issues and Support
=====================

We have an `issue tracker`_ on Github that all bug reports and feature requests
should be directed to. We have a `mailing list`_ with Google Groups that you can
use to reach out for support. We are generally on FreeNode in the #sc2reader
and can generally provide live support and address issues there as well.


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
  their `s2protocol`_ reference implementation.


.. _s2protocol: https://github.com/Blizzard/s2protocol
.. _ggtracker.com: http://ggtracker.com
.. _gamereplays.org: http://www.gamereplays.org/starcraft2/
.. _Midi Conversion: https://github.com/obohrer/sc2midi
.. _sc2reader.scripts: https://github.com/GraylinKim/sc2reader/tree/master/sc2reader/scripts
.. _The Core: http://www.teamliquid.net/forum/viewmessage.php?topic_id=341878
.. _PyPy: http://pypy.org/
.. _sc2pp: https://github.com/zsol/sc2pp
.. _sc2replay-csharp: https://github.com/ascendedguard/sc2replay-csharp
.. _comsat: https://github.com/tec27/comsat
.. _phpsc2replay: http://code.google.com/p/phpsc2replay/
.. _Team Liquid: http://www.teamliquid.net/forum/viewmessage.php?topic_id=330926
.. _develop: http://peak.telecommunity.com/DevCenter/setuptools#development-mode
.. _documentation: http://sc2reader.rtfd.org/
.. _mailing list: http://groups.google.com/group/sc2reader
.. _developers mailing list: http://groups.google.com/group/sc2reader-dev
.. _phpsc2replay: http://code.google.com/p/phpsc2replay/
.. _issue tracker: https://github.com/GraylinKim/sc2reader/issues
.. _bnet_scraper: https://github.com/agoragames/bnet_scraper
.. _sc2profile: https://github.com/srounet/sc2profile
