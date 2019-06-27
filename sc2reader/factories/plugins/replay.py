# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import json
from collections import defaultdict

from sc2reader import log_utils
from sc2reader.utils import Length
from sc2reader.factories.plugins.utils import (
    PlayerSelection,
    GameState,
    JSONDateEncoder,
    plugin,
)


@plugin
def toJSON(replay, **user_options):
    options = dict(cls=JSONDateEncoder)
    options.update(user_options)
    obj = toDict()(replay)
    return json.dumps(obj, **options)


@plugin
def toDict(replay):
    # Build observers into dictionary
    observers = list()
    for observer in replay.observers:
        messages = list()
        for message in getattr(observer, "messages", list()):
            messages.append(
                {
                    "time": message.time.seconds,
                    "text": message.text,
                    "is_public": message.to_all,
                }
            )
        observers.append(
            {
                "name": getattr(observer, "name", None),
                "pid": getattr(observer, "pid", None),
                "messages": messages,
            }
        )

    # Build players into dictionary
    players = list()
    for player in replay.players:
        messages = list()
        for message in player.messages:
            messages.append(
                {
                    "time": message.time.seconds,
                    "text": message.text,
                    "is_public": message.to_all,
                }
            )
        players.append(
            {
                "avg_apm": getattr(player, "avg_apm", None),
                "color": player.color.__dict__ if hasattr(player, "color") else None,
                "handicap": getattr(player, "handicap", None),
                "name": getattr(player, "name", None),
                "pick_race": getattr(player, "pick_race", None),
                "pid": getattr(player, "pid", None),
                "play_race": getattr(player, "play_race", None),
                "result": getattr(player, "result", None),
                "type": getattr(player, "type", None),
                "uid": getattr(player, "uid", None),
                "url": getattr(player, "url", None),
                "messages": messages,
            }
        )

    # Consolidate replay metadata into dictionary
    return {
        "region": getattr(replay, "region", None),
        "map_name": getattr(replay, "map_name", None),
        "file_time": getattr(replay, "file_time", None),
        "filehash": getattr(replay, "filehash", None),
        "unix_timestamp": getattr(replay, "unix_timestamp", None),
        "date": getattr(replay, "date", None),
        "utc_date": getattr(replay, "utc_date", None),
        "speed": getattr(replay, "speed", None),
        "category": getattr(replay, "category", None),
        "type": getattr(replay, "type", None),
        "is_ladder": getattr(replay, "is_ladder", False),
        "is_private": getattr(replay, "is_private", False),
        "filename": getattr(replay, "filename", None),
        "file_time": getattr(replay, "file_time", None),
        "frames": getattr(replay, "frames", None),
        "build": getattr(replay, "build", None),
        "release": getattr(replay, "release_string", None),
        "game_fps": getattr(replay, "game_fps", None),
        "game_length": getattr(getattr(replay, "game_length", None), "seconds", None),
        "players": players,
        "observers": observers,
        "real_length": getattr(getattr(replay, "real_length", None), "seconds", None),
        "real_type": getattr(replay, "real_type", None),
        "time_zone": getattr(replay, "time_zone", None),
        "versions": getattr(replay, "versions", None),
    }


@plugin
def APMTracker(replay):
    """
    Builds ``player.aps`` and ``player.apm`` dictionaries where an action is
    any Selection, Hotkey, or Command event.

    Also provides ``player.avg_apm`` which is defined as the sum of all the
    above actions divided by the number of seconds played by the player (not
    necessarily the whole game) multiplied by 60.
    """
    for player in replay.players:
        player.aps = defaultdict(int)
        player.apm = defaultdict(int)
        player.seconds_played = replay.length.seconds

        for event in player.events:
            if (
                event.name == "SelectionEvent"
                or "CommandEvent" in event.name
                or "ControlGroup" in event.name
            ):
                player.aps[event.second] += 1.4
                player.apm[int(event.second / 60)] += 1.4

            elif event.name == "PlayerLeaveEvent":
                player.seconds_played = event.second

        if len(player.apm) > 0:
            player.avg_apm = (
                sum(player.aps.values()) / float(player.seconds_played) * 60
            )
        else:
            player.avg_apm = 0

    return replay


@plugin
def SelectionTracker(replay):
    debug = replay.opt["debug"]
    logger = log_utils.get_logger(SelectionTracker)

    for person in replay.entities:
        # TODO: A more robust person interface might be nice
        person.selection_errors = 0
        player_selections = GameState(PlayerSelection())
        for event in person.events:
            error = False
            if event.name == "SelectionEvent":
                selections = player_selections[event.frame]
                control_group = selections[event.control_group].copy()
                error = not control_group.deselect(event.mask_type, event.mask_data)
                control_group.select(event.new_units)
                selections[event.control_group] = control_group
                if debug:
                    logger.info(
                        "[{0}] {1} selected {2} units: {3}".format(
                            Length(seconds=event.second),
                            person.name,
                            len(selections[0x0A].objects),
                            selections[0x0A],
                        )
                    )

            elif event.name == "SetControlGroupEvent":
                selections = player_selections[event.frame]
                selections[event.control_group] = selections[0x0A].copy()
                if debug:
                    logger.info(
                        "[{0}] {1} set hotkey {2} to current selection".format(
                            Length(seconds=event.second), person.name, event.hotkey
                        )
                    )

            elif event.name == "AddToControlGroupEvent":
                selections = player_selections[event.frame]
                control_group = selections[event.control_group].copy()
                error = not control_group.deselect(event.mask_type, event.mask_data)
                control_group.select(selections[0x0A].objects)
                selections[event.control_group] = control_group
                if debug:
                    logger.info(
                        "[{0}] {1} added current selection to hotkey {2}".format(
                            Length(seconds=event.second), person.name, event.hotkey
                        )
                    )

            elif event.name == "GetControlGroupEvent":
                selections = player_selections[event.frame]
                control_group = selections[event.control_group].copy()
                error = not control_group.deselect(event.mask_type, event.mask_data)
                selections[0xA] = control_group
                if debug:
                    logger.info(
                        "[{0}] {1} retrieved hotkey {2}, {3} units: {4}".format(
                            Length(seconds=event.second),
                            person.name,
                            event.control_group,
                            len(selections[0x0A].objects),
                            selections[0x0A],
                        )
                    )

            else:
                continue

            # TODO: The event level interface here should be improved
            #       Possibly use 'added' and 'removed' unit lists as well
            event.selected = selections[0x0A].objects
            if error:
                person.selection_errors += 1
                if debug:
                    logger.warn(
                        "Error detected in deselection mode {0}.".format(
                            event.mask_type
                        )
                    )

        person.selection = player_selections
        # Not a real lock, so don't change it!
        person.selection.locked = True

    return replay
