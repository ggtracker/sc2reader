from data import abilities

################################################
# Initialization Event Parsers
################################################

class PlayerJoinEventParser(object):
    def load(self,event,bytes):
        #print "Time %s - Player %s has joined the game" % (self.time,self.player)
        event.name = 'join'
        return event
    
class GameStartEventParser(object):
    def load(self,event,bytes):
        #print "Time %s - The game has started" % self.time
        event.name = 'start'
        return event
    
class WierdInitializationEventParser(object):
    def load(self,event,bytes):
        event.bytes += bytes.skip(19,byteCode=True)
        #print "Time %s - Wierd Initialization Event" % (self.time)
        event.name = 'weird'
        return event
        

#################################################
# Player Action Parsers
#################################################
class PlayerLeaveEventParser(object):
    def load(self,event,bytes):
        #print "Time %s - Player %s has left the game" % (self.time,self.player)
        event.name = 'leave'
        return event
        
class AbilityEventParser(object):
    def load(self,event,bytes):
        event.bytes += bytes.skip(4,byteCode=True)
        event.bytes += bytes.peek(4)
        event.ability = bytes.getBigInt(1) << 16 | bytes.getBigInt(1) << 8 | bytes.getBigInt(1)
        reqTarget = bytes.getBigInt(1)
        
        #In certain cases we need an extra byte
        if reqTarget == 0x30 or reqTarget == 0x05:
            event.bytes += bytes.skip(25,byteCode=True)
        else:
            event.bytes += bytes.skip(24,byteCode=True)
            
class AbilityEventParser_16561(AbilityEventParser):
    def load(self,event,bytes):
        event.bytes += bytes.peek(5)
        first,atype = (bytes.getBigInt(1),bytes.getBigInt(1))
        event.ability = bytes.getBigInt(1) << 16 | bytes.getBigInt(1) << 8 | (bytes.getBigInt(1) & 0x3F)
        
        if event.ability in abilities:
            event.abilitystr = abilities[event.ability]
        else: 
            event.abilitystr = "0x"+str(hex(event.ability))[2:].rjust(6,"0")
        
        if atype == 0x20 or atype == 0x22:
            event.name = 'unitability'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr,self.player,hex(atype),event.abilitystr)
            if event.ability & 0xFF > 0x07:
                if first == 0x29 or first == 0x19:
                    event.bytes += bytes.skip(4,byteCode=True)
                else:
                    event.bytes += bytes.skip(9,byteCode=True)
                    if event.ability & 0x20 != 0:
                        event.bytes += bytes.skip(9,byteCode=True)
                        
        elif atype == 0x48 or atype == 0x4A:
            #identifies target point
            event.name = 'targetlocation'
            #print "Time %s - Player %s issues location target" % (self.timestr,self.player)
            event.bytes += bytes.skip(7,byteCode=True)
        
        elif atype == 0x88 or atype == 0x8A:
            #identifies the target unit
            event.name = 'targetunit'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr,self.player,hex(atype),abilitystr)
            event.bytes += bytes.skip(15,byteCode=True)
        
        else:
            raise TypeError("Ability type %s is unknown at location %s" % (hex(atype),event.location))
            
        return event
            

class SelectionEventParser(object):
    def load(self,event,bytes):
        event.name = 'selection'
        event.bytes += bytes.peek(2)
        selectFlags,deselectCount = bytes.getBigInt(1),bytes.getBigInt(1)
        
        if deselectCount > 0:
            #Skip over the deselection bytes
            event.bytes += bytes.skip(deselectCount >> 3,byteCode=True)
        
        #Find the bits left over
        extras = deselectCount & 0x07
        if extras == 0:
            #This is easy when we are byte aligned
            unitTypeCount,byte = bytes.getBigInt(1,byteCode=True)
            event.bytes += byte
            
            event.bytes += bytes.peek(unitTypeCount*4+1)
            for i in range(0,unitTypeCount):
                unitType,unitCount = bytes.getBigInt(3),bytes.getBigInt(1)
            totalUnits = bytes.getBigInt(1)
            
            event.bytes += bytes.peek(totalUnits*4)
            for i in range(0,totalUnits):
                unitId,useCount = bytes.getBigInt(2),bytes.getBigInt(2)
        else:
            #We're not byte aligned, so need do so some bit shifting
            #This seems like 1000% wrong to me, but its what the people
            #at phpsc2replay think it is so I'll deal for now
            tailMask = 0xFF >> (8-extras)
            headMask = ~tailMask & 0xFF
            wTailMask = 0xFF >> extras
            wHeadMask = ~wTailMask & 0xFF
            
            event.bytes += bytes.peek(2)
            prevByte,nextByte = bytes.getBigInt(1), bytes.getBigInt(1)
            
            unitTypeCount = prevByte & headMask | nextByte & tailMask
            
            event.bytes += bytes.peek(unitTypeCount*4+1)
            for i in range(0,unitTypeCount):
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitType = prevByte & headMask | ((nextByte & wHeadMask) >> (8-extras))
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitType = unitType << 8 | (prevByte & wTailMask) << extras | nextByte & tailMask
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitType = unitType << 8 | (prevByte & headMask) << extras | nextByte & tailMask
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitCount = prevByte & headMask | nextByte & tailMask
                
            prevByte,nextByte = nextByte,bytes.getBigInt(1)    
            totalUnits = prevByte & headMask | nextByte & tailMask
            
            event.bytes = bytes.peek(totalUnits*4)
            for i in range(0,totalUnits):
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitId = prevByte & headMask | ((nextByte & wHeadMask) >> (8-extras))
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitId = unitId << 8 | prevByte & wTailMask << extras | ((nextByte & wHeadMask) >> (8-extras))
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitId = unitId << 8 | prevByte & wTailMask << extras | ((nextByte & wHeadMask) >> (8-extras))
                prevByte,nextByte = nextByte,bytes.getBigInt(1)
                unitId = unitId << 8 | prevByte & wTailMask << extras | nextByte & tailMask
            
class SelectionEventParser_16561(SelectionEventParser):
    def load(self,event,bytes):
        event.name = 'selection'
        event.bytes += bytes.peek(2)
        selectFlags,deselectType = bytes.getBigInt(1),bytes.getBigInt(1)
        
        #No deselection to do here
        if deselectType & 3 == 0:
            lastByte = deselectType #This is the last byte
            mask = 0x03 #default mask of '11' applies
            
        #deselection by bit counted indicators
        elif deselectType & 3 == 1:
            #use the 6 left bits on top and the 2 right bits on bottom
            countByte,byte = bytes.getBigInt(1,byteCode=True)
            deselectCount = deselectType & 0xFC | countByte & 0x03
            event.bytes += byte
            
            #If we don't need extra bytes then this is the last one
            if deselectCount <= 6:
                lastByte = countByte
            else:
                #while count > 6 we need to eat into more bytes because
                #we only have 6 bits left in our current byte
                while deselectCount > 6:
                    lastByte,byte = bytes.getBigInt(1,byteCode=True)
                    deselectCount -= 8
                    event.bytes += byte
            
            #If we exactly use the whole byte
            if deselectCount == 6:
                mask = 0xFF #no mask is needed since we are even
                
            #Because we went bit by bit the mask is different so we
            #take the deselect bits used on the lastByte, add the two
            #bits left bits we've carried down, we need a mask that long
            else:
                mask = (1 << (deselectCount+2)) - 1
            
        #deselect by byte, I think (deselectType & 3 == 3) is deselect all
        #and as such probably has a deselectCount always == 0, not sure though
        else:
            #use the 6 left bits on top and the 2 right bits on bottom
            countByte,byte = bytes.getBigInt(1,byteCode=True)
            deselectCount = deselectType & 0xFC | countByte & 0x03
            event.bytes += byte
            
            #If the count is zero than that byte is the last one
            if deselectCount == 0:
                lastByte = countByte
                
            #Because this count is in bytes we can just read that many bytes
            #we need to save the last one though because we need the bits
            else:
                event.bytes += bytes.peek(deselectCount)
                bytes.skip(deselectCount-1)
                lastByte = bytes.getBigInt(1)
            
            mask = 0x03 #default mask of '11' applies
        
        combine = lambda last,next: last & (0xFF-mask) | next & mask
        
        unitIds = list()    
        unitTypes = dict()
        
        #Get the number of selected unit types
        event.bytes += bytes.peek(1)
        nextByte = bytes.getBigInt(1)
        numUnitTypes = combine(lastByte,nextByte)
        
        #Read them all into a dictionary for later
        for i in range(0,numUnitTypes):
            #3 bytes for the typeID and 1 byte for the count
            event.bytes += bytes.peek(4)
            
            #Build the unitTypeId over the next 3 bytes
            byteList = list()
            for i in range(0,3):
                #Swap the bytes, grab another, and combine w/ the mask
                lastByte,nextByte = nextByte,bytes.getBigInt(1)
                byteList.append( combine(lastByte,nextByte) )
            unitTypeId = byteList[0] << 16 | byteList[1] << 8 | byteList[2]
            
            #Get the count for that type in the next byte
            lastByte,nextByte = nextByte,bytes.getBigInt(1)
            unitTypeCount = combine(lastByte,nextByte)
            
            #Store for later
            unitTypes[unitTypeId] = unitTypeCount
        
        #Get total unit count
        event.bytes += bytes.peek(1)
        lastByte,nextByte = nextByte,bytes.getBigInt(1)
        unitCount = combine(lastByte,nextByte)
        
        #Pull all the unitIds in for later
        for i in range(0,unitCount):
            event.bytes += bytes.peek(4)
            
            #build the unitId over the next 4 bytes
            byteList = list()
            for i in range(0,4):
                lastByte,nextByte = nextByte,bytes.getBigInt(1)
                byteList.append( combine(lastByte,nextByte) )
            
            #The first 2 bytes are unique and the last 2 mark reusage count
            unitId = byteList[0] << 24 | byteList[1] << 16 | byteList[2] << 8 | byteList[3]
            unitIds.append( unitId )
        """    
        print "Time %s - Player %s selects:" % (self.timestr,self.player)
        for uid,count in unitTypes.iteritems():
            if uid in units:
                uid = units[uid]
            else:
                uid = "0x"+str(hex(uid))[2:].rjust(6,"0")
                pause = True
            print "  - %s %s units" % (count,uid)
        """
        return event
        
class HotkeyEventParser(object):
    
    def loadSetHotkey(self,event,bytes,first):
        event.name = 'set_hotkey'
    
    def loadGetHotkey(self,event,bytes,first):
        event.name = 'get_hotkey'
    
    def loadGetHotkeyChanged(self,event,bytes,first):
        event.name = 'get_hotkey_changed'
        
        extras = first >> 3
        event.bytes += bytes.peek(extras+1)
        second = bytes.getBig(1)
        bytes.skip(extras)
        
        if first & 0x04: 
            event.bytes += bytes.skip(1,byteCode=True)
            if second & 0x06 == 0x06:
                event.bytes += bytes.skip(1,byteCode=True)
        
    def load(self,event,bytes):
        event.name = 'hotkey'
        event.hotkey = str(event.code >> 4)
        #print "Time %s - Player %s is using hotkey %s" % (self.timestr,self.player,eventCode >> 4)
        first,byte = bytes.getBigInt(1,byteCode=True)
        event.bytes += byte
        
        if   first == 0x00: self.loadSetHotkey(event,bytes,first)
        elif first == 0x02: self.loadGetHotkey(event,bytes,first)
        elif first  > 0x03: self.loadGetHotkeyChanged(event,bytes,first)
        else: pass
        
        return event
    
class HotkeyEventParser_16561(HotkeyEventParser):
    def loadGetHotkeyChanged(self,event,bytes,first):
        name = 'get_hotkey_changed'
        second,byte = bytes.getBigInt(1,byteCode=True)
        event.bytes += byte
        
        if first & 0x08:
            event.bytes += bytes.skip(second & 0x0F,byteCode=True)
        else:  
            extras = first >> 3
            event.bytes += bytes.skip(extras,byteCode=True)
            if extras == 0:
                if second & 0x07 > 0x04:
                    event.bytes += bytes.skip(1,byteCode=True)
                if second & 0x08 != 0:
                    event.bytes += bytes.skip(1,byteCode=True)
            else:
                if first & 0x04 != 0:
                    if second & 0x07 > 0x04:
                        event.bytes += bytes.skip(1,byteCode=True)
                    if second & 0x08 != 0:
                        event.bytes += bytes.skip(1,byteCode=True)
                        
class ResourceTransferEventParser(object):
    def load(self,event,bytes):
        event.name = 'resourcetransfer'
        #print "Time %s - Player %s is sending resources to Player %s" % (self.timestr,self.player,self.code >> 4)
        
        event.bytes += bytes.skip(1,byteCode=True)  # 84
        event.sender = event.player
        event.receiver = event.code >> 4
        
        #I might need to shift these two things to 19,11,3 for first 3 shifts
        event.bytes += bytes.peek(8)
        event.minerals = bytes.getBigInt(1) << 20 | bytes.getBigInt(1) << 12 | bytes.getBigInt(1) << 4 | bytes.getBigInt(1) >> 4
        event.gas = bytes.getBigInt(1) << 20 | bytes.getBigInt(1) << 12 | bytes.getBigInt(1) << 4 | bytes.getBigInt(1) >> 4
        
        #unknown extra stuff
        event.bytes += bytes.skip(2,byteCode=True)
        return event

class ResourceTransferEventParser_16561(ResourceTransferEventParser):
    def load(self,event,bytes):
        event.name = 'resourcetransfer'
        
        #Always 17 bytes long
        event.bytes += bytes.peek(17)
        event.sender = event.player
        event.reciever = event.code >> 4
        
        bytes.getBigInt(1) #Always 84
        
        #Minerals and Gas are encoded the same way
        base,extension = bytes.getBigInt(3),bytes.getBigInt(1)
        event.minerals = base*(extension >> 4)+ (extension & 0x0F)
        base,extension = bytes.getBigInt(3),bytes.getBigInt(1)
        event.gas = base*(extension >> 4)+ (extension & 0x0F)
        
        #Another 8 bytes that don't make sense
        bytes.skip(8)
        return event
        
        
#######################################################
# Camera Movement Event Parsers
#######################################################
        
class CameraMovementEventParser_87(object):
    def load(self,event,bytes):
        event.name = 'cameramovement_87'
        event.bytes += bytes.skip(8,byteCode=True)
        return event

class CameraMovementEventParser_08(object):
    def load(self,event,bytes):
        event.name = 'cameramovement_08'
        event.bytes += bytes.skip(10,byteCode=True)
        return event
        
class CameraMovementEventParser_18(object):
    def load(self,event,bytes):
        event.name = 'cameramovement_18'
        event.bytes += bytes.skip(162,byteCode=True)
        return event
        
class CameraMovementEventParser_X1(object):
    def load(self,event,bytes):
        event.name = 'cameramovement_X1'
        #Get the X and Y, last byte is also a flag
        event.bytes += bytes.skip(3,byteCode=True)+bytes.peek(1)
        flag = bytes.getBigInt(1)
        
        #Get the zoom, last byte is a flag
        if flag & 0x10 != 0:
            event.bytes += bytes.skip(1,byteCode=True)+bytes.peek(1)
            flag = bytes.getBigInt(1)
        
        #If we are currently zooming get more?? idk
        if flag & 0x20 != 0:
            event.bytes += bytes.skip(1,byteCode=True)+bytes.peek(1)
            flag = bytes.getBigInt(1)
            
        #Do camera rotation as applies
        if flag & 0x40 != 0:
            event.bytes += bytes.skip(2,byteCode=True)
        
        return event
        
#####################################################
# Unknown Event Type 02 Parsers
#####################################################

class UnknownEventParser_0206(object):
    def load(self,event,bytes):
        event.name = 'unknown0206'
        event.bytes += bytes.skip(8,byteCode=True)
        return event
        
class UnknownEventParser_0207(object):
    def load(self,event,bytes):
        event.name = 'unknown0207'
        event.bytes += bytes.skip(4,byteCode=True)
        return event

#####################################################
# Unknown Event Type 04 Parsers
#####################################################

class UnknownEventParser_04X2(object):
    def load(self,event,bytes):
        event.name = 'unknown04X2'
        event.bytes += bytes.skip(2,byteCode=True)
        return event
        
class UnknownEventParser_0416(object):
    def load(self,event,bytes):
        event.name = 'unknown0416'
        event.bytes += bytes.skip(24,byteCode=True)
        return event
        
class UnknownEventParser_04C6(object):
    def load(self,event,bytes):
        event.name = 'unknown04C6'
        event.bytes += bytes.peek(16)
        block1 = bytes.getBig(4)
        block2 = bytes.getBig(4)
        block3 = bytes.getBig(4)
        block4 = bytes.getBig(4)
        return event

class UnknownEventParser_041C(object):
    def load(self,event,bytes):
        event.name = 'unknown041C'
        event.bytes += bytes.skip(15,byteCode=True)
        return event
        
class UnknownEventParser_0487(object):
    def load(self,event,bytes):
        event.name = 'unknown0418-87'
        event.data, databytes = bytes.getBig(4,byteCode=True) #Always 00 00 00 01??
        event.bytes += databytes
        return event
        
class UnknownEventParser_0400(object):
    def load(self,event,bytes):
        event.name = 'unknown0400'
        event.bytes += bytes.skip(10,byteCode=True)
        return event

class UnknownEventParser_04XC(object):
    def load(self,event,bytes):
        event.name = 'unknown04XC'
        print bytes.peek(20)
        return event
        
#####################################################
# Unknown Event Type 05 Parsers
#####################################################

class UnknownEventParser_0589(object):
    def load(self,event,bytes):
        event.name = 'unknown0589'
        event.bytes += bytes.skip(4,byteCode=True)
        return event
        