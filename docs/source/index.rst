SC2Reader User Manual
=========================

There is a pressing need in the SC2 community for better statistics, better
analytics, better tools for organizing and searching replays. Better websites
for sharing replays and hosting tournaments. These tools can't be created with
out first being able to open up replay files and analyze the content within.
That's why **sc2reader** was built, to provide a solid foundation on which the next
generation of tools and websites can be built and benefit the community.

So lets get you started right away! Through the linked tutorials and reference
pages below we'll get you started building your own tools and systems in no
time. Any questions, suggestions, or concerns should be posted to the sc2reader
`mailing list`_. You can also pop on to our #sc2reader, our `IRC channel`_ on
Freenode if you want to chat or need some live support.

.. note::

    Checkout our :doc:`faq`. If your question isn't covered there, let us know and we'll add it to the list.

.. _mailing list: http://groups.google.com/group/sc2reader
.. _IRC Channel: http://webchat.freenode.net/?channels=#sc2reader


About sc2reader
--------------------

**sc2reader** is an open source, MIT licensed, python library for extracting game play information from Starcraft II replay and map files. It is production ready, actively maintained, and hosted publicly on Github [`source`_].

Features:

* Fully parses and extracts all available data from all replay files (arcade included) from every official release (plus the HotS Beta).
* Automatically retrieves maps; extracts basic map data and images. Maps unit type and ability link ids to unit/ability game data.
* Processes replay data into an interlinked set of Team, Player, and Unit objects for easy data manipulation

Plugins:

* Selection Tracking: See every player's current selection and hotkeys at every frame of the game.
* APM Tracking: Provides basic APM information for each player by minute and as game averages.
* GameHeartNormalizer: Fixes teams, races, times, and other oddities typical of GameHeart games.

Scripts:

* sc2printer: Print basic replay information to the terminal.
* sc2json: Render basic replay information to json for use in other languages.
* sc2replayer: Play back a replay one event at a time with detailed printouts.

I am actively looking for community members to assist in documenting the replay data and in creating plugins that enhance functionality. `Contact me`_!

.. _source: http://github.com/GraylinKim/sc2reader
.. _Contact me: mailto://sc2reader@googlegroups.com

Getting Started
--------------------

I recommend the following steps when getting started:

* Follow the `installation guide`_
* Read this article on replays: :doc:`articles/whatsinareplay` (5 minutes).
* Read this article on sc2reader: :doc:`articles/conceptsinsc2reader` (5 minutes).
* Short introduction to sc2reader: :doc:`articles/gettingstarted` (5 minutes)

Now that you've been oriented, you can see sc2reader in action by working through a couple of the tutorials below.

.. _installation guide: https://github.com/GraylinKim/sc2reader#installation


Tutorials
---------------

The best way to pick sc2reader up and get started is probably by example. With that in mind, we've written up a series of tutorials on getting various simple tasks done with sc2reader; hopefully they can serve as a quick on ramp for you.

* :doc:`tutorials/prettyprinter` (10-15 minutes)


Articles
----------------

A collection of short handwritten articles about aspects of working with replays and sc2reader.

* :doc:`articles/whatsinareplay` (5 minutes).
* :doc:`articles/gettingstarted` (5 minutes).
* :doc:`articles/conceptsinsc2reader` (5 minutes).
* :doc:`articles/creatingagameengineplugin` (10 minutes).


Reference Pages
-----------------------

Don't forget to check the :doc:`faq` if you can't find the answer you are looking for!

.. toctree::

    sc2reader
    mainobjects
    supportobjects
    dataobjects
    plugins
    factories
    decoders
    utilities
    events/index



.. toctree::
    :hidden:
    :maxdepth: 2
    :glob:

    faq
    sc2reader
    mainobjects
    supportobjects
    dataobjects
    plugins
    factories
    decoders
    utilities
    articles/*
    tutorials/*
    events/index
