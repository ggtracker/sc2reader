Creating a GameEngine Plugin
================================

Handling Events
--------------------

Plugins can opt in to handle events with methods with the following naming convention::

	def handleEventName(self, event, replay)

In addition to handling specific event types, plugins can also handle events more generally by handling built-in parent classes from the list below:

* handleEvent - called for every single event of all types
* handleMessageEvent - called for events in replay.message.events
* handleGameEvent - called for events in replay.game.events
* handleTrackerEvent - called for events in replay.tracker.events
* handlePlayerActionEvent - called for all game events indicating player actions
* handleAbilityEvent - called for all types of ability events
* handleHotkeyEvent - called for all player hotkey events

For every event in a replay, the GameEngine will loop over all of its registered plugins looking for functions to handle that event. Matching handlers are called in order of plugin registration from most general to most specific.

Given the following plugins::

    class Plugin1():
        def handleAbilityEvent(self, event, replay):
            pass

    class Plugin2():
        def handleEvent(self, event, replay):
            pass

        def handleTargetAbilityEvent(self, event, replay):
            pass

    sc2reader.engine.register_plugin(Plugin1())
    sc2reader.engine.register_plugin(Plugin2())

When the engine handles a ``TargetAbilityEvent`` it will call handlers in the following order::

    Plugin1.handleAbilityEvent(event, replay)
    Plugin2.handleEvent(event, replay)
    Plugin2.handleTargetAbilityEvent(event, replay)

Setup and Cleanup
---------------------

Plugins may also handle special ``InitGame`` and ``EndGame`` events. These handlers for these events are called directly before and after the processing of the replay events:

* handleInitGame - is called prior to processing a new replay to provide
  an opportunity for the plugin to clear internal state and set up any
  replay state necessary.

* handleEndGame - is called after all events have been processed and
  can be used to perform post processing on aggrated data or clean up
  intermediate data caches.

Message Passing
--------------------

Event handlers can choose to ``yield`` additional events which will be injected into the event stream directly after the event currently being processed. This feature allows for message passing between plugins. An ExpansionTracker plugin could notify all other plugins of a new ExpansionEvent that they could opt to process::

	def handleUnitDoneEvent(self, event, replay):
		if event.unit.name == 'Nexus':
			yield ExpansionEvent(event.frame, event.unit)
		...

Early Exits
--------------------

If a plugin wishes to stop processing a replay it can yield a PluginExit event before returning::

	def handleEvent(self, event, replay):
		if len(replay.tracker_events) == 0:
			yield PluginExit(self, code=0, details=dict(msg="tracker events required"))
			return
		...

	def handleAbilityEvent(self, event, replay):
		try:
			possibly_throwing_error()
		catch Error as e:
			logger.error(e)
			yield PluginExit(self, code=0, details=dict(msg="Unexpected exception"))
			return

The GameEngine will intercept this event and remove the plugin from the list of active plugins for this replay. The exit code and details will be available from the replay::

	code, details = replay.plugins['MyPlugin']

Using Your Plugin
-----------------

To use your plugin with sc2reader, just register it to the game engine:

	sc2reader.engine.register_plugin(MyPlugin())

Plugins will be called in order of registration for each event. If plugin B depends on plugin A make sure to register plugin A first!
