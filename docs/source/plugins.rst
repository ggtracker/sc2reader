Plugins
=============

sc2reader has a built in game engine that you can plug into to efficiently process replay events. You can add plugins to the engine by calling :meth:`~sc2reader.engine.engine.GameEngine.register_plugin`::

	import sc2reader
	from sc2reader.engine.plugins import APMTracker, SelectionTracker
	sc2reader.engine.register_plugin(APMTracker())
	sc2reader.engine.register_plugin(SelectionTracker())

Plugins will be called in order of registration for each event. If plugin B depends on plugin A make sure to register plugin A first!

See the :doc:`articles/creatingagameengineplugin` article for instructions on making your own plugins.


ContextLoader
-------------

.. note::

	This plugin is registered by default.

This plugin creates and maintains all the :class:`~sc2reader.data.Unit` and :class:`~sc2reader.data.Ability` data objects from the raw replay data. This creates all the ``event.player``, ``event.unit``, ``event.ability`` object references and maintains other game data structures like :attr:`~sc2reader.resources.Replay.objects`.


GameHeartNormalizer
---------------------

.. note::

	This plugin is registered by default.

This plugin fixes player lists, teams, game lengths, and frames for games that were played with the GameHeart mod.


APMTracker
----------------

The :class:`~sc2reader.engine.plugins.APMTracker` adds three simple fields based on a straight tally of non-camera player action events such as selections, abilities, and hotkeys.

* ``player.aps`` = a dictionary of second => total actions in that second
* ``player.apm`` = a dictionary of minute => total actions in that minute
* ``player.avg_apm`` = Average APM as a float


SelectionTracker
--------------------

.. note::

	This plugin is intended to be used in conjunction with other user written plugins. If you attempt to use the ``player.selection`` attribute outside of a registered plugin the values will be the values as they were at the end of the game.

The :class:`SelectionTracker` maintains a ``person.selection`` structure maps selection buffers for that player to the player's current selection::

    active_selection = event.player.selection[10]

Where buffer is a control group 0-9 or a 10 which represents the active selection.
