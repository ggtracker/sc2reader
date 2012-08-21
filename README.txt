What is sc2reader?
====================

sc2reader is a python library for extracting information from various different
Starcraft II resources. These resources currently include Replays, Maps, and
Game Summaries; we will eventually include BNet profiles and possibly adapters
to the more entrenched SCII sites like sc2ranks.

Our goal is to give anyone and everyone the power to construct their own
tools, do their own analysis, and hack on their own Starcraft II projects
under the open MIT license. Currently powering:

* Websites: `ggtracker.com`_
* Research: `Build Order Classification`

Our secondary goal is to become a reference implementation for people looking
to implement parsers in other languages. There are currently implementations
under development in:

* C#: `sc2replay-csharp`_ (special thanks for v1.5 help)
* C++: `sc2pp`_
* Javascript: `comsat`_
* PHP: `phpsc2replay`_ (the original open implementation!)

If you'd like your tool, site, project, or implementation listed above, drop
us a line on our mailing list or stop by our #sc2reader IRC channel and say hi!


Current Status
=================

sc2reader is currently capable of parsing varying levels of information out of
the three primary resource types listed below. For a more detailed and exact
description of the information that can be extracted please consult the
`documentation`_ hosted on Read the Docs and packaged with the source.


Replays
-------------

Almost all the basic contextual information can be extracted from any post-beta
replays. This information includes:

- Replay details (map, length, version, datetime, game type, game speed, ...)
- Player details (name, race, team, color, bnet url, win/loss, ...)
- Message details (text, time, player, target, pings, ...)

Additional information can be parsed from ladder replays and replays from basic
unmodded private "custom" games. This information includes:

- Unit Selection and Hotkey events.
- Resource Transfers and Requests (but not collection or unspent values!)
- Unfiltered Unit commands (attack, move, train, build, psi storm, etc)
- Camera Movements for all players and observers.

In some cases, further information can be extracted from this raw information:

- All unit selections and hotkey values for every frame of the game.
- APM/EPM and its untold variations.

We are in the process of building data dictionaries for all the SC2 units and
abilities which should enable much more creative and robust analysis of the
raw event stream found in replay files.


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

Tons of data parsed. Thank you Prillan and others from `Team Liquid`_.

* Lobby Properties (game speed, game type, ...)
* Player Information (Race, Team, Result, bnet info, ...)
* Player Graphs & Stats (Army Graph, Income Graph, Avg Unspent Resources, ...)
* URLs to map localization files and images
* Player build orders up to 64 (real) actions

This isn't super reliable yet and s2gs files may fail during processing. We've
figured out the basic common structure and where the information is stored but
the data structure sometimes can't be processed with current techniques and it
seems as though different s2gs files can contain radically different amounts
of information based on some unknown factors.

It is likely that s2gs file support will be improved in future releases.


Example Usage
=====================

To demonstrate how you might use sc2reader in practice I've included some short
contrived scripts below. For more elaborate examples, checkout the docs and the
sc2reader.scripts package on Github.

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
            print "Saved Map: {0} [{1}]".format(replay.map_name, replay.map_hash)


Organizing Replays
----------------------

Organizing your 1v1 replays by race played and matchup and sortable by length::

    import sc2reader, os, shutil, sys

    sorted_base = 'sorted'
    path_to_replays = 'my/replays'

    for replay in sc2reader.load_replays(sys.argv[1], load_level=1):
        if replay.real_type != '1v1':
            continue

        try:
            me = replay.player.name('ShadesofGray')
            you = team[(me.team.number+1)%2].players[0]

            matchup = "{}v{}".format(me.play_race[0], you.play_race[1])

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

Contributions can be sent via pull request or by `mailing list`_ with attached
patch files. It is highly recommended you get in touch with us before working
on patches.


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
and kept this project going. Special thanks to the people of the awesome
`phpsc2replay`_ project whose public documentation and source code made
starting this library possible and to sc2replay-csharp for setting us
straight on game events parsing and assisting with our v1.5 upgrade.

.. _Build Order Classification: https://github.com/grahamjenson/sc2reader
.. _ggtracker.com: http://ggtracker.com
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
