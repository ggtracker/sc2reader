Frequently Asked Questions
==============================

1. :ref:`faq1`
2. :ref:`faq2`
3. :ref:`faq3`
4. :ref:`faq4`

.. _faq1:

How do I get a list of game events (including messages)?
------------------------------------------------------------

Here is a minimal example::

	replay = sc2reader.load_replay('path/to/replay.SC2Replay')
	for event in replay.events:
	    print '{0} => {1}: {2}'.format(event.pid,event.name, event.time)

Please see the `documentation`_ for a full listing of the information available.

.. _documentation: http://sc2reader.rtfd.org

.. _faq2:

How to I get the game state at a specific time in the game. E.g. at 10:00 how many workers every player has.
---------------------------------------------------------------------------------------------------------------

This is difficult. Events are only recorded for player initiated actions and you'll find that both successful and unsuccessful actions are included. That means several things complicates our lives:

1. There is no "unit created" event. Only a "player attempted to use train <unit>" events.
2. There is no "death" event. You can only tell a unit is alive when it is actively selected.
3. Game state information: player resources, available supply, etc are unavailable at all times.

It may be possible to overcome these limitations and approximate game state with a series of very smart assumptions and cool algorithms. If you could accurately count workers though, you'd be the first I think.

.. _faq3:

How can I retrieve game summary files?
-----------------------------------------

s2gs files hashes are not contained inside any other SC2 resources as far as anyone knows.

Make sure you read the  `s2gs thread`_ for details.

Aside from manually causing s2gs files to download to your battle.net cache folder you might try set up the `S2GSExtractor`_ to scrape them from the process memory. I can't speak to its legality or effectiveness but it is somewhere to start if you want to automate things.

.. _s2gs thread: http://www.teamliquid.net/forum/viewmessage.php?topic_id=330926
.. _S2GSExtractor: https://github.com/gibybo/S2GS-Extractor

.. _faq4:

Script <name here> is broken. What is wrong?
-----------------------------------------------

It is true that not all the scripts are very well maintained. They were originally intended as mini usage examples. It seems that people are trying to use them as a primary interface for sc2reader though. I'll have to make sure they don't break going forward.

Patches to the scripts are always accepted, just issue a pull request or email me a patch file.
