from data import abilities

################################################
# Initialization Event Parsers
################################################

class PlayerJoinEventParser(object):
    def load(self, event, bytes):
        #print "Time %s - Player %s has joined the game" % (self.time, self.player)
        event.name = 'join'
        return event
    
class GameStartEventParser(object):
    def load(self, event, bytes):
        #print "Time %s - The game has started" % self.time
        event.name = 'start'
        return event
    
class WierdInitializationEventParser(object):
    def load(self, event, bytes):
        event.bytes += bytes.skip(19, byte_code=True)
        #print "Time %s - Wierd Initialization Event" % (self.time)
        event.name = 'weird'
        return event
        

#################################################
# Player Action Parsers
#################################################
class PlayerLeaveEventParser(object):
    def load(self, event, bytes):
        #print "Time %s - Player %s has left the game" % (self.time, self.player)
        event.name = 'leave'
        return event
        
class AbilityEventParser(object):
    def load(self, event, bytes):
        event.bytes += bytes.skip(4, byte_code=True)
        event.bytes += bytes.peek(4)
        event.ability = bytes.get_big_int(1) << 16 | bytes.get_big_int(1) << 8 | bytes.get_big_int(1)
        req_target = bytes.get_big_int(1)
        
        #In certain cases we need an extra byte
        if req_target == 0x30 or req_target == 0x05:
            event.bytes += bytes.skip(25, byte_code=True)
        else:
            event.bytes += bytes.skip(24, byte_code=True)
            
class AbilityEventParser_16561(AbilityEventParser):
    def load(self, event, bytes):
        event.bytes += bytes.peek(5)
        first, atype = (bytes.get_big_int(1), bytes.get_big_int(1))
        event.ability = bytes.get_big_int(1) << 16 | bytes.get_big_int(1) << 8 | (bytes.get_big_int(1) & 0x3F)
        
        if event.ability in abilities:
            event.abilitystr = abilities[event.ability]
        else: 
            event.abilitystr = "0x"+str(hex(event.ability))[2:].rjust(6, "0")
        
        if atype == 0x20 or atype == 0x22:
            event.name = 'unitability'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr, self.player, hex(atype), event.abilitystr)
            if event.ability & 0xFF > 0x07:
                if first == 0x29 or first == 0x19:
                    event.bytes += bytes.skip(4, byte_code=True)
                else:
                    event.bytes += bytes.skip(9, byte_code=True)
                    if event.ability & 0x20 != 0:
                        event.bytes += bytes.skip(9, byte_code=True)
                        
        elif atype == 0x48 or atype == 0x4A:
            #identifies target point
            event.name = 'targetlocation'
            #print "Time %s - Player %s issues location target" % (self.timestr, self.player)
            event.bytes += bytes.skip(7, byte_code=True)
        
        elif atype == 0x88 or atype == 0x8A:
            #identifies the target unit
            event.name = 'targetunit'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr, self.player, hex(atype), abilitystr)
            event.bytes += bytes.skip(15, byte_code=True)
        
        else:
            raise TypeError("Ability type %s is unknown at location %s" % (hex(atype), event.location))
            
        return event
            

class SelectionEventParser(object):
    def load(self, event, bytes):
        event.name = 'selection'
        event.bytes += bytes.peek(2)
        select_flags, deselect_count = bytes.get_big_int(1), bytes.get_big_int(1)
        
        if deselect_count > 0:
            #Skip over the deselection bytes
            event.bytes += bytes.skip(deselect_count >> 3, byte_code=True)
        
        #Find the bits left over
        extras = deselect_count & 0x07
        if extras == 0:
            #This is easy when we are byte aligned
            unit_type_count, byte = bytes.get_big_int(1, byte_code=True)
            event.bytes += byte
            
            event.bytes += bytes.peek(unit_type_count*4+1)
            for i in range(0, unit_type_count):
                unit_type, unit_count = bytes.get_big_int(3), bytes.get_big_int(1)
            totalUnits = bytes.get_big_int(1)
            
            event.bytes += bytes.peek(totalUnits*4)
            for i in range(0, totalUnits):
                unit_id, use_count = bytes.get_big_int(2), bytes.get_big_int(2)
        else:
            #We're not byte aligned,  so need do so some bit shifting
            #This seems like 1000% wrong to me,  but its what the people
            #at phpsc2replay think it is so I'll deal for now
            tail_mask = 0xFF >> (8-extras)
            head_mask = ~tail_mask & 0xFF
            w_tail_mask = 0xFF >> extras
            w_head_mask = ~w_tail_mask & 0xFF
            
            event.bytes += bytes.peek(2)
            prev_byte, next_byte = bytes.get_big_int(1),  bytes.get_big_int(1)
            
            unit_type_count = prev_byte & head_mask | next_byte & tail_mask
            
            event.bytes += bytes.peek(unit_type_count*4+1)
            for i in range(0, unit_type_count):
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_type = prev_byte & head_mask | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_type = unit_type << 8 | (prev_byte & w_tail_mask) << extras | next_byte & tail_mask
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_type = unit_type << 8 | (prev_byte & head_mask) << extras | next_byte & tail_mask
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_count = prev_byte & head_mask | next_byte & tail_mask
                
            prev_byte, next_byte = next_byte, bytes.get_big_int(1)    
            totalUnits = prev_byte & head_mask | next_byte & tail_mask
            
            event.bytes = bytes.peek(totalUnits*4)
            for i in range(0, totalUnits):
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_id = prev_byte & head_mask | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_id = unit_id << 8 | prev_byte & w_tail_mask << extras | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_id = unit_id << 8 | prev_byte & w_tail_mask << extras | ((next_byte & w_head_mask) >> (8-extras))
                prev_byte, next_byte = next_byte, bytes.get_big_int(1)
                unit_id = unit_id << 8 | prev_byte & w_tail_mask << extras | next_byte & tail_mask
            
class SelectionEventParser_16561(SelectionEventParser):
    def load(self, event, bytes):
        event.name = 'selection'
        event.bytes += bytes.peek(2)
        select_flags, deselect_type = bytes.get_big_int(1), bytes.get_big_int(1)
        
        #No deselection to do here
        if deselect_type & 3 == 0:
            last_byte = deselect_type #This is the last byte
            mask = 0x03 #default mask of '11' applies
            
        #deselection by bit counted indicators
        elif deselect_type & 3 == 1:
            #use the 6 left bits on top and the 2 right bits on bottom
            count_byte, byte = bytes.get_big_int(1, byte_code=True)
            deselect_count = deselect_type & 0xFC | count_byte & 0x03
            event.bytes += byte
            
            #If we don't need extra bytes then this is the last one
            if deselect_count <= 6:
                last_byte = count_byte
            else:
                #while count > 6 we need to eat into more bytes because
                #we only have 6 bits left in our current byte
                while deselect_count > 6:
                    last_byte, byte = bytes.get_big_int(1, byte_code=True)
                    deselect_count -= 8
                    event.bytes += byte
            
            #If we exactly use the whole byte
            if deselect_count == 6:
                mask = 0xFF #no mask is needed since we are even
                
            #Because we went bit by bit the mask is different so we
            #take the deselect bits used on the last_byte,  add the two
            #bits left bits we've carried down,  we need a mask that long
            else:
                mask = (1 << (deselect_count+2)) - 1
            
        #deselect by byte,  I think (deselect_type & 3 == 3) is deselect all
        #and as such probably has a deselect_count always == 0,  not sure though
        else:
            #use the 6 left bits on top and the 2 right bits on bottom
            count_byte, byte = bytes.get_big_int(1, byte_code=True)
            deselect_count = deselect_type & 0xFC | count_byte & 0x03
            event.bytes += byte
            
            #If the count is zero than that byte is the last one
            if deselect_count == 0:
                last_byte = count_byte
                
            #Because this count is in bytes we can just read that many bytes
            #we need to save the last one though because we need the bits
            else:
                event.bytes += bytes.peek(deselect_count)
                bytes.skip(deselect_count-1)
                last_byte = bytes.get_big_int(1)
            
            mask = 0x03 #default mask of '11' applies
        
        combine = lambda last, next: last & (0xFF-mask) | next & mask
        
        unit_ids = list()    
        unit_types = dict()
        
        #Get the number of selected unit types
        event.bytes += bytes.peek(1)
        next_byte = bytes.get_big_int(1)
        numunit_types = combine(last_byte, next_byte)
        
        #Read them all into a dictionary for later
        for i in range(0, numunit_types):
            #3 bytes for the type_id and 1 byte for the count
            event.bytes += bytes.peek(4)
            
            #Build the unit_type_id over the next 3 bytes
            byte_list = list()
            for i in range(0, 3):
                #Swap the bytes,  grab another,  and combine w/ the mask
                last_byte, next_byte = next_byte, bytes.get_big_int(1)
                byte_list.append( combine(last_byte, next_byte) )
            unit_type_id = byte_list[0] << 16 | byte_list[1] << 8 | byte_list[2]
            
            #Get the count for that type in the next byte
            last_byte, next_byte = next_byte, bytes.get_big_int(1)
            unit_type_count = combine(last_byte, next_byte)
            
            #Store for later
            unit_types[unit_type_id] = unit_type_count
        
        #Get total unit count
        event.bytes += bytes.peek(1)
        last_byte, next_byte = next_byte, bytes.get_big_int(1)
        unit_count = combine(last_byte, next_byte)
        
        #Pull all the unit_ids in for later
        for i in range(0, unit_count):
            event.bytes += bytes.peek(4)
            
            #build the unit_id over the next 4 bytes
            byte_list = list()
            for i in range(0, 4):
                last_byte, next_byte = next_byte, bytes.get_big_int(1)
                byte_list.append( combine(last_byte, next_byte) )
            
            #The first 2 bytes are unique and the last 2 mark reusage count
            unit_id = byte_list[0] << 24 | byte_list[1] << 16 | byte_list[2] << 8 | byte_list[3]
            unit_ids.append( unit_id )
        """    
        print "Time %s - Player %s selects:" % (self.timestr, self.player)
        for uid, count in unit_types.iteritems():
            if uid in units:
                uid = units[uid]
            else:
                uid = "0x"+str(hex(uid))[2:].rjust(6, "0")
                pause = True
            print "  - %s %s units" % (count, uid)
        """
        return event
        
class HotkeyEventParser(object):
    
    def load_set_hotkey(self, event, bytes, first):
        event.name = 'set_hotkey'
    
    def load_get_hotkey(self, event, bytes, first):
        event.name = 'get_hotkey'
    
    def load_get_hotkey_changed(self, event, bytes, first):
        event.name = 'get_hotkey_changed'
        
        extras = first >> 3
        event.bytes += bytes.peek(extras+1)
        second = bytes.get_big(1)
        bytes.skip(extras)
        
        if first & 0x04: 
            event.bytes += bytes.skip(1, byte_code=True)
            if second & 0x06 == 0x06:
                event.bytes += bytes.skip(1, byte_code=True)
        
    def load(self, event, bytes):
        event.name = 'hotkey'
        event.hotkey = str(event.code >> 4)
        #print "Time %s - Player %s is using hotkey %s" % (self.timestr, self.player, eventCode >> 4)
        first, byte = bytes.get_big_int(1, byte_code=True)
        event.bytes += byte
        
        if   first == 0x00: self.load_set_hotkey(event, bytes, first)
        elif first == 0x02: self.load_get_hotkey(event, bytes, first)
        elif first  > 0x03: self.load_get_hotkey_changed(event, bytes, first)
        else: pass
        
        return event
    
class HotkeyEventParser_16561(HotkeyEventParser):
    def load_get_hotkey_changed(self, event, bytes, first):
        name = 'get_hotkey_changed'
        second, byte = bytes.get_big_int(1, byte_code=True)
        event.bytes += byte
        
        if first & 0x08:
            event.bytes += bytes.skip(second & 0x0F, byte_code=True)
        else:  
            extras = first >> 3
            event.bytes += bytes.skip(extras, byte_code=True)
            if extras == 0:
                if second & 0x07 > 0x04:
                    event.bytes += bytes.skip(1, byte_code=True)
                if second & 0x08 != 0:
                    event.bytes += bytes.skip(1, byte_code=True)
            else:
                if first & 0x04 != 0:
                    if second & 0x07 > 0x04:
                        event.bytes += bytes.skip(1, byte_code=True)
                    if second & 0x08 != 0:
                        event.bytes += bytes.skip(1, byte_code=True)
                        
class ResourceTransferEventParser(object):
    def load(self, event, bytes):
        event.name = 'resourcetransfer'
        #print "Time %s - Player %s is sending resources to Player %s" % (self.timestr, self.player, self.code >> 4)
        
        event.bytes += bytes.skip(1, byte_code=True)  # 84
        event.sender = event.player
        event.receiver = event.code >> 4
        
        #I might need to shift these two things to 19, 11, 3 for first 3 shifts
        event.bytes += bytes.peek(8)
        event.minerals = bytes.get_big_int(1) << 20 | bytes.get_big_int(1) << 12 | bytes.get_big_int(1) << 4 | bytes.get_big_int(1) >> 4
        event.gas = bytes.get_big_int(1) << 20 | bytes.get_big_int(1) << 12 | bytes.get_big_int(1) << 4 | bytes.get_big_int(1) >> 4
        
        #unknown extra stuff
        event.bytes += bytes.skip(2, byte_code=True)
        return event

class ResourceTransferEventParser_16561(ResourceTransferEventParser):
    def load(self, event, bytes):
        event.name = 'resourcetransfer'
        
        #Always 17 bytes long
        event.bytes += bytes.peek(17)
        event.sender = event.player
        event.reciever = event.code >> 4
        
        bytes.get_big_int(1) #Always 84
        
        #Minerals and Gas are encoded the same way
        base, extension = bytes.get_big_int(3), bytes.get_big_int(1)
        event.minerals = base*(extension >> 4)+ (extension & 0x0F)
        base, extension = bytes.get_big_int(3), bytes.get_big_int(1)
        event.gas = base*(extension >> 4)+ (extension & 0x0F)
        
        #Another 8 bytes that don't make sense
        bytes.skip(8)
        return event
        
        
#######################################################
# Camera Movement Event Parsers
#######################################################
        
class CameraMovementEventParser_87(object):
    def load(self, event, bytes):
        event.name = 'cameramovement_87'
        event.bytes += bytes.skip(8, byte_code=True)
        return event

class CameraMovementEventParser_08(object):
    def load(self, event, bytes):
        event.name = 'cameramovement_08'
        event.bytes += bytes.skip(10, byte_code=True)
        return event
        
class CameraMovementEventParser_18(object):
    def load(self, event, bytes):
        event.name = 'cameramovement_18'
        event.bytes += bytes.skip(162, byte_code=True)
        return event
        
class CameraMovementEventParser_X1(object):
    def load(self, event, bytes):
        event.name = 'cameramovement_X1'
        #Get the X and Y,  last byte is also a flag
        event.bytes += bytes.skip(3, byte_code=True)+bytes.peek(1)
        flag = bytes.get_big_int(1)
        
        #Get the zoom,  last byte is a flag
        if flag & 0x10 != 0:
            event.bytes += bytes.skip(1, byte_code=True)+bytes.peek(1)
            flag = bytes.get_big_int(1)
        
        #If we are currently zooming get more?? idk
        if flag & 0x20 != 0:
            event.bytes += bytes.skip(1, byte_code=True)+bytes.peek(1)
            flag = bytes.get_big_int(1)
            
        #Do camera rotation as applies
        if flag & 0x40 != 0:
            event.bytes += bytes.skip(2, byte_code=True)
        
        return event
        
#####################################################
# Unknown Event Type 02 Parsers
#####################################################

class UnknownEventParser_0206(object):
    def load(self, event, bytes):
        event.name = 'unknown0206'
        event.bytes += bytes.skip(8, byte_code=True)
        return event
        
class UnknownEventParser_0207(object):
    def load(self, event, bytes):
        event.name = 'unknown0207'
        event.bytes += bytes.skip(4, byte_code=True)
        return event

#####################################################
# Unknown Event Type 04 Parsers
#####################################################

class UnknownEventParser_04X2(object):
    def load(self, event, bytes):
        event.name = 'unknown04X2'
        event.bytes += bytes.skip(2, byte_code=True)
        return event
        
class UnknownEventParser_0416(object):
    def load(self, event, bytes):
        event.name = 'unknown0416'
        event.bytes += bytes.skip(24, byte_code=True)
        return event
        
class UnknownEventParser_04C6(object):
    def load(self, event, bytes):
        event.name = 'unknown04C6'
        event.bytes += bytes.peek(16)
        block1 = bytes.get_big(4)
        block2 = bytes.get_big(4)
        block3 = bytes.get_big(4)
        block4 = bytes.get_big(4)
        return event

class UnknownEventParser_041C(object):
    def load(self, event, bytes):
        event.name = 'unknown041C'
        event.bytes += bytes.skip(15, byte_code=True)
        return event
        
class UnknownEventParser_0487(object):
    def load(self, event, bytes):
        event.name = 'unknown0418-87'
        event.data,  databytes = bytes.get_big(4, byte_code=True) #Always 00 00 00 01??
        event.bytes += databytes
        return event
        
class UnknownEventParser_0400(object):
    def load(self, event, bytes):
        event.name = 'unknown0400'
        event.bytes += bytes.skip(10, byte_code=True)
        return event

class UnknownEventParser_04XC(object):
    def load(self, event, bytes):
        event.name = 'unknown04XC'
        print bytes.peek(20)
        return event
        
#####################################################
# Unknown Event Type 05 Parsers
#####################################################

class UnknownEventParser_0589(object):
    def load(self, event, bytes):
        event.name = 'unknown0589'
        event.bytes += bytes.skip(4, byte_code=True)
        return event
        