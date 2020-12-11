# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from sc2reader.utils import Length
from sc2reader.events.base import Event
from sc2reader.log_utils import loggable

from itertools import chain


@loggable
class GameEvent(Event):
    """
    This is the base class for all game events. The attributes below are universally available.
    """

    def __init__(self, frame, pid):
        #: The id of the player generating the event. This is 16 for global non-player events.
        #: Prior to Heart of the Swarm this was the player id. Since HotS it is
        #: now the user id (uid), we still call it pid for backwards compatibility. You shouldn't
        #: ever need to use this; use :attr:`player` instead.
        self.pid = pid

        #: A reference to the :class:`~sc2reader.objects.Player` object representing
        #: this player in the replay. Not available for global events (:attr:`is_local` = False)
        self.player = None

        #: The frame of the game that this event was recorded at. 16 frames per game second.
        self.frame = frame

        #: The second of the game that this event was recorded at. 16 frames per game second.
        self.second = frame >> 4

        #: A flag indicating if it is a local or global event.
        self.is_local = pid != 16

        #: Short cut string for event class name
        self.name = self.__class__.__name__

    def _str_prefix(self):
        if getattr(self, "pid", 16) == 16:
            player_name = "Global"
        elif self.player and not self.player.name:
            player_name = "Player {0} - ({1})".format(
                self.player.pid, self.player.play_race
            )
        elif self.player:
            player_name = self.player.name
        else:
            player_name = "no name"
        return "{0}\t{1:<15} ".format(Length(seconds=int(self.frame / 16)), player_name)

    def __str__(self):
        return self._str_prefix() + self.name


class GameStartEvent(GameEvent):
    """
    Recorded when the game starts and the frames start to roll. This is a global non-player
    event.
    """

    def __init__(self, frame, pid, data):
        super(GameStartEvent, self).__init__(frame, pid)

        #: ???
        self.data = data


class PlayerLeaveEvent(GameEvent):
    """
    Recorded when a player leaves the game.
    """

    def __init__(self, frame, pid, data):
        super(PlayerLeaveEvent, self).__init__(frame, pid)

        #: ???
        self.data = data


class UserOptionsEvent(GameEvent):
    """
    This event is recorded for each player at the very beginning of the game before the
    :class:`GameStartEvent`.
    """

    def __init__(self, frame, pid, data):
        super(UserOptionsEvent, self).__init__(frame, pid)
        #:
        self.game_fully_downloaded = data["game_fully_downloaded"]

        #:
        self.development_cheats_enabled = data["development_cheats_enabled"]

        #:
        self.multiplayer_cheats_enabled = data["multiplayer_cheats_enabled"]

        #:
        self.sync_checksumming_enabled = data["sync_checksumming_enabled"]

        #:
        self.is_map_to_map_transition = data["is_map_to_map_transition"]

        #:
        self.use_ai_beacons = data["use_ai_beacons"]

        #: Are workers sent to auto-mine on game start
        self.starting_rally = (
            data["starting_rally"] if "starting_rally" in data else None
        )

        #:
        self.debug_pause_enabled = data["debug_pause_enabled"]

        #:
        self.base_build_num = data["base_build_num"]


def create_command_event(frame, pid, data):
    ability_type = data["data"][0]
    if ability_type == "None":
        return BasicCommandEvent(frame, pid, data)

    elif ability_type == "TargetUnit":
        return TargetUnitCommandEvent(frame, pid, data)

    elif ability_type == "TargetPoint":
        return TargetPointCommandEvent(frame, pid, data)

    elif ability_type == "Data":
        return DataCommandEvent(frame, pid, data)


@loggable
class CommandEvent(GameEvent):
    """
    Ability events are generated when ever a player in the game issues a command
    to a unit or group of units. They are split into three subclasses of ability,
    each with their own set of associated data. The attributes listed below are
    shared across all ability event types.

    See :class:`TargetPointCommandEvent`, :class:`TargetUnitCommandEvent`, and
    :class:`DataCommandEvent` for individual details.
    """

    def __init__(self, frame, pid, data):
        super(CommandEvent, self).__init__(frame, pid)

        #: Flags on the command???
        self.flags = data["flags"]

        #: A dictionary of possible ability flags. Flags are:
        #:
        #: * alternate
        #: * queued
        #: * preempt
        #: * smart_click
        #: * smart_rally
        #: * subgroup
        #: * set_autocast,
        #: * set_autocast_on
        #: * user
        #: * data_a
        #: * data_b
        #: * data_passenger
        #: * data_abil_queue_order_id,
        #: * ai
        #: * ai_ignore_on_finish
        #: * is_order
        #: * script
        #: * homogenous_interruption,
        #: * minimap
        #: * repeat
        #: * dispatch_to_other_unit
        #: * target_self
        #:
        self.flag = dict(
            alternate=0x1 & self.flags != 0,
            queued=0x2 & self.flags != 0,
            preempt=0x4 & self.flags != 0,
            smart_click=0x8 & self.flags != 0,
            smart_rally=0x10 & self.flags != 0,
            subgroup=0x20 & self.flags != 0,
            set_autocast=0x40 & self.flags != 0,
            set_autocast_on=0x80 & self.flags != 0,
            user=0x100 & self.flags != 0,
            data_a=0x200 & self.flags != 0,
            data_passenger=0x200 & self.flags != 0,  # alt-name
            data_b=0x400 & self.flags != 0,
            data_abil_queue_order_id=0x400 & self.flags != 0,  # alt-name
            ai=0x800 & self.flags != 0,
            ai_ignore_on_finish=0x1000 & self.flags != 0,
            is_order=0x2000 & self.flags != 0,
            script=0x4000 & self.flags != 0,
            homogenous_interruption=0x8000 & self.flags != 0,
            minimap=0x10000 & self.flags != 0,
            repeat=0x20000 & self.flags != 0,
            dispatch_to_other_unit=0x40000 & self.flags != 0,
            target_self=0x80000 & self.flags != 0,
        )

        #: Flag marking that the command had ability information
        self.has_ability = data["ability"] is not None

        #: Link the the ability group
        self.ability_link = data["ability"]["ability_link"] if self.has_ability else 0

        #: The index of the ability in the ability group
        self.command_index = (
            data["ability"]["ability_command_index"] if self.has_ability else 0
        )

        #: Additional ability data.
        self.ability_data = (
            data["ability"]["ability_command_data"] if self.has_ability else 0
        )

        #: Unique identifier for the ability
        self.ability_id = self.ability_link << 5 | self.command_index

        #: A reference to the ability being used
        self.ability = None

        #: A shortcut to the name of the ability being used
        self.ability_name = ""

        #: The type of ability, one of: None (no target), TargetPoint, TargetUnit, or Data
        self.ability_type = data["data"][0]

        #: The raw data associated with this ability type
        self.ability_type_data = data["data"][1]

        #: Other unit id??
        self.other_unit_id = data["other_unit_tag"]

        #: A reference to the other unit
        self.other_unit = None

    def __str__(self):
        string = self._str_prefix()
        if self.has_ability:
            string += "Ability ({0:X})".format(self.ability_id)
            if self.ability:
                string += " - {0}".format(self.ability.name)
        else:
            string += "Right Click"

        if self.ability_type == "TargetUnit":
            string += "; Target: {0} [{1:0>8X}]".format(
                self.target.name, self.target_unit_id
            )

        if self.ability_type in ("TargetPoint", "TargetUnit"):
            string += "; Location: {0}".format(str(self.location))

        return string


class BasicCommandEvent(CommandEvent):
    """
    Extends :class:`CommandEvent`

    This event is recorded for events that have no extra information recorded.

    Note that like all CommandEvents, the event will be recorded regardless
    of whether or not the command was successful.
    """

    def __init__(self, frame, pid, data):
        super(BasicCommandEvent, self).__init__(frame, pid, data)


class TargetPointCommandEvent(CommandEvent):
    """
    Extends :class:`CommandEvent`

    This event is recorded when ever a player issues a command that targets a location
    and NOT a unit. Commands like Psistorm, Attack Move, Fungal Growth, and EMP fall
    under this category.

    Note that like all CommandEvents, the event will be recorded regardless
    of whether or not the command was successful.
    """

    def __init__(self, frame, pid, data):
        super(TargetPointCommandEvent, self).__init__(frame, pid, data)

        #: The x coordinate of the target. Available for TargetPoint and TargetUnit type events.
        self.x = self.ability_type_data["point"].get("x", 0) / 4096.0

        #: The y coordinate of the target. Available for TargetPoint and TargetUnit type events.
        self.y = self.ability_type_data["point"].get("y", 0) / 4096.0

        #: The z coordinate of the target. Available for TargetPoint and TargetUnit type events.
        self.z = self.ability_type_data["point"].get("z", 0)

        #: The location of the target. Available for TargetPoint and TargetUnit type events
        self.location = (self.x, self.y, self.z)


class TargetUnitCommandEvent(CommandEvent):
    """
    Extends :class:`CommandEvent`

    This event is recorded when ever a player issues a command that targets a unit.
    The location of the target unit at the time of the command is also recorded. Commands like
    Chronoboost, Transfuse, and Snipe fall under this category.

    Note that like all CommandEvents, the event will be recorded regardless
    of whether or not the command was successful.
    """

    def __init__(self, frame, pid, data):
        super(TargetUnitCommandEvent, self).__init__(frame, pid, data)

        #: Flags set on the target unit. Available for TargetUnit type events
        self.target_flags = self.ability_type_data.get("flags", None)

        #: Timer??  Available for TargetUnit type events.
        self.target_timer = self.ability_type_data.get("timer", None)

        #: Unique id of the target unit. Available for TargetUnit type events.
        #: This id can be 0 when the target unit is shrouded by fog of war.
        self.target_unit_id = self.ability_type_data.get("unit_tag", None)

        #: A reference to the targeted unit. When the :attr:`target_unit_id` is
        #: 0 this target unit is a generic, reused fog of war unit of the :attr:`target_unit_type`
        #: with an id of zero. It should not be confused with a real unit.
        self.target_unit = None

        #: Current integer type id of the target unit. Available for TargetUnit type events.
        self.target_unit_type = self.ability_type_data.get("unit_link", None)

        #: Integer player id of the controlling player. Available for TargetUnit type events starting in 19595.
        #: When the targeted unit is under fog of war this id is zero.
        self.control_player_id = self.ability_type_data.get("control_player_id", None)

        #: Integer player id of the player paying upkeep. Available for TargetUnit type events.
        self.upkeep_player_id = self.ability_type_data.get("upkeep_player_id", None)

        #: The x coordinate of the target. Available for TargetPoint and TargetUnit type events.
        self.x = self.ability_type_data["point"].get("x", 0) / 4096.0

        #: The y coordinate of the target. Available for TargetPoint and TargetUnit type events.
        self.y = self.ability_type_data["point"].get("y", 0) / 4096.0

        #: The z coordinate of the target. Available for TargetPoint and TargetUnit type events.
        self.z = self.ability_type_data["point"].get("z", 0)

        #: The location of the target. Available for TargetPoint and TargetUnit type events
        self.location = (self.x, self.y, self.z)


class UpdateTargetPointCommandEvent(TargetPointCommandEvent):
    """
    Extends :class: 'TargetPointCommandEvent'

    This event is generated when the user changes the point of a unit. Appears to happen
    when a unit is moving and it is given a new command. It's possible there are other
    instances of this occurring.

    """

    name = "UpdateTargetPointCommandEvent"


class UpdateTargetUnitCommandEvent(TargetUnitCommandEvent):
    """
    Extends :class:`TargetUnitCommandEvent`

    This event is generated when a TargetUnitCommandEvent is updated, likely due to
    changing the target unit. It is unclear if this needs to be a separate event
    from TargetUnitCommandEvent, but for flexibility, it will be treated
    differently.

    One example of this event occurring is casting inject on a hatchery while
    holding shift, and then shift clicking on a second hatchery.
    """

    name = "UpdateTargetUnitCommandEvent"


class DataCommandEvent(CommandEvent):
    """
    Extends :class:`CommandEvent`

    DataCommandEvent are recorded when ever a player issues a command that has no target. Commands
    like Burrow, SeigeMode, Train XYZ, and Stop fall under this category.

    Note that like all CommandEvents, the event will be recorded regardless
    of whether or not the command was successful.
    """

    def __init__(self, frame, pid, data):
        super(DataCommandEvent, self).__init__(frame, pid, data)

        #: Other target data. Available for Data type events.
        self.target_data = self.ability_type_data.get("data", None)


@loggable
class SelectionEvent(GameEvent):
    """
    Selection events are generated when ever the active selection of the
    player is updated. Unlike other game events, these events can also be
    generated by non-player actions like unit deaths or transformations.

    Starting in Starcraft 2.0.0, selection events targeting control group
    buffers are also generated when control group selections are modified
    by non-player actions. When a player action updates a control group
    a :class:`ControlGroupEvent` is generated.
    """

    def __init__(self, frame, pid, data):
        super(SelectionEvent, self).__init__(frame, pid)

        #: The control group being modified. 10 for active selection
        self.control_group = data["control_group_index"]

        #: Deprecated, use control_group
        self.bank = self.control_group

        #: ???
        self.subgroup_index = data["subgroup_index"]

        #: The type of mask to apply. One of None, Mask, OneIndices, ZeroIndices
        self.mask_type = data["remove_mask"][0]

        #: The data for the mask
        self.mask_data = data["remove_mask"][1]

        #: The unit type data for the new units
        self.new_unit_types = [
            (
                d["unit_link"],
                d["subgroup_priority"],
                d["intra_subgroup_priority"],
                d["count"],
            )
            for d in data["add_subgroups"]
        ]

        #: The unit id data for the new units
        self.new_unit_ids = data["add_unit_tags"]

        # This stretches out the unit types and priorities to be zipped with ids.
        unit_types = chain(
            *[
                [utype] * count
                for (
                    utype,
                    subgroup_priority,
                    intra_subgroup_priority,
                    count,
                ) in self.new_unit_types
            ]
        )
        unit_subgroup_priorities = chain(
            *[
                [subgroup_priority] * count
                for (
                    utype,
                    subgroup_priority,
                    intra_subgroup_priority,
                    count,
                ) in self.new_unit_types
            ]
        )
        unit_intra_subgroup_priorities = chain(
            *[
                [intra_subgroup_priority] * count
                for (
                    utype,
                    subgroup_priority,
                    intra_subgroup_priority,
                    count,
                ) in self.new_unit_types
            ]
        )

        #: The combined type and id information for new units
        self.new_unit_info = list(
            zip(
                self.new_unit_ids,
                unit_types,
                unit_subgroup_priorities,
                unit_intra_subgroup_priorities,
            )
        )

        #: A list of references to units added by this selection
        self.new_units = None

        #: Deprecated, see new_units
        self.objects = None

    def __str__(self):
        if self.new_units:
            return GameEvent.__str__(self) + str([str(u) for u in self.new_units])
        else:
            return GameEvent.__str__(self) + str([str(u) for u in self.new_unit_info])


def create_control_group_event(frame, pid, data):
    update_type = data["control_group_update"]
    if update_type == 0:
        return SetControlGroupEvent(frame, pid, data)
    elif update_type == 1:
        return AddToControlGroupEvent(frame, pid, data)
    elif update_type == 2:
        return GetControlGroupEvent(frame, pid, data)
    elif update_type == 3:
        # TODO: What could this be?!?
        return ControlGroupEvent(frame, pid, data)
    else:
        # No idea what this is but we're seeing update_types of 4 and 5 in 3.0
        return ControlGroupEvent(frame, pid, data)


@loggable
class ControlGroupEvent(GameEvent):
    """
    ControlGroup events are recorded when ever a player action modifies or accesses a control
    group. There are three kinds of events, generated by each of the possible
    player actions:

    * :class:`SetControlGroup` - Recorded when a user sets a control group (ctrl+#).
    * :class:`GetControlGroup` - Recorded when a user retrieves a control group (#).
    * :class:`AddToControlGroup` - Recorded when a user adds to a control group (shift+ctrl+#)

    All three events have the same set of data (shown below) but are interpreted differently.
    See the class entry for details.
    """

    def __init__(self, frame, pid, data):
        super(ControlGroupEvent, self).__init__(frame, pid)

        #: Index to the control group being modified
        self.control_group = data["control_group_index"]

        #: Deprecated, use control_group
        self.bank = self.control_group

        #: Deprecated, use control_group
        self.hotkey = self.control_group

        #: The type of update being performed, 0 (set),1 (add),2 (get)
        self.update_type = data["control_group_update"]

        #: The type of mask to apply. One of None, Mask, OneIndices, ZeroIndices
        self.mask_type = data["remove_mask"][0]

        #: The data for the mask
        self.mask_data = data["remove_mask"][1]


class SetControlGroupEvent(ControlGroupEvent):
    """
    Extends :class:`ControlGroupEvent`

    This event does a straight forward replace of the current control group contents
    with the player's current selection. This event doesn't have masks set.
    """


class AddToControlGroupEvent(SetControlGroupEvent):
    """
    Extends :class:`ControlGroupEvent`

    This event adds the current selection to the control group.
    """


class GetControlGroupEvent(ControlGroupEvent):
    """
    Extends :class:`ControlGroupEvent`

    This event replaces the current selection with the contents of the control group.
    The mask data is used to limit that selection to units that are currently selectable.
    You might have 1 medivac and 8 marines on the control group but if the 8 marines are
    inside the medivac they cannot be part of your selection.
    """


@loggable
class CameraEvent(GameEvent):
    """
    Camera events are generated when ever the player camera moves, zooms, or rotates.
    It does not matter why the camera changed, this event simply records the current
    state of the camera after changing.
    """

    def __init__(self, frame, pid, data):
        super(CameraEvent, self).__init__(frame, pid)

        #: The x coordinate of the center of the camera
        self.x = (data["target"]["x"] if data["target"] is not None else 0) / 256.0

        #: The y coordinate of the center of the camera
        self.y = (data["target"]["y"] if data["target"] is not None else 0) / 256.0

        #: The location of the center of the camera
        self.location = (self.x, self.y)

        #: The distance to the camera target ??
        self.distance = data["distance"]

        #: The current pitch of the camera
        self.pitch = data["pitch"]

        #: The current yaw of the camera
        self.yaw = data["yaw"]

    def __str__(self):
        return self._str_prefix() + "{0} at ({1}, {2})".format(
            self.name, self.x, self.y
        )


@loggable
class ResourceTradeEvent(GameEvent):
    """
    Generated when a player trades resources with another player. But not when fullfulling
    resource requests.
    """

    def __init__(self, frame, pid, data):
        super(ResourceTradeEvent, self).__init__(frame, pid)

        #: The id of the player sending the resources
        self.sender_id = pid

        #: A reference to the player sending the resources
        self.sender = None

        #: The id of the player receiving the resources
        self.recipient_id = data["recipient_id"]

        #: A reference to the player receiving the resources
        self.recipient = None

        #: An array of resources sent
        self.resources = data["resources"]

        #: Amount minerals sent
        self.minerals = self.resources[0] if len(self.resources) >= 1 else None

        #: Amount vespene sent
        self.vespene = self.resources[1] if len(self.resources) >= 2 else None

        #: Amount terrazine sent
        self.terrazine = self.resources[2] if len(self.resources) >= 3 else None

        #: Amount custom resource sent
        self.custom_resource = self.resources[3] if len(self.resources) >= 4 else None

    def __str__(self):
        return self._str_prefix() + " transfer {0} minerals, {1} gas, {2} terrazine, and {3} custom to {4}".format(
            self.minerals,
            self.vespene,
            self.terrazine,
            self.custom_resource,
            self.recipient,
        )


class ResourceRequestEvent(GameEvent):
    """
    Generated when a player creates a resource request.
    """

    def __init__(self, frame, pid, data):
        super(ResourceRequestEvent, self).__init__(frame, pid)

        #: An array of resources sent
        self.resources = data["resources"]

        #: Amount minerals sent
        self.minerals = self.resources[0] if len(self.resources) >= 1 else None

        #: Amount vespene sent
        self.vespene = self.resources[1] if len(self.resources) >= 2 else None

        #: Amount terrazine sent
        self.terrazon = self.resources[2] if len(self.resources) >= 3 else None

        #: Amount custom resource sent
        self.custom_resource = self.resources[3] if len(self.resources) >= 4 else None

    def __str__(self):
        return (
            self._str_prefix()
            + " requests {0} minerals, {1} gas, {2} terrazine, and {3} custom".format(
                self.minerals, self.vespene, self.terrazine, self.custom_resource
            )
        )


class ResourceRequestFulfillEvent(GameEvent):
    """
    Generated when a player accepts a resource request.
    """

    def __init__(self, frame, pid, data):
        super(ResourceRequestFulfillEvent, self).__init__(frame, pid)

        #: The id of the request being fulfilled
        self.request_id = data["request_id"]


class ResourceRequestCancelEvent(GameEvent):
    """
    Generated when a player cancels their resource request.
    """

    def __init__(self, frame, pid, data):
        super(ResourceRequestCancelEvent, self).__init__(frame, pid)

        #: The id of the request being cancelled
        self.request_id = data["request_id"]


class HijackReplayGameEvent(GameEvent):
    """
    Generated when players take over from a replay.
    """

    def __init__(self, frame, pid, data):
        super(HijackReplayGameEvent, self).__init__(frame, pid)

        #: The method used. Not sure what 0/1 represent
        self.method = data["method"]

        #: Information on the users hijacking the game
        self.user_infos = data["user_infos"]
