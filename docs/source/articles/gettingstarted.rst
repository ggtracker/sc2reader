Getting Started with SC2Reader
==================================

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

There are a growing number of community generated plugins that you can take advantage of in your project. See the article on :doc:`creatingagameengineplugin` for details on creating your own. To use these plugins you need to customize the game engine::

	from sc2reader.engine.plugins import SelectionTracker, APMTracker
	sc2reader.engine.register_plugin(SelectionTracker())
	sc2reader.engine.register_plugin(APMTracker())

The :class:`~sc2reader.engine.plugins.ContextLoader` and :class:`~sc2reader.engine.plugins.GameHeartNormalizer` plugins are registered by default.
