# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import collections
from sc2reader.events import *
from sc2reader.engine.events import InitGameEvent, EndGameEvent, PluginExit


class GameEngine(object):
    """
    GameEngine Specification
    --------------------------

    The game engine runs through all the events for a given replay in
    chronological order. For each event, event handlers from registered
    plugins are executed in order of plugin registration from most general
    to most specific.

    Example Usage::

        class Plugin1():
            def handleCommandEvent(self, event, replay):
                pass

        class Plugin2():
            def handleEvent(self, event, replay):
                pass

            def handleTargetUnitCommandEvent(self, event, replay):
                pass

        ...

        engine = GameEngine(plugins=[Plugin1(), Plugin2()], **options)
        engine.register_plugins(Plugin3(), Plugin(4))
        engine.reigster_plugin(Plugin(5))
        engine.run(replay)

    Calls functions in the following order for a ``TargetUnitCommandEvent``::

        Plugin1.handleCommandEvent(event, replay)
        Plugin2.handleEvent(event, replay)
        Plugin2.handleTargetUnitCommandEvent(event, replay)


    Plugin Specification
    -------------------------

    Plugins can opt in to handle events with methods in the format:

        def handleEventName(self, event, replay)

    In addition to handling specific event types, plugins can also
    handle events more generally by handling built-in parent classes
    from the list below::

        * handleEvent - called for every single event of all types
        * handleMessageEvent - called for events in replay.message.events
        * handleGameEvent - called for events in replay.game.events
        * handleTrackerEvent - called for events in replay.tracker.events
        * handleCommandEvent - called for all types of command events
        * handleControlGroupEvent - called for all player control group events

    Plugins may also handle optional ``InitGame`` and ``EndGame`` events generated
    by the GameEngine before and after processing all the events:

      * handleInitGame - is called prior to processing a new replay to provide
        an opportunity for the plugin to clear internal state and set up any
        replay state necessary.

      * handleEndGame - is called after all events have been processed and
        can be used to perform post processing on aggrated data or clean up
        intermediate data caches.

    Event handlers can choose to ``yield`` additional events which will be injected
    into the event stream directly after the event currently being processed. This
    feature allows for message passing between plugins. An ExpansionTracker plugin
    could notify all other plugins of a new ExpansionEvent that they could opt to
    process::

        def handleUnitDoneEvent(self, event, replay):
            if event.unit.name == 'Nexus':
                yield ExpansionEvent(event.frame, event.unit)
            ....

    If a plugin wishes to stop processing a replay it can yield a PluginExit event before returning::

        def handleEvent(self, event, replay):
            if len(replay.tracker_events) == 0:
                yield PluginExit(self, code=0, details=dict(msg="tracker events required"))
                return
            ...

        def handleCommandEvent(self, event, replay):
            try:
                possibly_throwing_error()
            catch Error as e:
                logger.error(e)
                yield PluginExit(self, code=0, details=dict(msg="Unexpected exception"))

    The GameEngine will intercept this event and remove the plugin from the list of
    active plugins for this replay. The exit code and details will be available from the
    replay::

        code, details = replay.plugins['MyPlugin']

    If your plugin depends on another plugin, it is a good idea to implement handlePluginExit
    and be alerted if the plugin that you require fails. This way you can exit gracefully. You
    can also check to see if the plugin name is in ``replay.plugin_failures``::

        if 'RequiredPlugin' in replay.plugin_failures:
            code, details = replay.plugins['RequiredPlugin']
            message = "RequiredPlugin failed with code: {0}. Cannot continue.".format(code)
            yield PluginExit(self, code=1, details=dict(msg=message))
    """

    def __init__(self, plugins=[]):
        self._plugins = list()
        self.register_plugins(*plugins)

    def register_plugin(self, plugin):
        self._plugins.append(plugin)

    def register_plugins(self, *plugins):
        for plugin in plugins:
            self.register_plugin(plugin)

    def plugins(self):
        return self._plugins

    def run(self, replay):
        # A map of [event.name] => event handlers in plugin registration order
        # ranked from most generic to most specific
        handlers = dict()

        # Create a local copy of the plugins list. As plugins exit we can
        # remove them from this list and regenerate event handlers.
        plugins = list(self._plugins)

        # Create a dict for storing plugin exit codes and details.
        replay.plugin_result = replay.plugins = dict()

        # Create a list storing replay.plugins keys for failures.
        replay.plugin_failures = list()

        # Fill event event queue with the replay events, bookmarked by Init and End events.
        event_queue = collections.deque()
        event_queue.append(InitGameEvent())
        event_queue.extend(replay.events)
        event_queue.append(EndGameEvent())

        # Work through the events in the queue, pushing newly emitted events to
        # the front of the line for immediate processing.
        while len(event_queue) > 0:
            event = event_queue.popleft()

            if event.name == "PluginExit":
                # Remove the plugin and reset the handlers.
                plugins.remove(event.plugin)
                handlers.clear()
                replay.plugin_result[event.plugin.name] = (event.code, event.details)
                if event.code != 0:
                    replay.plugin_failures.append(event.plugin.name)

            # If we haven't compiled a list of handlers for this event yet, do so!
            if event.name not in handlers:
                event_handlers = self._get_event_handlers(event, plugins)
                handlers[event.name] = event_handlers
            else:
                event_handlers = handlers[event.name]

            # Events have the option of yielding one or more additional events
            # which get processed after the current event finishes. The new_events
            # batch is constructed in reverse order because extendleft reverses
            # the order again with a series of appendlefts.
            new_events = collections.deque()
            for event_handler in event_handlers:
                try:
                    for new_event in event_handler(event, replay) or []:
                        if new_event.name == "PluginExit":
                            new_events.append(new_event)
                            break
                        else:
                            new_events.appendleft(new_event)
                except Exception as e:
                    if event_handler.__self__.name in ["ContextLoader"]:
                        # Certain built in plugins should probably still cause total failure
                        raise  # Maybe??
                    else:
                        new_event = PluginExit(
                            event_handler.__self__, code=1, details=dict(error=e)
                        )
                        new_events.append(new_event)
            event_queue.extendleft(new_events)

        # For any plugins that didn't yield a PluginExit event or throw unexpected exceptions,
        # record a successful completion.
        for plugin in plugins:
            replay.plugin_result[plugin.name] = (0, dict())

    def _get_event_handlers(self, event, plugins):
        return sum(
            [self._get_plugin_event_handlers(plugin, event) for plugin in plugins], []
        )

    def _get_plugin_event_handlers(self, plugin, event):
        handlers = list()
        if isinstance(event, Event) and hasattr(plugin, "handleEvent"):
            handlers.append(getattr(plugin, "handleEvent", None))
        if isinstance(event, MessageEvent) and hasattr(plugin, "handleMessageEvent"):
            handlers.append(getattr(plugin, "handleMessageEvent", None))
        if isinstance(event, GameEvent) and hasattr(plugin, "handleGameEvent"):
            handlers.append(getattr(plugin, "handleGameEvent", None))
        if isinstance(event, TrackerEvent) and hasattr(plugin, "handleTrackerEvent"):
            handlers.append(getattr(plugin, "handleTrackerEvent", None))
        if isinstance(event, CommandEvent) and hasattr(plugin, "handleCommandEvent"):
            handlers.append(getattr(plugin, "handleCommandEvent", None))
        if isinstance(event, ControlGroupEvent) and hasattr(
            plugin, "handleControlGroupEvent"
        ):
            handlers.append(getattr(plugin, "handleControlGroupEvent", None))
        if hasattr(plugin, "handle" + event.name):
            handlers.append(getattr(plugin, "handle" + event.name, None))
        return handlers
