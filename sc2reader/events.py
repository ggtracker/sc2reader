from __future__ import absolute_import

from sc2reader.utils import Length, LITTLE_ENDIAN
from sc2reader.data.utils import DataObject
from sc2reader import log_utils

class Event(object):
    def __init__(self, frame, pid):
        self.logger = log_utils.get_logger(self.__class__)
        self.pid = pid
        self.frame = frame
        self.second = frame >> 4
        self.time = Length(seconds=self.second)
        if not hasattr(self, 'name'):
            self.name = self.__class__.__name__

    def load_context(self, replay):
        if self.pid != 16:
            self.player = replay.person[self.pid]

class GameEvent(Event):
    """Abstract Event Type, should not be directly instanciated"""
    def __init__(self, frame, pid, event_type, event_code):
        super(GameEvent, self).__init__(frame, pid)

        self.type = event_type
        self.code = event_code
        self.is_local = (pid != 16)

        self.is_init = (event_type == 0x00)
        self.is_player_action = (event_type == 0x01)
        self.is_camera_movement = (event_type == 0x03)
        self.is_unknown = (event_type == 0x02 or event_type == 0x04 or event_type == 0x05)

    def _str_prefix(self):
        player_name = self.player.name if self.is_local else "Global"
        return "%s\t%-15s " % (Length(seconds=int(self.frame/16)), player_name)

    def __str__(self):
        return self._str_prefix() + self.name

#############################################3
# Message Events
#########################

class MessageEvent(Event):
    def __init__(self, frame, pid, flags):
        super(MessageEvent, self).__init__(frame, pid)
        self.flags=flags

class ChatEvent(MessageEvent):
    def __init__(self, frame, pid, flags, buffer):
        super(ChatEvent, self).__init__(frame, pid, flags)

        # A flag set without the 0x80 bit set is a player message. Messages
        # store a target (allies or all) as well as the message text.
        extension = (flags & 0x18) << 3
        self.target = flags & 0x03
        self.text = buffer.read_chars(buffer.read_byte() + extension)
        self.to_all = (self.target == 0)
        self.to_allies = (self.target == 2)

class PacketEvent(MessageEvent):
    def __init__(self, frame, pid, flags, buffer):
        super(PacketEvent, self).__init__(frame, pid, flags)

        # The 0x80 flag marks a network packet. I believe these mark packets
        # send over the network to establish latency or connectivity.
        self.data = buffer.read_chars(4)

class PingEvent(MessageEvent):
    def __init__(self, frame, pid, flags, buffer):
        super(PingEvent, self).__init__(frame, pid, flags)

        # The 0x83 flag indicates a minimap ping and contains the x and
        # y coordinates of that ping as the payload.
        self.x=buffer.read_int(LITTLE_ENDIAN)
        self.y=buffer.read_int(LITTLE_ENDIAN)


#############################################3
# Game Events
#########################

class UnknownEvent(GameEvent):
    pass

class PlayerJoinEvent(GameEvent):
	pass

class GameStartEvent(GameEvent):
    pass

class PlayerLeaveEvent(GameEvent):
	pass

class CameraMovementEvent(GameEvent):
    pass

class PlayerActionEvent(GameEvent):
    pass

class ResourceTransferEvent(PlayerActionEvent):
    def __init__(self, frames, pid, type, code, target, minerals, vespene):
        super(ResourceTransferEvent, self).__init__(frames, pid, type, code)
        self.sender = pid
        self.reciever = target
        self.minerals = minerals
        self.vespene = vespene

    def __str__(self):
        return self._str_prefix() + "%s transfer %d minerals and %d gas to %s" % (self.sender, self.minerals, self.vespene, self.reciever)

    def load_context(self, replay):
        super(ResourceTransferEvent, self).load_context(replay)
        self.sender = replay.player[self.sender]
        self.reciever = replay.player[self.reciever]

class AbilityEvent(PlayerActionEvent):
    def __init__(self, framestamp, player, type, code, ability):
        super(AbilityEvent, self).__init__(framestamp, player, type, code)
        self.ability_code = ability
        self.ability_name = 'Uknown'

    def load_context(self, replay):
        super(AbilityEvent, self).load_context(replay)

        if self.ability_code not in replay.datapack.abilities:
            if not getattr(replay, 'marked_error', None):
                replay.marked_error=True
                self.logger.error(replay.filename)
                self.logger.error("Release String: "+replay.release_string)
                for player in replay.players:
                    self.logger.error("\t"+str(player))
            self.logger.error("{0}\t{1}\tMissing ability {2} from {3}".format(self.frame, self.player.name, hex(self.ability_code), replay.datapack.__class__.__name__))

        else:
            self.ability_name = replay.datapack.abilities[self.ability_code]


    def __str__(self):
        if not self.ability_code:
            return self._str_prefix() + "Move"
        else:
            return self._str_prefix() + "Ability (%s) - %s" % (hex(self.ability_code), self.ability_name)

class TargetAbilityEvent(AbilityEvent):
    def __init__(self, framestamp, player, type, code, ability, target):
        super(TargetAbilityEvent, self).__init__(framestamp, player, type, code, ability)
        self.target = None
        self.target_id, self.target_type = target
        #Forgot why we have to munge this
        self.target_type = self.target_type << 8 | 0x01


    def load_context(self, replay):
        super(TargetAbilityEvent, self).load_context(replay)
        uid = (self.target_id, self.target_type)

        if uid in replay.objects:
            self.target = replay.objects[uid]

        else:
            if self.target_type not in replay.datapack.types:
                self.target = None
            else:
                unit_class = replay.datapack.types[self.target_type]
                self.target = unit_class(self.target_id)
                replay.objects[uid] = self.target

    def __str__(self):
        if self.target:
            if isinstance(self.target, DataObject):
                target = "{0} [{1:0>8X}]".format(self.target.name, self.target.id)
            else:
                target = "{0:X} [{1:0>8X}]".format(self.target[1], self.target[0])
        else:
            target = "NONE"

        return AbilityEvent.__str__(self) + "; Target: {0}".format(target)

class LocationAbilityEvent(AbilityEvent):
    def __init__(self, framestamp, player, type, code, ability, location):
        super(LocationAbilityEvent, self).__init__(framestamp, player, type, code, ability)
        self.location = location

    def __str__(self):
        return AbilityEvent.__str__(self) + "; Location: %s" % str(self.location)

class SelfAbilityEvent(AbilityEvent):
    pass

class HotkeyEvent(PlayerActionEvent):
    def __init__(self, framestamp, player, type, code, hotkey, deselect):
        super(HotkeyEvent, self).__init__(framestamp, player, type, code)
        self.hotkey = hotkey
        self.deselect = deselect

class SetToHotkeyEvent(HotkeyEvent):
    pass

class AddToHotkeyEvent(HotkeyEvent):
    pass

class GetFromHotkeyEvent(HotkeyEvent):
    pass

class SelectionEvent(PlayerActionEvent):
    def __init__(self, framestamp, player, type, code, bank, objects, deselect):
        super(SelectionEvent, self).__init__(framestamp, player, type, code)
        self.bank = bank
        self.objects = objects
        self.deselect = deselect

    def load_context(self, replay):
        super(SelectionEvent, self).load_context(replay)

        if not replay.datapack:
            return

        objects = list()
        data = replay.datapack
        for (obj_id, obj_type) in self.objects:
            if obj_type not in data.types:
                msg = "Unit Type {0} not found in {1}"
                self.logger.error(msg.format(hex(obj_type), data.__class__.__name__))
                objects.append(DataObject(0x0))

            else:
                if (obj_id, obj_type) not in replay.objects:
                    obj = data.types[obj_type](obj_id)
                    replay.objects[(obj_id,obj_type)] = obj
                else:
                    obj = replay.objects[(obj_id,obj_type)]

                objects.append(obj)

        self.objects = objects