from __future__ import absolute_import

import json
import functools
from collections import defaultdict

from sc2reader import log_utils
from sc2reader.utils import Length
from sc2reader.events import SelectionEvent, HotkeyEvent, AddToHotkeyEvent, GetFromHotkeyEvent, SetToHotkeyEvent
from sc2reader.plugins.utils import PlayerSelection, GameState, JSONDateEncoder, plugin

@plugin
def toJSON(replay, **user_options):
    options = dict(cls=JSONDateEncoder)
    options.update(user_options)
    return json.dumps(toDict(replay), **options)

@plugin
def toDict(replay):
    # Build observers into dictionary
    observers = list()
    for observer in replay.observers:
        messages = list()
        for message in getattr(observer,'messages',list()):
            messages.append({
                'time': message.time.seconds,
                'text': message.text,
                'is_public': message.to_all
            })
        observers.append({
            'name': getattr(observer, 'name', None),
            'pid': getattr(observer, 'pid', None),
            'messages': messages,
        })

    # Build players into dictionary
    players = list()
    for player in replay.players:
        messages = list()
        for message in player.messages:
            messages.append({
                'time': message.time.seconds,
                'text': message.text,
                'is_public': message.to_all
            })
        players.append({
            'avg_apm': getattr(player, 'avg_apm', None),
            'color': getattr(player, 'color', None),
            'name': getattr(player, 'name', None),
            'pick_race': getattr(player, 'pick_race', None),
            'pid': getattr(player, 'pid', None),
            'play_race': getattr(player, 'play_race', None),
            'result': getattr(player, 'result', None),
            'type': getattr(player, 'type', None),
            'uid': getattr(player, 'uid', None),
            'url': getattr(player, 'url', None),
            'messages': messages,
        })

    # Consolidate replay metadata into dictionary
    return {
        'gateway': getattr(replay, 'gateway', None),
        'map': getattr(replay, 'map', None),
        'file_time': getattr(replay, 'file_time', None),
        'unix_timestamp': getattr(replay, 'unix_timestamp', None),
        'date': getattr(replay, 'date', None),
        'utc_date': getattr(replay, 'utc_date', None),
        'speed': getattr(replay, 'speed', None),
        'category': getattr(replay, 'category', None),
        'type': getattr(replay, 'type', None),
        'is_ladder': getattr(replay, 'is_ladder', False),
        'is_private': getattr(replay, 'is_private', False),
        'filename': getattr(replay, 'filename', None),
        'file_time': getattr(replay, 'file_time', None),
        'frames': getattr(replay, 'frames', None),
        'build': getattr(replay, 'build', None),
        'release': getattr(replay, 'release_string', None),
        'length': getattr(getattr(replay, 'length', None),'seconds', None),
        'players': players,
        'observers': observers
    }

@plugin
def APMTracker(replay):
    efilter = lambda event: getattr(event,'is_player_action',False)
    for player in replay.players:
        player.aps = defaultdict(int)
        player.apm = defaultdict(int)
        for event in filter(efilter, player.events):
            player.aps[event.second] += 1
            player.apm[event.second/60] += 1
        player.avg_apm = sum(player.apm.values())/float(len(player.apm.keys()))

@plugin
def SelectionTracker(replay):
    logger = log_utils.get_logger(SelectionTracker)
    efilter = lambda e: isinstance(e, SelectionEvent) or isinstance(e, HotkeyEvent)

    for person in replay.people:
        # TODO: A more robust person interface might be nice
        person.selection_errors = 0
        person.selection = GameState(PlayerSelection())
        for event in filter(efilter, person.events):
            if replay.opt.debug:
                logger.debug("Event bytes: "+event.bytes.encode("hex"))

            error = False
            selection = person.selection[event.frame]

            if isinstance(event, SetToHotkeyEvent):
                # Make a copy to decouple the hotkey from primary selection
                selection[event.hotkey] = selection[0x0A].copy()
                logger.info("[{0}] {1} set hotkey {2} to current selection".format(Length(seconds=event.second),person.name,event.hotkey))

            elif isinstance(event, AddToHotkeyEvent):
                error = not selection[event.hotkey].deselect(*event.deselect)
                selection[event.hotkey].select(selection[0x0A].objects)
                logger.info("[{0}] {1} added current selection to hotkey {2}".format(Length(seconds=event.second),person.name,event.hotkey))

            elif isinstance(event, GetFromHotkeyEvent):
                # For some reason they leave the hotkey buffer unmodified so make a copy
                selection[0x0A] = selection[event.hotkey].copy()
                error = not selection[0x0A].deselect(*event.deselect)
                logger.info("[{0}] {1} retrieved hotkey {2}, {3} units: {4}".format(Length(seconds=event.second),person.name,event.hotkey,len(selection[0x0A].objects),selection[0x0A]))

            elif isinstance(event, SelectionEvent):
                error = not selection[0x0A].deselect(*event.deselect)
                selection[0x0A].select(event.objects)
                logger.info("[{0}] {1} selected {2} units: {3}".format(Length(seconds=event.second),person.name,len(selection[0x0A].objects),selection[0x0A]))

            # TODO: The event level interface here should be improved
            #       Possibly use 'added' and 'removed' unit lists as well
            event.selected = selection[0x0A].objects
            if error:
                person.selection_errors += 1
                if replay.opt.debug:
                    logger.warn("Error detected in deselection mode {}.".format(event.deselect[0]))
