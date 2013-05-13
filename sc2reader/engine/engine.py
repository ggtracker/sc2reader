from __future__ import absolute_import

import collections
from sc2reader.events import *

class InitGameEvent(object):
    name = 'InitGame'

class EndGameEvent(object):
    name = 'EndGame'

class GameEngine(object):
    """ GameEngine Specification
        --------------------------

        The game engine runs through all the events for a given replay in
        chronological order. For each event, event handlers from registered
        plugins are executed in order of plugin registration from most general
        to most specific.

        Example Usage::

            class Plugin1():
                def handleAbilityEvent(self, event, replay):
                    pass

            class Plugin2():
                def handleEvent(self, event, replay):
                    pass

                def handleTargetAbilityEvent(self, event, replay):
                    pass

            ...

            engine = GameEngine(plugins=[Plugin1(), Plugin2()], **options)
            engine.register_plugins(Plugin3(), Plugin(4))
            engine.reigster_plugin(Plugin(5))
            engine.run(replay)

        Calls functions in the following order for a ``TargetUnitEvent``::

            Plugin1.handleAbilityEvent(replay, event)
            Plugin2.handleEvent(replay, event)
            Plugin2.handleTargetAbilityEvent(replay, event)


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
            * handlePlayerActionEvent - called for all game events indicating player actions
            * handleAbilityEvent - called for all types of ability events
            * handleHotkeyEvent - called for all player hotkey events

        Plugins may also handle optional InitGame and EndGame events generated
        by the GameEngine before and after processing all the events:

          * handleInitGame - is called prior to processing a new replay to provide
            an opportunity for the plugin to clear internal state and set up any
            replay state necessary.

          * handleEndGame - is called after all events have been processed and
            can be used to perform post processing on aggrated data or clean up
            intermediate data caches.

        Event handlers can choose to ``yield`` additional events which will be injected
        into the event stream directly after the event currently being processed. This is
        a great way to send messages to downstream plugins.
    """
    def __init__(self, plugins=[]):
        self._plugins = list()
        self.register_plugins(*plugins)

    def register_plugin(self, plugin):
        self._plugins.append(plugin)

    def register_plugins(self, *plugins):
        for plugin in plugins:
            self.register_plugin(plugin)

    def run(self, replay):
        # A map of [event.name] => event handlers in plugin registration order
        # ranked from most generic to most specific
        handlers = dict()

        # Fill event event queue with the replay events, bookmarked by Init and End events.
        event_queue = collections.deque()
        event_queue.append(InitGameEvent())
        event_queue.extend(replay.events)
        event_queue.append(EndGameEvent())

        # Work through the events in the queue, pushing newly emitted events to
        # the front of the line for immediate processing.
        while len(event_queue) > 0:
            event = event_queue.popleft()

            # If we haven't compiled a list of handlers for this event yet, do so!
            if event.name not in handlers:
                event_handlers = self._get_event_handlers(event)
                handlers[event.name] = event_handlers
            else:
                event_handlers = handlers[event.name]

            # Events have the option of yielding one or more additional events
            # which get processed after the current event finishes.
            new_events = list()
            for event_handler in event_handlers:
                new_events.extend(event_handler(event, replay) or [])

            # extendleft does a series of appendlefts and reverses the order so we
            # need to reverse the list first to have them added in order.
            event_queue.extendleft(new_events)


    def _get_event_handlers(self, event):
        return sum([self._get_plugin_event_handlers(plugin, event) for plugin in self._plugins],[])

    def _get_plugin_event_handlers(self, plugin, event):
        handlers = list()
        if isinstance(event, Event) and self._has_event_handler(plugin, Event):
            handlers.append(self._get_event_handler(plugin,Event))
        if isinstance(event, MessageEvent) and self._has_event_handler(plugin, MessageEvent):
            handlers.append(self._get_event_handler(plugin,MessageEvent))
        if isinstance(event, GameEvent) and self._has_event_handler(plugin, GameEvent):
            handlers.append(self._get_event_handler(plugin,GameEvent))
        if isinstance(event, TrackerEvent) and self._has_event_handler(plugin, TrackerEvent):
            handlers.append(self._get_event_handler(plugin,TrackerEvent))
        if isinstance(event, PlayerActionEvent) and self._has_event_handler(plugin, PlayerActionEvent):
            handlers.append(self._get_event_handler(plugin,PlayerActionEvent))
        if isinstance(event, AbilityEvent) and self._has_event_handler(plugin, AbilityEvent):
            handlers.append(self._get_event_handler(plugin,AbilityEvent))
        if isinstance(event, HotkeyEvent) and self._has_event_handler(plugin, HotkeyEvent):
            handlers.append(self._get_event_handler(plugin,HotkeyEvent))
        if self._has_event_handler(plugin, event):
            handlers.append(self._get_event_handler(plugin,event))
        return handlers

    def _has_event_handler(self, plugin, event):
        return hasattr(plugin, 'handle'+event.name)

    def _get_event_handler(self, plugin, event):
        return getattr(plugin, 'handle'+event.name, None)


if __name__ == '__main__':
    from sc2reader.events import UserOptionsEvent, GameStartEvent, PlayerLeaveEvent
    class TestEvent(object):
        name = 'TestEvent'
        def __init__(self, source):
            self.source = source

    class TestPlugin(object):
        yields = TestEvent

        def handleInitGame(self, event, replay,):
            yield TestEvent(event.name)

        def handleTestEvent(self, event, replay):
            print event.source

        def handleGameStartEvent(self, event, replay):
            yield TestEvent(event.name)

        def handleEndGame(self, event, replay):
            yield TestEvent(event.name)

    class TestReplay(object):
        events = [UserOptionsEvent, UserOptionsEvent, GameStartEvent, PlayerLeaveEvent]

    engine = GameEngine()
    engine.register_plugin(TestPlugin())
    events = engine.run(TestReplay)
