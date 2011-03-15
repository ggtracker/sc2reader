from sc2reader.objects import PlayerJoinEvent, GameStartEvent, UnknownEvent, PlayerLeaveEvent, AbilityEvent, SelectionEvent, ResourceTransferEvent, HotkeyEvent, CameraMovementEvent



class Parser(object):
    def load(self, bytes, frames, event_type, event_code, pid):
        raise NotYetImplemented("This should return a processed event!")

################################################
# Initialization Event Parsers
################################################
class PlayerJoinEventParser(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        return PlayerJoinEvent(frames, event_type, event_code, pid)
    
class GameStartEventParser(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        return GameStartEvent(frames, event_type, event_code, pid)

#################################################
# Player Action Parsers
#################################################
class PlayerLeaveEventParser(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        return PlayerLeaveEvent(frames, event_type, event_code, pid)
        
class AbilityEventParser(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = AbilityEvent(frames, event_type, event_code, pid)
        bytes.skip(4)
        event.ability = bytes.get_big_8() << 16 | bytes.get_big_8() << 8 | bytes.get_big_8()
        req_target = bytes.get_big_8()
        
        bytes.skip(24)
        
        #In certain cases we need an extra byte
        if req_target == 0x30 or req_target == 0x05:
            bytes.skip(1)
            
        return event
            
class AbilityEventParser_16561(AbilityEventParser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = AbilityEvent(frames, event_type, event_code, pid)
        
        first, atype = (bytes.get_big_8(), bytes.get_big_8())
        event.ability = bytes.get_big_8() << 16 | bytes.get_big_8() << 8 | (bytes.get_big_8() & 0x3F)
                
        if atype == 0x20 or atype == 0x22:
            event.name = 'unitability'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr, self.player, hex(atype), event.abilitystr)
            if event.ability & 0xFF > 0x07:
                if first == 0x29 or first == 0x19:
                    bytes.skip(4)
                else:
                    bytes.skip(9)
                    if event.ability & 0x20 != 0:
                        bytes.skip(9)
                        
        elif atype == 0x48 or atype == 0x4A:
            #identifies target point
            event.name = 'targetlocation'
            #print "Time %s - Player %s issues location target" % (self.timestr, self.player)
            bytes.skip(7)
        
        elif atype == 0x88 or atype == 0x8A:
            #identifies the target unit
            event.name = 'targetunit'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr, self.player, hex(atype), abilitystr)
            bytes.skip(15)
        
        else:
            raise TypeError("Ability type %s is unknown at location %s" % (hex(atype), event.location))
            
        return event
            

class SelectionEventParser(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = SelectionEvent(frames, event_type, event_code, pid)
        select_flags, deselect_count = bytes.get_big_8(), bytes.get_big_8()
        
        if deselect_count > 0:
            #Skip over the deselection bytes
            bytes.skip(deselect_count >> 3)
        
        #Find the bits left over
        extras = deselect_count & 0x07
        if extras == 0:
            #This is easy when we are byte aligned
            unit_type_count = bytes.get_big_8()
            
            for i in range(0, unit_type_count):
                unit_type_block = bytes.get_big_32()
                unit_type, unit_count = unit_type_block >> 8, unit_type_block & 0xFF
            totalUnits = bytes.get_big_8()
            
            for i in range(0, totalUnits):
                unit_id, use_count = bytes.get_big_16(), bytes.get_big_16()
        else:
            #We're not byte aligned, so need do so some bit shifting
            #This seems like 1000% wrong to me, but its what the people
            #at phpsc2replay think it is so I'll deal for now
            tail_mask = 0xFF >> (8-extras)
            head_mask = ~tail_mask & 0xFF
            w_tail_mask = 0xFF >> extras
            w_head_mask = ~w_tail_mask & 0xFF
            
            prev_byte, next_byte = bytes.get_big_8(),  bytes.get_big_8()
            
            unit_type_count = prev_byte & head_mask | next_byte & tail_mask
            
            for i in range(0, unit_type_count):
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_type = prev_byte & head_mask | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_type = unit_type << 8 | (prev_byte & w_tail_mask) << extras | next_byte & tail_mask
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_type = unit_type << 8 | (prev_byte & head_mask) << extras | next_byte & tail_mask
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_count = prev_byte & head_mask | next_byte & tail_mask
                
            prev_byte, next_byte = next_byte, bytes.get_big_8()
            totalUnits = prev_byte & head_mask | next_byte & tail_mask
            
            for i in range(0, totalUnits):
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_id = prev_byte & head_mask | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_id = unit_id << 8 | prev_byte & w_tail_mask << extras | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_id = unit_id << 8 | prev_byte & w_tail_mask << extras | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_8()
                unit_id = unit_id << 8 | prev_byte & w_tail_mask << extras | next_byte & tail_mask
        return event
            
class SelectionEventParser_16561(SelectionEventParser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = SelectionEvent(frames, event_type, event_code, pid)
        select_flags, deselect_type = bytes.get_big_8(), bytes.get_big_8()
        
        #No deselection to do here
        if deselect_type & 3 == 0:
            last_byte = deselect_type #This is the last byte
            mask = 0x03 #default mask of '11' applies
            
        #deselection by bit counted indicators
        elif deselect_type & 3 == 1:
            #use the 6 left bits on top and the 2 right bits on bottom
            count_byte = bytes.get_big_8()
            deselect_count = deselect_type & 0xFC | count_byte & 0x03
            
            #If we don't need extra bytes then this is the last one
            if deselect_count <= 6:
                last_byte = count_byte
            else:
                #while count > 6 we need to eat into more bytes because
                #we only have 6 bits left in our current byte
                while deselect_count > 6:
                    last_byte = bytes.get_big_8()
                    deselect_count -= 8
            
            #If we exactly use the whole byte
            if deselect_count == 6:
                mask = 0xFF #no mask is needed since we are even
                
            #Because we went bit by bit the mask is different so we
            #take the deselect bits used on the last_byte,  add the two
            #bits left bits we've carried down, we need a mask that long
            else:
                mask = (1 << (deselect_count+2)) - 1
            
        #deselect by byte,I think (deselect_type & 3 == 3) is deselect all
        #and as such probably has a deselect_count always == 0,  not sure though
        else:
            #use the 6 left bits on top and the 2 right bits on bottom
            count_byte = bytes.get_big_8()
            deselect_count = deselect_type & 0xFC | count_byte & 0x03
            
            #If the count is zero than that byte is the last one
            if deselect_count == 0:
                last_byte = count_byte
                
            #Because this count is in bytes we can just read that many bytes
            #we need to save the last one though because we need the bits
            else:
                bytes.skip(deselect_count-1)
                last_byte = bytes.get_big_8()
            
            mask = 0x03 #default mask of '11' applies
        
        combine = lambda last, next: last & (0xFF-mask) | next & mask
        
        unit_ids = list()    
        unit_types = dict()
        
        #Get the number of selected unit types
        next_byte = bytes.get_big_8()
        numunit_types = combine(last_byte, next_byte)
        
        #Read them all into a dictionary for later
        for i in range(0, numunit_types):
            #Build the unit_type_id over the next 3 bytes
            byte_list = list()
            for i in range(0, 3):
                #Swap the bytes, grab another, and combine w/ the mask
                last_byte, next_byte = next_byte, bytes.get_big_8()
                byte_list.append( combine(last_byte, next_byte) )
            unit_type_id = byte_list[0] << 16 | byte_list[1] << 8 | byte_list[2]
            
            #Get the count for that type in the next byte
            last_byte, next_byte = next_byte, bytes.get_big_8()
            unit_type_count = combine(last_byte, next_byte)
            
            #Store for later
            unit_types[unit_type_id] = unit_type_count
        
        #Get total unit count
        last_byte, next_byte = next_byte, bytes.get_big_8()
        unit_count = combine(last_byte, next_byte)
        
        #Pull all the unit_ids in for later
        for i in range(0, unit_count):            
            #build the unit_id over the next 4 bytes
            byte_list = list()
            for i in range(0, 4):
                last_byte, next_byte = next_byte, bytes.get_big_8()
                byte_list.append( combine(last_byte, next_byte) )
            
            #The first 2 bytes are unique and the last 2 mark reusage count
            unit_id = byte_list[0] << 24 | byte_list[1] << 16 | byte_list[2] << 8 | byte_list[3]
            unit_ids.append( unit_id )
            
        return event
        
class HotkeyEventParser(Parser):
    def load_set_hotkey(self, event, bytes, first):
        event.name = 'set_hotkey'
    
    def load_get_hotkey(self, event, bytes, first):
        event.name = 'get_hotkey'
    
    def load_get_hotkey_changed(self, event, bytes, first):
        event.name = 'get_hotkey_changed'
        extras = first >> 3
        second = bytes.get_big_8()
        bytes.skip(extras)
        
        if first & 0x04: 
            bytes.skip(1)
            if second & 0x06 == 0x06:
                bytes.skip(1)
    
    def load_shift_set_hotkey(self, event, bytes, first):
        event.name = 'shift_set_hotkey'
    
    def load(self, bytes, frames, event_type, event_code, pid):
        event = HotkeyEvent(frames, event_type, event_code, pid)
        event.hotkey = str(event.code >> 4)
        #print "Time %s - Player %s is using hotkey %s" % (self.timestr, self.player, eventCode >> 4)
        first = bytes.get_big_8()
        
        if   first == 0x00: self.load_set_hotkey(event, bytes, first)
        elif first == 0x01: self.load_shift_set_hotkey(event, bytes, first)
        elif first == 0x02: self.load_get_hotkey(event, bytes, first)
        elif first >= 0x03: self.load_get_hotkey_changed(event, bytes, first)
        else: pass
        
        return event
    
class HotkeyEventParser_16561(HotkeyEventParser):
    def load_get_hotkey_changed(self, event, bytes, first):
        event.name = 'get_hotkey_changed'
        second = bytes.get_big_8()
        
        if first & 0x08:
            bytes.skip(second & 0x0F)
        else:  
            extras = first >> 3
            bytes.skip(extras)
            if extras == 0:
                if second & 0x07 > 0x04:
                    bytes.skip(1)
                if second & 0x08 != 0:
                    bytes.skip(1)
            else:
                if first & 0x04 != 0:
                    if second & 0x07 > 0x04:
                        bytes.skip(1)
                    if second & 0x08 != 0:
                        bytes.skip(1)
                        
class ResourceTransferEventParser(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = ResourceTransferEvent(frames, event_type, event_code, pid)
        
        bytes.skip(1)  # 84
        event.sender = event.player
        event.receiver = event.code >> 4
        
        #I might need to shift these two things to 19, 11, 3 for first 3 shifts
        event.minerals = bytes.get_big_8() << 20 | bytes.get_big_8() << 12 | bytes.get_big_8() << 4 | bytes.get_big_8() >> 4
        event.gas = bytes.get_big_8() << 20 | bytes.get_big_8() << 12 | bytes.get_big_8() << 4 | bytes.get_big_8() >> 4
        
        #unknown extra stuff
        bytes.skip(2)
        
        return event

class ResourceTransferEventParser_16561(ResourceTransferEventParser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = ResourceTransferEvent(frames, event_type, event_code, pid)
        
        #Always 17 bytes long
        event.sender = event.player
        event.reciever = event.code >> 4
        
        bytes.get_big_8() #Always 84
        
        #Minerals and Gas are encoded the same way
        resource_block =  bytes.get_big_32()
        base, extension = resource_block >> 8, resource_block & 0xFF
        event.minerals = base*(extension >> 4)+ (extension & 0x0F)
        resource_block =  bytes.get_big_32()
        base, extension = resource_block >> 8, resource_block & 0xFF
        event.gas = base*(extension >> 4)+ (extension & 0x0F)
        
        #Another 8 bytes that don't make sense
        bytes.skip(8)
        
        return event
        
        
#######################################################
# Camera Movement Event Parsers
#######################################################
class CameraMovementEventParser_87(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = CameraMovementEvent(frames, event_type, event_code, pid)
        event.name = 'cameramovement_87'
        bytes.skip(8)
        return event

class CameraMovementEventParser_08(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = CameraMovementEvent(frames, event_type, event_code, pid)
        event.name = 'cameramovement_08'
        bytes.skip( (bytes.get_big_16() & 0x0F) << 3)
        return event
        
class CameraMovementEventParser_18(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = CameraMovementEvent(frames, event_type, event_code, pid)
        event.name = 'cameramovement_18'
        bytes.skip(162)
        return event
        
class CameraMovementEventParser_X1(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = CameraMovementEvent(frames, event_type, event_code, pid)
        event.name = 'cameramovement_X1'
        #Get the X and Y,  last byte is also a flag
        bytes.skip(3)
        flag = bytes.get_big_8()
        
        #Get the zoom,  last byte is a flag
        if flag & 0x10 != 0:
            bytes.skip(1)
            flag = bytes.get_big_8()
        
        #If we are currently zooming get more?? idk
        if flag & 0x20 != 0:
            bytes.skip(1)
            flag = bytes.get_big_8()
            
        #Do camera rotation as applies
        if flag & 0x40 != 0:
            bytes.skip(2)
        
        return event
        
#####################################################
# Unknown Event Type 02 Parsers
#####################################################
class UnknownEventParser_0206(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown0206'
        bytes.skip(8)
        return event
        
class UnknownEventParser_0207(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown0207'
        bytes.skip(4)
        return event

class UnknownEventParser_020E(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown020E'
        bytes.skip(4)
        return event

#####################################################
# Unknown Event Type 04 Parsers
#####################################################

class UnknownEventParser_04X2(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown04X2'
        bytes.skip(2)
        return event
        
class UnknownEventParser_0416(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown0416'
        bytes.skip(24)
        return event
        
class UnknownEventParser_04C6(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown04C6'
        block1 = bytes.get_big_32()
        block2 = bytes.get_big_32()
        block3 = bytes.get_big_32()
        block4 = bytes.get_big_32()
        return event

class UnknownEventParser_041C(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown041C'
        bytes.skip(15)
        return event
        
class UnknownEventParser_0487(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown0418-87'
        event.data = bytes.get_big_32() #Always 00 00 00 01??
        return event
        
class UnknownEventParser_0400(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown0400'
        bytes.skip(10)
        return event

class UnknownEventParser_04XC(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown04XC'
        return event
        
#####################################################
# Unknown Event Type 05 Parsers
#####################################################

class UnknownEventParser_0589(Parser):
    def load(self, bytes, frames, event_type, event_code, pid):
        event = UnknownEvent(frames, event_type, event_code, pid)
        event.name = 'unknown0589'
        bytes.skip(4)
        return event
