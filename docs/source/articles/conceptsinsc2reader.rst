Concepts in sc2reader
=======================

Some of the important concepts in sc2reader in no particular order.


Factories
--------------

All resources are loaded through a factory. There are four kinds:

* :class:`~sc2reader.factories.SC2Factory` - Basic factory. Loads resources.
* :class:`~sc2reader.factories.DictCachedSC2Factory` - Caches remote resources in memory. When loading remote resources, the dict cache is checked first.
* :class:`~sc2reader.factories.FileCachedSC2Factory` - Caches remote resources on the file system. When loading remote resources, the file system is checked first.
* :class:`~sc2reader.factories.DoubleCachedSC2Factory` - Caches remote resource in memory and on the file system.

A default factory is automatically configured and attached to the ``sc2reader`` module when the library is imported. Calling any factory method on the sc2reader module will use this default factory::

	sc2reader.configure(debug=True)
	replay = sc2reader.load_replay('my_replay.SC2Replay')

The default factory can be configured with the following environment variables:

* SC2READER_CACHE_DIR - Enables caching to file at the specified directory.
* SC2READER_CACHE_MAX_SIZE - Enables memory caching of resources with a maximum number of entries; not based on memory imprint!


Resources
----------------

A Starcraft II resource is any Starcraft II game file. This primarily refers to :class:`~sc2reader.resources.Replay` and :class:`~sc2reader.resources.Map` resources but also includes less common resources such as :class:`~sc2reader.resources.GameSummary`, :class:`~sc2reader.resources.Localization`, and SC2Mods.


Player vs User
-----------------

All entities in a replay fall into one of two overlapping buckets:

* User: A human entity, only users have game and message events.
* Player: A entity that actively plays in the game, only players have tracker events.

As such the following statements are true:

* A Participant is a Player **and** a User
* An Observer is a User **and not** a Player
* An Computer is a Player **and not** a User


Game vs Real
----------------

Many attributes in sc2reader are prefixed with ``game_`` and ``real_``. Game refers to the value encoded in the replay. Real refers to the real life value, as best as we can tell. For instance, ``game_type`` might be 2v2 but by looking at the teams we know that ``real_type`` is 1v1.


GameEngine
----------------

The game engine is used to process replay events and augument the replay with new statistics and game state. It implements a plugin system that allows developers
to inject their own logic into the game loop. It also allows plugins to ``yield`` new
events to the event stream. This allows for basic message passing between plugins.

A default engine is automatically configured and attached to the ``sc2reader.engine`` module when the library is imported. Calling any game engine method on the engine module will use this default factory::

	sc2reader.engine.register_plugin(MyPlugin())
	sc2reader.engine.run(replay)


Datapack
-----------------

A datapack is a collection of :class:`~sc2reader.data.Unit` and :class:`~sc2reader.data.Ability` classes that represent the game meta data for a given replay. Because this information is not stored in a replay, sc2reader ships with a datapack for standard ladder games from each Starcraft patch.

For non-standard maps, this datapack will be both wrong and incomplete and the Unit/Ability data should not be trusted. If you want to add a datapack for your map, see the article on :doc:`addingnewdatapacks`.
