# -*- coding: utf-8 -*-
# TODO: Dry this up a bit!
from __future__ import absolute_import, print_function, unicode_literals, division

from sc2reader.log_utils import loggable
from sc2reader.utils import Length


@loggable
class ContextLoader(object):
    name = "ContextLoader"

    def handleInitGame(self, event, replay):
        replay.units = set()
        replay.unit = dict()

        # keep track of last TargetUnitCommandEvent for UpdateTargetUnitCommandEvent
        self.last_target_ability_event = {}

    def handleGameEvent(self, event, replay):
        self.load_message_game_player(event, replay)

    def handleMessageEvent(self, event, replay):
        self.load_message_game_player(event, replay)

    def handleCommandEvent(self, event, replay):
        if not replay.datapack:
            return

        if event.ability_id not in replay.datapack.abilities:
            # safeguard against missing abilities
            if event.player.pid in self.last_target_ability_event:
                del self.last_target_ability_event[event.player.pid]

            if not getattr(replay, "marked_error", None):
                replay.marked_error = True
                event.logger.error(replay.filename)
                event.logger.error("Release String: " + replay.release_string)
                for player in replay.players:
                    try:
                        event.logger.error(
                            "\t" + unicode(player).encode("ascii", "ignore")
                        )
                    except NameError:  # unicode() is not defined in Python 3
                        event.logger.error("\t" + player.__str__())

            self.logger.error(
                "{0}\t{1}\tMissing ability {2:X} from {3}".format(
                    event.frame,
                    event.player.name,
                    event.ability_id,
                    replay.datapack.__class__.__name__,
                )
            )

        else:
            event.ability = replay.datapack.abilities[event.ability_id]
            event.ability_name = event.ability.name

        if event.other_unit_id in replay.objects:
            event.other_unit = replay.objects[event.other_unit_id]
        elif event.other_unit_id is not None:
            self.logger.error("Other unit {0} not found".format(event.other_unit_id))

    def handleTargetUnitCommandEvent(self, event, replay):
        self.last_target_ability_event[event.player.pid] = event

        if not replay.datapack:
            return

        if event.target_unit_id in replay.objects:
            event.target = replay.objects[event.target_unit_id]
            if not replay.tracker_events and not event.target.is_type(
                event.target_unit_type
            ):
                replay.datapack.change_type(
                    event.target, event.target_unit_type, event.frame
                )
        else:
            # Often when the target_unit_id is not in replay.objects it is 0 because it
            # is a target building/destructable hidden by fog of war. Perhaps we can match
            # it through the fog using location?
            unit = replay.datapack.create_unit(
                event.target_unit_id, event.target_unit_type, event.frame
            )
            event.target = unit
            replay.objects[event.target_unit_id] = unit

    def handleUpdateTargetUnitCommandEvent(self, event, replay):
        # We may not find a TargetUnitCommandEvent before finding an
        # UpdateTargetUnitCommandEvent, perhaps due to Missing Abilities in the
        # datapack
        if event.player.pid in self.last_target_ability_event:
            # store corresponding TargetUnitCommandEvent data in this event
            # currently using for *MacroTracker only, so only need ability name
            event.ability_name = self.last_target_ability_event[
                event.player.pid
            ].ability_name

        self.handleTargetUnitCommandEvent(event, replay)

    def handleSelectionEvent(self, event, replay):
        if not replay.datapack:
            return

        units = list()
        # TODO: Blizzard calls these subgroup flags but that doesn't make sense right now
        for (
            unit_id,
            unit_type,
            subgroup_flags,
            intra_subgroup_flags,
        ) in event.new_unit_info:
            # If we don't have access to tracker events, use selection events to create
            # new units and track unit type changes. It won't be perfect, but it is better
            # than nothing.
            if not replay.tracker_events:
                # Starting at 23925 the default viking mode is assault. Most people expect
                # the default viking mode to be figher so fudge it a bit here.
                if (
                    replay.versions[1] == 2
                    and replay.build >= 23925
                    and unit_type == 71
                ):
                    unit_type = 72

                if unit_id in replay.objects:
                    unit = replay.objects[unit_id]
                    if not unit.is_type(unit_type):
                        replay.datapack.change_type(unit, unit_type, event.frame)
                else:
                    unit = replay.datapack.create_unit(unit_id, unit_type, event.frame)
                    replay.objects[unit_id] = unit

            # If we have tracker events, the unit must already exist and must already
            # have the correct unit type.
            elif unit_id in replay.objects:
                unit = replay.objects[unit_id]

            # Except when it doesn't.
            else:
                unit = replay.datapack.create_unit(unit_id, unit_type, event.frame)
                replay.objects[unit_id] = unit

            # Selection events hold flags on units (like hallucination)
            unit.apply_flags(intra_subgroup_flags)

            units.append(unit)

        event.new_units = event.objects = units

    def handleResourceTradeEvent(self, event, replay):
        event.sender = event.player
        event.recipient = replay.player[event.recipient_id]

    def handleHijackReplayGameEvent(self, event, replay):
        replay.resume_from_replay = True
        replay.resume_method = event.method
        replay.resume_user_info = event.user_infos

    def handlePlayerStatsEvent(self, event, replay):
        self.load_tracker_player(event, replay)

    def handleUnitBornEvent(self, event, replay):
        self.load_tracker_upkeeper(event, replay)
        self.load_tracker_controller(event, replay)

        if not replay.datapack:
            return

        if event.unit_id in replay.objects:
            # This can happen because game events are done first
            event.unit = replay.objects[event.unit_id]
        else:
            # TODO: How to tell if something is hallucination?
            event.unit = replay.datapack.create_unit(
                event.unit_id, event.unit_type_name, event.frame
            )
            replay.objects[event.unit_id] = event.unit

        replay.active_units[event.unit_id_index] = event.unit
        event.unit.location = event.location
        event.unit.started_at = event.frame
        event.unit.finished_at = event.frame

        if event.unit_upkeeper:
            event.unit.owner = event.unit_upkeeper
            event.unit.owner.units.append(event.unit)

    def handleUnitDiedEvent(self, event, replay):
        if not replay.datapack:
            return

        if event.unit_id in replay.objects:
            event.unit = replay.objects[event.unit_id]
            event.unit.died_at = event.frame
            event.unit.location = event.location
            if event.unit_id_index in replay.active_units:
                del replay.active_units[event.unit_id_index]
            else:
                self.logger.error(
                    "Unable to delete unit index {0} at {1} [{2}], index not active.".format(
                        event.killer_pid, Length(seconds=event.second), event.frame
                    )
                )
        else:
            self.logger.error(
                "Unit {0} died at {1} [{2}] before it was born!".format(
                    event.unit_id, Length(seconds=event.second), event.frame
                )
            )

        if event.killing_player_id in replay.player:
            event.killing_player = event.killer = replay.player[event.killing_player_id]
            if event.unit:
                event.unit.killing_player = event.unit.killed_by = event.killing_player
                event.killing_player.killed_units.append(event.unit)
        elif event.killing_player_id:
            self.logger.error(
                "Unknown killing player id {0} at {1} [{2}]".format(
                    event.killing_player_id, Length(seconds=event.second), event.frame
                )
            )

        if event.killing_unit_id in replay.objects:
            event.killing_unit = replay.objects[event.killing_unit_id]
            if event.unit:
                event.unit.killing_unit = event.killing_unit
                event.killing_unit.killed_units.append(event.unit)
        elif event.killing_unit_id:
            self.logger.error(
                "Unknown killing unit id {0} at {1} [{2}]".format(
                    event.killing_unit_id, Length(seconds=event.second), event.frame
                )
            )

    def handleUnitOwnerChangeEvent(self, event, replay):
        self.load_tracker_controller(event, replay)
        self.load_tracker_upkeeper(event, replay)

        if not replay.datapack:
            return

        if event.unit_id in replay.objects:
            event.unit = replay.objects[event.unit_id]
        else:
            self.logger.error(
                "Unit {0} owner changed at {1} [{2}] before it was born!".format(
                    event.unit_id, Length(seconds=event.second), event.frame
                )
            )

        if event.unit_upkeeper and event.unit:
            if event.unit.owner:
                event.unit.owner.units.remove(event.unit)
            event.unit.owner = event.unit_upkeeper
            event.unit_upkeeper.units.append(event.unit)

    def handleUnitTypeChangeEvent(self, event, replay):
        if not replay.datapack:
            return

        if event.unit_id in replay.objects:
            event.unit = replay.objects[event.unit_id]
            replay.datapack.change_type(event.unit, event.unit_type_name, event.frame)
        else:
            self.logger.error(
                "Unit {0} type changed at {1} [{2}] before it was born!".format(
                    event.unit_id, Length(seconds=event.second)
                )
            )

    def handleUpgradeCompleteEvent(self, event, replay):
        self.load_tracker_player(event, replay)
        # TODO: We don't have upgrade -> ability maps
        # TODO: we can probably do the same thing we did for units

    def handleUnitInitEvent(self, event, replay):
        self.load_tracker_upkeeper(event, replay)
        self.load_tracker_controller(event, replay)

        if not replay.datapack:
            return

        if event.unit_id in replay.objects:
            event.unit = replay.objects[event.unit_id]
        else:
            # TODO: How to tell if something is hallucination?
            event.unit = replay.datapack.create_unit(
                event.unit_id, event.unit_type_name, event.frame
            )
            replay.objects[event.unit_id] = event.unit

        replay.active_units[event.unit_id_index] = event.unit
        event.unit.location = event.location
        event.unit.started_at = event.frame

        if event.unit_upkeeper:
            event.unit.owner = event.unit_upkeeper
            event.unit.owner.units.append(event.unit)

    def handleUnitDoneEvent(self, event, replay):
        if not replay.datapack:
            return

        if event.unit_id in replay.objects:
            event.unit = replay.objects[event.unit_id]
            event.unit.finished_at = event.frame
        else:
            self.logger.error(
                "Unit {0} done at {1} [{2}] before it was started!".format(
                    event.killer_pid, Length(seconds=event.second), event.frame
                )
            )

    def handleUnitPositionsEvent(self, event, replay):
        if not replay.datapack:
            return

        for unit_index, (x, y) in event.positions:
            if unit_index in replay.active_units:
                unit = replay.active_units[unit_index]
                unit.location = (x, y)
                event.units[unit] = unit.location
            else:
                self.logger.error(
                    "Unit at active_unit index {0} moved at {1} [{2}] but it doesn't exist!".format(
                        event.killer_pid, Length(seconds=event.second), event.frame
                    )
                )

    def load_message_game_player(self, event, replay):
        if replay.versions[1] == 1 or (
            replay.versions[1] == 2 and replay.build < 24247
        ):
            if event.pid in replay.entity:
                event.player = replay.entity[event.pid]
                event.player.events.append(event)
            elif event.pid != 16:
                self.logger.error(
                    "Bad pid ({0}) for event {1} at {2} [{3}].".format(
                        event.pid,
                        event.__class__,
                        Length(seconds=event.second),
                        event.frame,
                    )
                )
            else:
                pass  # This is a global event

        else:  # Now event.pid is actually a user id for human entities
            if event.pid < len(replay.humans):
                event.player = replay.human[event.pid]
                event.player.events.append(event)
            elif event.pid != 16:
                self.logger.error(
                    "Bad pid ({0}) for event {1} at {2} [{3}].".format(
                        event.pid,
                        event.__class__,
                        Length(seconds=event.second),
                        event.frame,
                    )
                )
            else:
                pass  # This is a global event

    def load_tracker_player(self, event, replay):
        if event.pid in replay.entity:
            event.player = replay.entity[event.pid]
        else:
            self.logger.error(
                "Bad pid ({0}) for event {1} at {2} [{3}].".format(
                    event.pid,
                    event.__class__,
                    Length(seconds=event.second),
                    event.frame,
                )
            )

    def load_tracker_upkeeper(self, event, replay):
        if event.upkeep_pid in replay.entity:
            event.unit_upkeeper = replay.entity[event.upkeep_pid]
        elif event.upkeep_pid != 0:
            self.logger.error(
                "Bad upkeep_pid ({0}) for event {1} at {2} [{3}].".format(
                    event.upkeep_pid,
                    event.__class__,
                    Length(seconds=event.second),
                    event.frame,
                )
            )

    def load_tracker_controller(self, event, replay):
        if event.control_pid in replay.entity:
            event.unit_controller = replay.entity[event.control_pid]
        elif event.control_pid != 0:
            self.logger.error(
                "Bad control_pid ({0}) for event {1} at {2} [{3}].".format(
                    event.control_pid,
                    event.__class__,
                    Length(seconds=event.second),
                    event.frame,
                )
            )
