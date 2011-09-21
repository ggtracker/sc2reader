from itertools import chain
from collections import defaultdict

from .objects import *
from .utils import BIG_ENDIAN,LITTLE_ENDIAN
from .exceptions import ParseError

class SetupParser(object):
    def parse_join_event(self, buffer, frames, type, code, pid):
        return PlayerJoinEvent(frames, pid, type, code)
        
    def parse_start_event(self, buffer, frames, type, code, pid):
        return GameStartEvent(frames, pid, type, code)

class ActionParser(object):
    def parse_leave_event(self, buffer, frames, type, code, pid):
        return PlayerLeaveEvent(frames, pid, type, code)

    def parse_ability_event(self, buffer, frames, type, code, pid):
        buffer.skip(7)
        switch = buffer.read_byte()
        if switch in (0x30,0x50):
            buffer.read_byte()
        buffer.skip(24)
        return AbilityEvent(frames, pid, type, code, None)

    def parse_selection_event(self, buffer, frames, type, code, pid):
        bank = code >> 4
        selFlags = buffer.read_byte()
        dsuCount = buffer.read_byte()
        buffer.read(bits=dsuCount)

        # <count> (<type_id>, <count>,)*
        object_types = [ (buffer.read_object_type(read_modifier=True), buffer.read_byte(), ) for i in range(buffer.read_byte()) ]
        # <count> (<object_id>,)*
        object_ids = [ buffer.read_object_id() for i in range(buffer.read_byte()) ]

        # repeat types count times
        object_types = chain(*[[object_type,]*count for (object_type, count) in object_types])
        objects = zip(object_ids, object_types)

        return SelectionEvent(frames, pid, type, code, bank, objects, None)

    def parse_hotkey_event(self, buffer, frames, type, code, pid):
        hotkey = code >> 4
        action, read = buffer.shift(2), buffer.shift(1)

        if read:
            mask = buffer.read(bits=buffer.read_byte())
            overlay = lambda a: Selection.mask(a, mask)
        else:
            overlay = None

        if action == 0:
            return SetToHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        elif action == 1:
            return AddToHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        elif action == 2:
            return GetHotkeyEvent(frames, pid, type, code, hotkey, overlay)

    def parse_transfer_event(self, buffer, frames, type, code, pid):
        def read_resource(buffer):
            block = buffer.read_int(BIG_ENDIAN)
            base, multiplier, extension = block >> 8, block & 0xF0, block & 0x0F
            return base*multiplier+extension

        target = code >> 4
        buffer.skip(1) #Always 84
        minerals,vespene = read_resource(buffer), read_resource(buffer)
        buffer.skip(8)

        return ResourceTransferEvent(frames, pid, type, code, target, minerals, vespene)

class ActionParser_16561(ActionParser):
        
    def parse_selection_event(self, buffer, frames, type, code, pid):
        bank = code >> 4
        first = buffer.read_byte() # TODO ?

        deselect_flag = buffer.shift(2)
        if deselect_flag == 0x01: # deselect deselect mask
            mask = buffer.read_bitmask()
            deselect = lambda a: Selection.mask(a, mask)
        elif deselect_flag == 0x02: # deselect mask
            indexes = [buffer.read_byte() for i in range(buffer.read_byte())]
            deselect = lambda a: Selection.deselect(a, indexes)
        elif deselect_flag == 0x03: # replace mask
            indexes = [buffer.read_byte() for i in range(buffer.read_byte())]
            deselect = lambda a: Selection.replace(a, indexes)
        else:
            deselect = None
            
        # <count> (<type_id>, <count>,)*
        object_types = [ (buffer.read_object_type(read_modifier=True), buffer.read_byte(), ) for i in range(buffer.read_byte()) ]
        # <count> (<object_id>,)*
        object_ids = [ buffer.read_object_id() for i in range(buffer.read_byte()) ]

        # repeat types count times
        object_types = chain(*[[object_type,]*count for (object_type, count) in object_types])
        objects = zip(object_ids, object_types)

        return SelectionEvent(frames, pid, type, code, bank, objects, deselect)

    def parse_hotkey_event(self, buffer, frames, type, code, pid):
        hotkey = code >> 4
        action, mode = buffer.shift(2), buffer.shift(2)

        if mode == 1: # deselect overlay mask
            mask = buffer.read_bitmask()
            overlay = lambda a: Selection.mask(a, mask)
        elif mode == 2: # deselect mask
            indexes = [buffer.read_byte() for i in range(buffer.read_byte())]
            overlay = lambda a: Selection.deselect(a, indexes)
        elif mode == 3: # replace mask
            indexes = [buffer.read_byte() for i in range(buffer.read_byte())]
            overlay = lambda a: Selection.replace(a, indexes)
        else:
            overlay = None

        if action == 0:
            return SetToHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        elif action == 1:
            return AddToHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        elif action == 2:
            return GetHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        else:
            raise ParseError("Hotkey Action '{0}' unknown")

    def command_card(self, buffer, frames, type, code, pid, flag, atype):
        ability = buffer.read_short()

        if flag in (0x29, 0x19, 0x14, 0x0c): # cancels
            # creation autoid number / object id
            ability = ability << 8 | buffer.read_byte()
            created_id = buffer.read_object_id()
            # TODO : expose the id
            return AbilityEvent(frames, pid, type, code, ability)

        else:
            ability_flags = buffer.shift(6)
            ability = ability << 8 | ability_flags

            if ability_flags & 0x10:
                # ability(3), coordinates (4), ?? (4)
                location = buffer.read_coordinate()
                buffer.skip(4)
                return LocationAbilityEvent(frames, pid, type, code, ability, location)

            elif ability_flags & 0x20:
                # ability(3), object id (4),  object type (2), ?? (10)
                code = buffer.read_short() # code??
                obj_id = buffer.read_object_id()
                obj_type = buffer.read_object_type()
                target = (obj_id, obj_type,)
                switch = buffer.read_byte()
                buffer.read_hex(9)
                return TargetAbilityEvent(frames, pid, type, code, ability, target)

            else:
                return AbilityEvent(frames,pid,type,code,ability)

    def location_move(self, buffer, frames, type, code, pid, flag, atype):
        h = buffer.read_hex(2)
        hinge = buffer.read_byte()
        if hinge & 0x20:
            "\t%s - %s" % (hex(hinge),buffer.read_hex(9))
        elif hinge & 0x40:
            "\t%s - %s" % (hex(hinge),buffer.read_hex(18))
        elif hinge < 0x10:
            pass
        else:
            pass

        return UnknownLocationAbilityEvent(frames, pid, type, code, None)

    def right_click_target(self, buffer, frames, type, code, pid, flag, atype):
        # ability (2), object id (4), object type (2), ?? (10)
        ability = buffer.read_short()
        obj_id = buffer.read_object_id()
        obj_type = buffer.read_object_type()
        target = (obj_id, obj_type,)
        buffer.skip(10)
        return TargetAbilityEvent(frames, pid, type, code, ability, target)

    def right_click_move(self, buffer, frames, type, code, pid, flag, atype):
        #10 bytes total, coordinates have a different format?
        #X coordinate definitely is the first byte, with (hopefully) y next
        location = buffer.read_coordinate()
        buffer.skip(5)
        return LocationAbilityEvent(frames, pid, type, code, None, location)

    def parse_ability_event(self, buffer, frames, type, code, pid):
        flag = buffer.read_byte()
        atype = buffer.read_byte()

        if atype & 0x20: # command card
            return self.command_card(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x40: # location/move
            if flag == 0x08:
                return self.right_click_move(buffer, frames, type, code, pid, flag, atype)
            elif flag in (0x04,0x05,0x07):
                return self.location_move(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x80: # right-click on target?
            return self.right_click_target(buffer, frames, type, code, pid, flag, atype)

            raise ParseError()


class ActionParser_18574(ActionParser_16561):

    def parse_ability_event(self, buffer, frames, type, code, pid):
        """Moves the right click move to the top level"""
        flag = buffer.read_byte()
        atype = buffer.read_byte()

        if atype & 0x20: # command card
            return self.command_card(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x40: # location/move ??
            return self.location_move(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x80: # right-click on target?
            return self.right_click_target(buffer, frames, type, code, pid, flag, atype)
        elif atype < 0x10: #new to patch 1.3.3, location now??
            return self.right_click_move(buffer, frames, type, code, pid, flag, atype)

        raise ParseError()

class ActionParser_19595(ActionParser_18574):
    def location_move(self, buffer, frames, type, code, pid, flag, atype):
        h = buffer.read_hex(2)
        hinge = buffer.read_byte()
        if hinge & 0x20:
            "\t%s - %s" % (hex(hinge),buffer.read_hex(9))
        elif hinge & 0x40:
            # extra byte
            "\t%s - %s" % (hex(hinge),buffer.read_hex(19))
        elif hinge < 0x10:
            pass
        else:
            pass

        return UnknownLocationAbilityEvent(frames, pid, type, code, None)

    def right_click_target(self, buffer, frames, type, code, pid, flag, atype):
        # ability (2), object id (4), object type (2), ?? (10)
        ability = buffer.read_byte() << 8 | buffer.read_byte()
        obj_id = buffer.read_object_id()
        obj_type = buffer.read_object_type()
        target = (obj_id, obj_type,)
        # extra byte
        buffer.skip(11)
        return TargetAbilityEvent(frames, pid, type, code, ability, target)

class Unknown2Parser(object):
    def parse_0206_event(self, buffer, frames, type, code, pid):
        buffer.skip(8)
        return UnknownEvent(frames, pid, type, code)
        
    def parse_0207_event(self, buffer, frames, type, code, pid):
        buffer.skip(4)
        return UnknownEvent(frames, pid, type, code)
        
    def parse_020E_event(self, buffer, frames, type, code, pid):
        buffer.skip(4)
        return UnknownEvent(frames, pid, type, code)
        
class CameraParser(object):
    def parse_camera87_event(self, buffer, frames, type, code, pid):
        #There are up to 3 peices to read depending on values encountered
        for i in range(3):
            if buffer.read_int(BIG_ENDIAN) & 0xF0 == 0:
                break

        return CameraMovementEvent(frames, pid, type, code)

    def parse_cameraX8_event(self, buffer, frames, type, code, pid):
        # No idea why these two cases are ever so slightly different. There
        # must be a pattern in here somewhere that I haven't found yet.
        #
        # TODO: Find out why we occassionally shift by 2 instead of 3
        if code == 0x88:
            flags = buffer.read_byte()
            extra = buffer.read_byte()
            buffer.skip( (code & 0xF0 | flags & 0x0F) << 2 )

        else:
            flags = buffer.read_byte()
            extra = buffer.read_byte()
            buffer.skip( (code & 0xF0 | flags & 0x0F) << 3 )

        return CameraMovementEvent(frames, pid, type, code)
        
    def parse_cameraX1_event(self, buffer, frames, type, code, pid):
        #Get the X and Y,  last byte is also a flag
        buffer.skip(3)
        flag = buffer.read_byte()

        if flag & 0x10 != 0:
            buffer.skip(1)
            flag = buffer.read_byte()
        if flag & 0x20 != 0:
            buffer.skip(1)
            flag = buffer.read_byte()
        if flag & 0x40 != 0:
            buffer.skip(2)

        return CameraMovementEvent(frames, pid, type, code)

    def parse_camera0A_event(self, buffer, frames, type, code, pid):
        # Not really sure wtf is up with this event
        # I've only seen it a dozen times. Always (?) a custom game
        for i in range(6):
            if not buffer.read_int(BIG_ENDIAN) & 0xF0:
                break

        return CameraMovementEvent(frames, pid, type, code)
        
class Unknown4Parser(object):
    def parse_0416_event(self, buffer, frames, type, code, pid):
        buffer.skip(24)
        return UnknownEvent(frames, pid, type, code)
        
    def parse_04C6_event(self, buffer, frames, type, code, pid):
        buffer.skip(16)
        return UnknownEvent(frames, pid, type, code)
        
    def parse_0487_event(self, buffer, frames, type, code, pid):
        buffer.skip(4) #Always 00 00 00 01 ??
        return UnknownEvent(frames, pid, type, code)
        
    def parse_0400_event(self, buffer, frames, type, code, pid):
        buffer.skip(10)
        return UnknownEvent(frames, pid, type, code)
        
    def parse_04X2_event(self, buffer, frames, type, code, pid):
        buffer.skip(2)
        return UnknownEvent(frames, pid, type, code)
        
    def parse_0488_event(self, buffer, frames, type, code, pid):
        buffer.skip(4) #Always 00 00 00 01 ?? or 00 00 00 03
        return UnknownEvent(frames, pid, type, code)
        
    def parse_04XC_event(self, buffer, frames, type, code, pid):
        #no body
        return UnknownEvent(frames, pid, type, code)
