What is sc2reader?
====================

sc2reader is a library for extracting game information from Starcraft II
replay files into a structured replay object. sc2reader aims to give anyone
and everyone the power to construct their own tools and hack on their own
Starcraft II projects under the open MIT license.



Supports Python 2.6+, Python 3 isn't tested but probably won't work. If you want
to make it work, drop a proposal on the `mailing list`_. Python 3.0 support
would be awesome.

Special thanks to the people of the awesome `phpsc2replay`_ project whose
public documentation and source code made starting this library possible.


Current Status
=================

sc2reader can parse basic replay information out of all official releases of
Starcraft II from 1.1.0 to 1.4.1. This means that the following information can
be extracted:

- Replay details (map, length, version, date, game type, game speed, ...)
- Player details (name, race, team, color, bnet url, ...)
- Message details (text, time, player, target, ...)
- Game details (winners, losers, unit abilities, unit selections, hotkeys, ...)

Unfortunately, the area around game details is still very rough. Most of the
available builds do not map the parsed ability codes to the corresponding unit
ability which really limits its usability for anything beyond apm type
calculations. Filling out the ability codes mapping is the primary task right now
and hopefully improve support can be added in the near future.

1.0.x is also supported via code more or less copied from the `phpsc2replay`_
project. While it appears to work, there are no guarantees and getting support
for any issues will probably be difficult. If you have 1.0.x replays laying
around it would be great if you could post them to the mailing list for testing
purposes. We would require permission to upload and distribute them through our
Github repository.


Examples
===================

The example below demonstrates some of the most basic usage. For more detailed
examples consult the official `documentation`_.

::

    >>> import sc2reader
    >>> r = sc2reader.read_file('test_replays/1.4.0.19679/36663.SC2Replay')
    >>> print "Duration: {0} on {1}, played {2} ".format(r.length, r.map, r.date)
    Duration: 10.59 on Xel'Naga Caverns, played 2011-09-21 02:49:47
    >>> for player in r.players:
    ...     print "[{0}] {1}, {2} APM".format(player.result,player,player.avg_apm)
    ...
    [Win] Player 1 - MaNNErCHOMP (Terran), 148.13353566 APM
    [Loss] Player 2 - vVvHasuu (Protoss), 143.525835866 APM
    >>> r.player[1].result
    'Win'
    >>> r.player['vVvHasuu'].url
    'http://us.battle.net/sc2/en/profile/493391/1/vVvHasuu/'


For web services, dumping to json might be a common operation.

::

    >>> import sc2reader;
    >>> from sc2reader.processors import jsonEncoder
    >>> print sc2reader.read_file(
    ...     'test_replays/1.4.0.19679/36663.SC2Replay',
    ...     processors=[jsonEncoder(indent=4)]
    ... )
    {
        "category": "Ladder",
        "map": "Xel'Naga Caverns",
        "players": [
            {
                "uid": 934659,
                "play_race": "Terran",
                "color": {
                    "a": 255,
                    "r": 180,
                    "b": 30,
                    "g": 20
                },
                "pick_race": "Terran",
                "pid": 1,
                "result": "Win",
                "name": "MaNNErCHOMP",
                "url": "http://us.battle.net/sc2/en/profile/934659/1/MaNNErCHOMP/",
                "messages": [
                    {
                        "text": "lol",
                        "is_public": true,
                        "time": 9
                    },
                    {
                        "text": "sup bra",
                        "is_public": true,
                        "time": 23
                    },
                    {
                        "text": ":(",
                        "is_public": true,
                        "time": 48
                    }
                ],
                "type": "Human",
                "avg_apm": 148.13353566009107
            },
            {
                "uid": 493391,
                "play_race": "Protoss",
                "color": {
                    "a": 255,
                    "r": 0,
                    "b": 255,
                    "g": 66
                },
                "pick_race": "Protoss",
                "pid": 2,
                "result": "Loss",
                "name": "vVvHasuu",
                "url": "http://us.battle.net/sc2/en/profile/493391/1/vVvHasuu/",
                "messages": [],
                "type": "Human",
                "avg_apm": 143.52583586626139
            }
        ],
        "type": "1v1",
        "is_ladder": true,
        "utc_date": "2011-09-21 06:49:47",
        "file_time": 129610613871027307,
        "observers": [],
        "frames": 10552,
        "build": 19679,
        "date": "2011-09-21 02:49:47",
        "unix_timestamp": 1316587787,
        "filename": "test_replays/1.4.0.19679/36663.SC2Replay",
        "speed": "Faster",
        "gateway": "us",
        "is_private": false,
        "release": "1.4.0.19679"
    }

Seriously, consult the `documentation`_! Its for your own good.


Example Scripts
====================

A couple simple scripts have been included in the sc2reader package to get you
started and provide an example. While potentially useful on their own they are
primarily there to demonstrate what can be done. As such, there are no
guarantees that these scripts will be maintained or continue operating in the
same way.

Please modify them to your liking or create your own as necessary. If you are
proud of your changes or would like to have your script distributed  let the
`mailing list`_ know. Generally speaking, we'd be happy to distribute more
useful example scripts and utilities.

sc2printer
--------------

The sc2printer script packaged with sc2reader provides a configurable printout
of several key aspects of the replay(s) that its pointed at:

::

    graylin@graylin-laptop:/home/sc2reader$ sc2printer test_replays/1.4.0.19679/36663.SC2Replay --messages --date --map --length --teams

    --------------------------------------
    test_replays/1.4.0.19679/36663.SC2Replay

       Map:      Xel'Naga Caverns
       Length:   10.59
       Date:     2011-09-21 02:49:47
       Teams:    TvP
          Team 1	MaNNErCHOMP (T)
          Team 2	vVvHasuu (P)
       Messages:
          00.09 - MaNNErCHOMP    - lol
          00.23 - MaNNErCHOMP    - sup bra
          00.48 - MaNNErCHOMP    - :(
       Version:  1.4.0.19679


sc2autosave
------------------

sc2autosave is a utility script that you could run in cycle mode in the
background or hook up to a cron job in batch mode to autosave your replay files
with configurable naming conventions into a structured file hierarchy.

Its got a lot of options, so make sure to use the ``--help`` command before you
get started.

::

    graylin@graylin-laptop:/home/sc2reader$ sc2autosave test_replays test_autosave --mode BATCH --action COPY --exclude-dirs problem_replays mine
    Loading state from file: test_autosave/sc2autosave.dat
    SCANNING: test_replays
    COPY:
	    Source: /149414-nSkENNY-VS-aflubin.sc2replay
	    Dest: /18.12 1v1 on Abyssal Caverns.SC2Replay
    COPY:
	    Source: /1.2.1.17682/VTPokebunny_vs_LuckyFool_5768.SC2Replay
	    Dest: /16.48 1v1 on Shakuras Plateau.SC2Replay
    COPY:
	    Source: /1.2.1.17682/Froadac_vs_BattleOtter_6040.SC2Replay
	    Dest: /20.20 1v1 on Lost Temple.SC2Replay
    COPY:
	    Source: /1.2.1.17682/2v2_Scorched Haven_6473.SC2Replay
	    Dest: /27.14 2v2 on Scorched Haven.SC2Replay
    COPY:
	    Source: /1.2.1.17682/Laegoose_vs_nitrousx_4626.SC2Replay
	    Dest: /21.04 1v1 on Мусоросборник.SC2Replay
    COPY:
	    Source: /1.2.1.17682/Deadiam_vs_McSwagger_6474.SC2Replay
	    Dest: /19.22 1v1 on Steppes of War.SC2Replay
    COPY:
	    Source: /1.2.1.17682/1v1_Lost Temple_3969.SC2Replay
	    Dest: /16.46 1v1 on Lost Temple.SC2Replay
    COPY:
	    Source: /1.2.1.17682/BowmanSX_vs_nubington_8614.SC2Replay
	    Dest: /22.04 1v1 on Metalopolis.SC2Replay
    COPY:
	    Source: /1.2.1.17682/Sharky_vs_trolli_4792.SC2Replay
	    Dest: /09.04 1v1 on Blistering Sands.SC2Replay

    .... #There are hundreds of test replays...


sc2store
-------------

sc2store is a really cool idea that I probably won't get around to finishing. It
uses sqlAlchemy to stuff the target replays into a target SQL database. The
models could definitely use some work and there might be a couple bugs to shake
out but it demonstrates a pretty solid approach to working with sc2reader from
other languages. Drop.sc used a script similar to this for a long time to work
with sc2reader from his Ruby on Rails web application.

If you don't specify a storage string it just uses sqlite in memory.

::

    graylin@graylin-laptop:/home/sc2reader$ sc2store test_replays/mine
    #LOTS OF SQLAlchemy output...
    2011-10-02 14:28:11,892 INFO sqlalchemy.engine.base.Engine SELECT DISTINCT person.name AS anon_1
    FROM person
    2011-10-02 14:28:11,892 INFO sqlalchemy.engine.base.Engine ()
    [(u'AMartinez',), (u'Adelscott',), (u'AintNoThang',), (u'Amanda',),
     (u'Blue',), (u'BurnemDown',), (u'ByTheNumbers',), (u'CDUB',), (u'CuP',),
     (u'Davidal',), (u'DrMandrake',), (u'Ender',), (u'ExAn',), (u'FalconPunch',),
     (u'Fertile',), (u'Geph',), (u'HaRibO',), (u'HaZeN',), (u'HarshCougar',),
     (u'HeLeCoPtEr',), (u'Jakrom',), (u'James',), (u'Jeff',), (u'Kamron',),
     (u'Kevin',), (u'Manny',), (u'Merveilles',), (u'Mort',), (u'NELLYSON',),
     (u'NerdHerder',), (u'Onjai',), (u'OrangeBottle',), (u'PandaFeather',),
     (u'PatsyCake',), (u'Peonz',), (u'Pille',), (u'Reaganomics',), (u'Red',),
     (u'Remedy',), (u'Saladrael',), (u'ShadesofGray',), (u'SourDiesel',),
     (u'TAG',), (u'TheBoss',), (u'ThisBryanFoo',), (u'TigerGosu',), (u'Tyrak',),
     (u'UniqueRubber',), (u'Violet',), (u'Wukasz',), (u'YoungPhoenix',),
     (u'ZORN',), (u'ZeroHero',), (u'agility',), (u'dante',), (u'haoster',),
     (u'marmot',), (u'mouzMaNa',), (u'neosmatrix',), (u'oobugoo',),
     (u'reddawn',), (u'rostin',), (u'rubbernutzz',), (u'wildcard',), (u'yenoMenO',)]


Installation
================

Okay, I've convinced you to give sc2reader a shot. Next you need to install it.
If you are on windows you can cheat and just run the .exe download at the bottom
of this page.

If you are on sane system like the rest of us you can try one of the following
magic incantations on the shell. If you are a developer and want the latest and
greatest at all times, you can skip to the advanced installation section.

::

    pip install sc2reader

If you don't have `pip`_, you should consider getting it, but I digress. You can
use easy_install instead.

::

    easy_install sc2reader

If you don't have `easy_install`_ you probably have your reasons. If you don't,
then I really think you should consider getting it. Or better yet, get `pip`_!
Never fear though, when all else fails you can still do things the old fashioned
way.

::

    wget http://pypi.python.org/packages/source/s/sc2reader/sc2reader-0.3.0.tar.gz
    tar -xzf sc2reader-0.3.0.tar.gz
    cd sc2reader-0.3.0
    python setup.py install


Advanced Installation
============================

Master is at times a bit unstable and the interface might change in (mostly)
minor ways without warning. That being said, its where all the best stuff is.
If you are going to do this install you should definitely be on the
`developers mailing list`_ and it would be great if you stopped by #sc2reader on
FreeNode.net and said Hi. We can help you get up to speed and get started.

::

	git clone https://github.com/GraylinKim/sc2reader.git
	cd sc2reader
	python setup.py install

If you intend on making local modifications it'd be better to use develop mode
instead:

::

    python setup.py develop


You can test your install to verify that things are working correctly using
`pytest`_, an automated testing solution. Just run the following from the root
folder of the sc2reader source code:

::

    pip install pytest
    py.test

If they don't all pass, something went wrong. Panic. If that doesn't work, reach
out on IRC or on our `mailing list`_ for assistance.

Community
==============

sc2reader has a small but growing community of people looking to make tools and
websites with Starcraft II replay data. If that sounds like something you'd like
to be a part of please join our underused `mailing list`_ and start a conversation
or stop by #sc2reader on FreeNode and say 'Hi'. We have members from all over
Europe, Australia, and the United States currently, so regardless of the time,
you can probably find someone to talk to.

Issues and Support
=====================

We have an `issue tracker`_ on Github that all bug reports and feature requests
should be directed to. We have a `mailing list`_ with Google Groups that you can
use to reach out for support. We are generally on FreeNode in the #sc2reader
and may be able to provide support and address issues there as well.


.. _documentation: http://sc2reader.rtfd.org/
.. _mailing list: http://groups.google.com/group/sc2reader
.. _developers mailing list: http://groups.google.com/group/sc2reader-dev
.. _phpsc2replay: http://code.google.com/p/phpsc2replay/
.. _pytest: http://pytest.org/
.. _issue tracker: https://github.com/GraylinKim/sc2reader/issues
.. _pip: http://pypi.python.org/pypi/pip
.. _easy_install: http://pypi.python.org/pypi/setuptools
