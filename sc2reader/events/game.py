# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sc2reader.data import Unit
from sc2reader.events.base import Event
from sc2reader.log_utils import loggable

from itertools import chain

@loggable
class GameEvent(Event):
    name = 'GameEvent'
    def __init__(self, frame, pid):
        super(GameEvent, self).__init__(frame, pid)
        self.is_local = (pid != 16)


class GameStartEvent(GameEvent):
    name = 'GameStartEvent'
    def __init__(self, frame, pid, data):
        super(GameStartEvent, self).__init__(frame, pid)


class PlayerLeaveEvent(GameEvent):
    name = 'PlayerLeaveEvent'
    def __init__(self, frame, pid, data):
        super(PlayerLeaveEvent, self).__init__(frame, pid)


class UserOptionsEvent(GameEvent):
    name = 'UserOptionsEvent'
    def __init__(self, frame, pid, data):
        super(UserOptionsEvent, self).__init__(frame, pid)
        #:
        self.game_fully_downloaded = data['game_fully_downloaded']

        #:
        self.development_cheats_enabled = data['development_cheats_enabled']

        #:
        self.multiplayer_cheats_enabled = data['multiplayer_cheats_enabled']

        #:
        self.sync_checksumming_enabled = data['sync_checksumming_enabled']

        #:
        is_map_to_map_transition = data['is_map_to_map_transition']

        #:
        self.use_ai_beacons = data['use_ai_beacons']

        #: Are workers sent to auto-mine on game start
        self.starting_rally = data['starting_rally']

        #:
        self.base_build_num = data['base_build_num']

def create_command_event(frame, pid, data):
    ability_type = data['data'][0]
    if ability_type == 'None':
        return AbilityEvent(frame, pid, data)

    elif ability_type == 'TargetUnit':
        return TargetAbilityEvent(frame, pid, data)

    elif ability_type == 'TargetPoint':
        return LocationAbilityEvent(frame, pid, data)

    elif ability_type == 'Data':
        return SelfAbilityEvent(frame, pid, data)

@loggable
class AbilityEvent(GameEvent):
    name = 'AbilityEvent'
    is_player_action = True
    def __init__(self, frame, pid, data):
        super(AbilityEvent, self).__init__(frame, pid)

        #: Flags on the command???
        self.flags = data['flags']

        #: Flag marking that the command had ability information
        self.has_ability = data['ability'] != None

        #: Link the the ability group
        self.ability_link = data['ability']['ability_link'] if self.has_ability else 0

        #: The index of the ability in the ability group
        self.command_index = data['ability']['ability_command_index'] if self.has_ability else 0

        #: Additional ability data.
        self.ability_data = data['ability']['ability_command_data'] if self.has_ability else 0

        #: Unique identifier for the ability
        self.ability_id = self.ability_link << 5 | self.command_index

        #: A reference to the ability being used
        self.ability = None

        #: A shortcut to the name of the ability being used
        self.ability_name = ''

        #: The type of ability, one of: None (no target), TargetPoint, TargetUnit, or Data
        self.ability_type = data['data'][0]

        ability_type_data = data['data'][1]

        if self.ability_type == 'TargetUnit':
            #: Flags set on the target unit. Available for TargetUnit type events
            self.target_flags = ability_type_data.get('flags',None)

            #: Timer??  Available for TargetUnit type events.
            self.target_timer = ability_type_data.get('timer',None)

            #: Unique id of the target unit. Available for TargetUnit type events.
            self.target_unit_id = ability_type_data.get('unit_tag',None)

            #: A reference to the targetted unit
            self.target_unit = None

            #: Current integer type id of the target unit. Available for TargetUnit type events.
            self.target_unit_type = ability_type_data.get('unit_link',None)

            #: Integer player id of the controlling player. Available for TargetUnit type events starting in 19595.
            self.control_player_id = ability_type_data.get('control_player_id',None)

            #: Integer player id of the player paying upkeep. Available for TargetUnit type events.
            self.upkeep_player_id = ability_type_data.get('upkeep_player_id',None)

        if self.ability_type in ('TargetPoint','TargetUnit'):
            #: The x coordinate of the target. Available for TargetPoint and TargetUnit type events.
            self.x = ability_type_data['point'].get('x',0)/4096.0

            #: The y coordinate of the target. Available for TargetPoint and TargetUnit type events.
            self.y = ability_type_data['point'].get('y',0)/4096.0

            #: The z coordinate of the target. Available for TargetPoint and TargetUnit type events.
            self.z = ability_type_data['point'].get('z',0)

            #: The location of the target. Available for TargetPoint and TargetUnit type events
            self.location = (self.x, self.y, self.z)

        if self.ability_type == 'Data':
            #: Other target data. Available for Data type events.
            self.target_data = ability_type_data.get('data', None)

        #: Other unit id??
        self.other_unit_id = data['other_unit_tag']

        #: A reference to the other unit
        self.other_unit = None

    def load_context(self, replay):
        super(AbilityEvent, self).load_context(replay)

        if not replay.datapack:
            return

        if self.ability_id not in replay.datapack.abilities:
            if not getattr(replay, 'marked_error', None):
                replay.marked_error=True
                self.logger.error(replay.filename)
                self.logger.error("Release String: "+replay.release_string)
                for player in replay.players:
                    self.logger.error("\t"+str(player))

            self.logger.error("{0}\t{1}\tMissing ability {2:X} from {3}".format(self.frame, self.player.name, self.ability_id, replay.datapack.__class__.__name__))

        else:
            self.ability = replay.datapack.abilities[self.ability_id]
            self.ability_name = self.ability.name


        if self.ability_type == 'TargetUnit':
            if self.target_unit_id in replay.objects:
                self.target = replay.objects[self.target_unit_id]
                if not self.target.is_type(self.target_unit_type):
                    replay.datapack.change_type(self.target, self.target_unit_type, self.frame)
            else:
                unit = replay.datapack.create_unit(self.target_unit_id, self.target_unit_type, 0x00, self.frame)
                self.target = unit
                replay.objects[self.target_unit_id] = unit

        if self.other_unit_id in replay.objects:
            self.other_unit = replay.objects[self.other_unit_id]
        elif self.other_unit_id != None:
            print "Other unit {0} not found".format(self.other_unit_id)

    def __str__(self):
        string = self._str_prefix()
        if self.has_ability:
            string += "Ability ({0:X})".format(self.ability_id)
            if self.ability:
                string += " - {0}".format(self.ability.name)
        else:
            string += "Right Click"

        if self.ability_type == 'TargetUnit':
            string += "; Target: {0} [{1:0>8X}]".format(self.target.name, self.target_unit_id)

        if self.ability_type in ('TargetPoint','TargetUnit') :
            string += "; Location: {0}".format(str(self.location))

        return string

class LocationAbilityEvent(AbilityEvent):
    name = 'LocationAbilityEvent'

class TargetAbilityEvent(AbilityEvent):
    name = 'TargetAbilityEvent'

class SelfAbilityEvent(AbilityEvent):
    name = 'SelfAbilityEvent'

@loggable
class SelectionEvent(GameEvent):
    name = 'SelectionEvent'
    is_player_action = True
    def __init__(self, frame, pid, data):
        super(SelectionEvent, self).__init__(frame, pid)

        #: The control group being modified. 10 for active selection
        self.control_group = data['control_group_index']

        #: Deprecated, use control_group
        self.bank = self.control_group

        #: ???
        self.subgroup_index = data['subgroup_index']

        #: The type of mask to apply. One of None, Mask, OneIndices, ZeroIndices
        self.mask_type = data['remove_mask'][0]

        #: The data for the mask
        self.mask_data = data['remove_mask'][1]

        #: The unit type data for the new units
        self.new_unit_types = [(d['unit_link'],d['subgroup_priority'],d['intra_subgroup_priority'],d['count']) for d in data['add_subgroups']]

        #: The unit id data for the new units
        self.new_unit_ids = data['add_unit_tags']

        # This stretches out the unit types and priorities to be zipped with ids.
        unit_types = chain(*[[utype]*count for (utype, subgroup_priority, intra_subgroup_priority, count) in self.new_unit_types])
        unit_subgroup_priorities = chain(*[[subgroup_priority]*count for (utype, subgroup_priority, intra_subgroup_priority, count) in self.new_unit_types])
        unit_intra_subgroup_priorities = chain(*[[intra_subgroup_priority]*count for (utype, subgroup_priority, intra_subgroup_priority, count) in self.new_unit_types])

        #: The combined type and id information for new units
        self.new_unit_info = list(zip(self.new_unit_ids, unit_types, unit_subgroup_priorities, unit_intra_subgroup_priorities))

        #: A list of references to units added by this selection
        self.new_units = None

        #: Deprecated, see new_units
        self.objects = None

    def load_context(self, replay):
        super(SelectionEvent, self).load_context(replay)

        if not replay.datapack:
            return

        units = list()
        for (unit_id, unit_type, subgroup, intra_subgroup) in self.new_unit_info:
            # Hack that defaults viking selection to fighter mode instead of assault
            if replay.versions[1] == 2 and replay.build >= 23925 and unit_type == 71:
                unit_type = 72

            if unit_id in replay.objects:
                unit = replay.objects[unit_id]
                if not unit.is_type(unit_type):
                    replay.datapack.change_type(unit, unit_type, self.frame)
            else:
                unit = replay.datapack.create_unit(unit_id, unit_type, 0x00, self.frame)
                replay.objects[unit_id] = unit

            units.append(unit)

        self.new_units = self.objects = units

    def __str__(self):
        if self.new_units:
            return GameEvent.__str__(self)+str([str(u) for u in self.new_units])
        else:
            return GameEvent.__str__(self)+str([str(u) for u in self.new_unit_info])


def create_control_group_event(frame, pid, data):
    update_type = data['control_group_update']
    if update_type == 0:
        return SetToHotkeyEvent(frame, pid, data)
    elif update_type == 1:
        return AddToHotkeyEvent(frame, pid, data)
    elif update_type == 2:
        return GetFromHotkeyEvent(frame, pid, data)

@loggable
class HotkeyEvent(GameEvent):
    name = 'HotkeyEvent'
    is_player_action = True
    def __init__(self, frame, pid, data):
        super(HotkeyEvent, self).__init__(frame, pid)

        #: Index to the control group being modified
        self.control_group = data['control_group_index']

        #: Deprecated, use control_group
        self.bank = self.control_group

        #: The type of update being performed, 0 (set),1 (add),2 (get)
        self.update_type = data['control_group_update']

        #: The type of mask to apply. One of None, Mask, OneIndices, ZeroIndices
        self.mask_type = data['remove_mask'][0]

        #: The data for the mask
        self.mask_data = data['remove_mask'][1]

class SetToHotkeyEvent(HotkeyEvent):
    name = 'SetToHotkeyEvent'

class AddToHotkeyEvent(HotkeyEvent):
    name = 'AddToHotkeyEvent'

class GetFromHotkeyEvent(HotkeyEvent):
    name = 'GetFromHotkeyEvent'


@loggable
class CameraEvent(GameEvent):
    name = 'CameraEvent'
    def __init__(self, frame, pid, data):
        super(CameraEvent, self).__init__(frame, pid)

        #: The x coordinate of the center? of the camera
        self.x = (data['target']['x'] if data['target'] != None else 0)/256.0

        #: The y coordinate of the center? of the camera
        self.y = (data['target']['y'] if data['target'] != None else 0)/256.0

        #: The location of the center? of the camera
        self.location = (self.x,self.y)

        #: The distance to the camera target ??
        self.distance = data['distance']

        #: The current pitch of the camera
        self.pitch = data['pitch']

        #: The current yaw of the camera
        self.yaw = data['yaw']

    def __str__(self):
        return self._str_prefix() + "{0} at ({1}, {2})".format(self.name, self.x,self.y)


@loggable
class ResourceTradeEvent(GameEvent):
    name = 'ResourceTradeEvent'
    def __init__(self, frame, pid, data):
        super(ResourceTradeEvent, self).__init__(frame, pid)

        #: The id of the player sending the resources
        self.sender_id = pid

        #: A reference to the player sending the resources
        self.sender = None

        #: The id of the player receiving the resources
        self.recipient_id = data['recipient_id']

        #: A reference to the player receiving the resources
        self.recipient = None

        #: An array of resources sent
        self.resources = data['resources']

        #: Amount minerals sent
        self.minerals = self.resources[0] if len(self.resources) >= 1 else None

        #: Amount vespene sent
        self.vespene = self.resources[1] if len(self.resources) >= 2 else None

        #: Amount terrazine sent
        self.terrazon = self.resources[2] if len(self.resources) >= 3 else None

        #: Amount custom resource sent
        self.custom_resource = self.resources[3] if len(self.resources) >= 4 else None

    def __str__(self):
        return self._str_prefix() + " transfer {0} minerals, {1} gas, {2} terrazine, and {3} custom to {4}" % (self.minerals, self.vespene, self.terrazine, self.custom, self.reciever)

    def load_context(self, replay):
        super(ResourceTradeEvent, self).load_context(replay)
        self.sender = self.player
        self.recipient = replay.players[self.recipient_id]


class ResourceRequestEvent(GameEvent):
    name = 'ResourceRequestEvent'
    def __init__(self, frame, pid, data):
        super(ResourceRequestEvent, self).__init__(frame, pid)

        #: An array of resources sent
        self.resources = data['resources']

        #: Amount minerals sent
        self.minerals = self.resources[0] if len(self.resources) >= 1 else None

        #: Amount vespene sent
        self.vespene = self.resources[1] if len(self.resources) >= 2 else None

        #: Amount terrazine sent
        self.terrazon = self.resources[2] if len(self.resources) >= 3 else None

        #: Amount custom resource sent
        self.custom_resource = self.resources[3] if len(self.resources) >= 4 else None

    def __str__(self):
        return self._str_prefix() + " requests {0} minerals, {1} gas, {2} terrazine, and {3} custom" % (self.minerals, self.vespene, self.terrazine, self.custom)


class ResourceRequestFulfillEvent(GameEvent):
    name = 'ResourceRequestFulfillEvent'
    def __init__(self, frame, pid, data):
        super(ResourceRequestFulfillEvent, self).__init__(frame, pid)

        #: The id of the request being fulfilled
        self.request_id = data['request_id']


class ResourceRequestCancelEvent(GameEvent):
    name = 'ResourceRequestCancelEvent'
    def __init__(self, frame, pid, data):
        super(ResourceRequestCancelEvent, self).__init__(frame, pid)

        #: The id of the request being cancelled
        self.request_id = data['request_id']
