from data import abilities

class Event(object):
    def __call__(self,elapsedTime,eventType,globalFlag,playerId,eventCode,bytes):
        self.time,seconds = (elapsedTime,elapsedTime/16)
        self.timestr = "%s:%s" % (seconds/60,str(seconds%60).rjust(2,"0"))
        self.type = eventType
        self.code = eventCode
        self.local = (globalFlag == 0x0)
        self.player = playerId
        self.bytes = ""
        self.parse(bytes)
        return self
        
class PlayerJoinEvent(Event):
    def parse(self,bytes):
        #print "Time %s - Player %s has joined the game" % (self.time,self.player)
        self.name = 'join'
    
class GameStartEvent(Event):
    def parse(self,bytes):
        #print "Time %s - The game has started" % self.time
        self.name = 'start'
        
class PlayerLeaveEvent(Event):
    def parse(self,bytes):
        #print "Time %s - Player %s has left the game" % (self.time,self.player)
        self.name = 'leave'
    
class WierdInitializationEvent(Event):
    def parse(self,bytes):
        self.bytes += bytes.skip(19,byteCode=True)
        #print "Time %s - Wierd Initialization Event" % (self.time)
        self.name = 'weird'
        
        
class AbilityEvent(Event):
    def parse(self,bytes):
        self.bytes += bytes.peek(5)
        first,atype = (bytes.getBigInt(1),bytes.getBigInt(1))
        ability = bytes.getBigInt(1) << 16 | bytes.getBigInt(1) << 8 | (bytes.getBigInt(1) & 0x3F)
        
        if ability in abilities:
            abilitystr = abilities[ability]
        else: 
            if atype == 0x20 or atype == 0x22: pause = True
            abilitystr = "0x"+str(hex(ability))[2:].rjust(6,"0")
        
        if atype == 0x20 or atype == 0x22:
            self.name = 'unitability'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr,self.player,hex(atype),abilitystr)
            if ability & 0xFF > 0x07:
                if first == 0x29 or first == 0x19:
                    self.bytes += bytes.skip(4,byteCode=True)
                else:
                    self.bytes += bytes.skip(9,byteCode=True)
                    if ability & 0x20 != 0:
                        self.bytes += bytes.skip(9,byteCode=True)
                        
        elif atype == 0x48 or atype == 0x4A:
            #identifies target point
            self.name = 'targetlocation'
            #print "Time %s - Player %s issues location target" % (self.timestr,self.player)
            self.bytes += bytes.skip(7,byteCode=True)
        
        elif atype == 0x88 or atype == 0x8A:
            #identifies the target unit
            self.name = 'targetunit'
            #print "Time %s - Player %s orders (%s) %s " % (self.timestr,self.player,hex(atype),abilitystr)
            self.bytes += bytes.skip(15,byteCode=True)
        
        else:
            raise TypeError("Ability type %s is unknown at location %s" % (hex(atype),hex(bytes.cursor)))
            
            
class SelectionEvent(Event):
    def parse(self,bytes):
        self.name = 'selection'
        self.bytes += bytes.peek(2)
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
            self.bytes += byte
            
            #If we don't need extra bytes then this is the last one
            if deselectCount <= 6:
                lastByte = countByte
            else:
                #while count > 6 we need to eat into more bytes because
                #we only have 6 bits left in our current byte
                while deselectCount > 6:
                    lastByte,byte = bytes.getBigInt(1,byteCode=True)
                    deselectCount -= 8
                    self.bytes += byte
            
            #If we exactly use the whole byte
            if deselectCount == 6:
                mask = 0xFF #no mask is needed since we are even
                
            #Because we went bit by bit the mask is different so we
            #take the deselect bits used on the lastByte, add the two
            #bits left bits we've carried down, we need a mask that long
            else:
                mask = (1 << (deselectCount+2)) - 1
            
        #deselection by byte counted indicators
        else:
            #use the 6 left bits on top and the 2 right bits on bottom
            countByte,byte = bytes.getBigInt(1,byteCode=True)
            deselectCount = deselectType & 0xFC | countByte & 0x03
            self.bytes += byte
            
            #If the count is zero than that byte is the last one
            if deselectCount == 0:
                lastByte = countByte
                
            #Because this count is in bytes we can just read that many bytes
            #we need to save the last one though because we need the bits
            else:
                self.bytes += bytes.peek(deselectCount)
                bytes.skip(deselectCount-1)
                lastByte = bytes.getBigInt(1)
            
            mask = 0x03 #default mask of '11' applies
        
        combine = lambda last,next: last & (0xFF-mask) | next & mask
        
        unitIds = list()    
        unitTypes = dict()
        
        #Get the number of selected unit types
        self.bytes += bytes.peek(1)
        nextByte = bytes.getBigInt(1)
        numUnitTypes = combine(lastByte,nextByte)
        
        #Read them all into a dictionary for later
        for i in range(0,numUnitTypes):
            #3 bytes for the typeID and 1 byte for the count
            self.bytes += bytes.peek(4)
            
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
        self.bytes += bytes.peek(1)
        lastByte,nextByte = nextByte,bytes.getBigInt(1)
        unitCount = combine(lastByte,nextByte)
        
        #Pull all the unitIds in for later
        for i in range(0,unitCount):
            self.bytes += bytes.peek(4)
            
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
        
class HotkeyEvent(Event):
    def parse(self,bytes):
        self.name = 'hotkey'
        #print "Time %s - Player %s is using hotkey %s" % (self.timestr,self.player,eventCode >> 4)
        first,byte = bytes.getBigInt(1,byteCode=True)
        self.bytes += byte
        
        if first > 0x03:
            second,byte = bytes.getBigInt(1,byteCode=True)
            self.bytes += byte
            
            if first & 0x08:
                self.bytes += bytes.skip(second & 0x0F,byteCode=True)
            else:
                extras = first >> 3
                self.bytes += bytes.skip(extras,byteCode=True)
                #self.bytes += bytes.getBig(1) #Not sure why this is here, works fine w/out it?
                if extras == 0:
                    if second & 0x07 > 0x04:
                        self.bytes += bytes.skip(1,byteCode=True)
                    if second & 0x08 != 0:
                        self.bytes += bytes.skip(1,byteCode=True)
                else:
                    if first & 0x04 != 0:
                        if second & 0x07 > 0x04:
                            self.bytes += bytes.skip(1,byteCode=True)
                        if second & 0x08 != 0:
                            self.bytes += bytes.skip(1,byteCode=True)
        else:
            pass #print "No data associated with hotkey"
            
class ResourceTransferEvent(Event):
    def parse(self,bytes):
        self.name = 'resourcetransfer'
        print "Time %s - Player %s is sending resources to Player %s" % (self.timestr,self.player,eventCode >> 4)
        
        self.bytes += bytes.skip(1,byteCode=True)  # 84
        sender = self.player
        receiver = eventCode >> 4
        
        #I might need to shift these two things to 19,11,3 for first 3 shifts
        self.bytes += bytes.peek(8)
        minerals = bytes.getBigInt(1) << 20 | bytes.getBigInt(1) << 12 | bytes.getBigInt(1) << 4 | bytes.getBigInt(1) >> 4
        gas = bytes.getBigInt(1) << 20 | bytes.getBigInt(1) << 12 | bytes.getBigInt(1) << 4 | bytes.getBigInt(1) >> 4
        
        #unknown extra stuff
        self.bytes += bytes.skip(2,byteCode=True)

class CameraMovementEvent_87(Event):
    def parse(self,bytes):
        self.name = 'cameramovement'
        self.bytes += bytes.skip(8,byteCode=True)

class CameraMovementEvent_08(Event):
    def parse(self,bytes):
        self.name = 'cameramovement'
        self.bytes += bytes.skip(10,byteCode=True)
        
class CameraMovementEvent_18(Event):
    def parse(self,bytes):
        self.name = 'cameramovement'
        self.bytes += bytes.skip(162,byteCode=True)
        
class CameraMovementEvent_X1(Event):
    def parse(self,bytes):
        self.name = 'cameramovement'
        #Get the X and Y, last byte is also a flag
        self.bytes += bytes.skip(3,byteCode=True)+bytes.peek(1)
        flag = bytes.getBigInt(1)
        
        #Get the zoom, last byte is a flag
        if flag & 0x10 != 0:
            self.bytes += bytes.skip(1,byteCode=True)+bytes.peek(1)
            flag = bytes.getBigInt(1)
        
        #If we are currently zooming get more?? idk
        if flag & 0x20 != 0:
            self.bytes += bytes.skip(1,byteCode=True)+bytes.peek(1)
            flag = bytes.getBigInt(1)
            
        #Do camera rotation as applies
        if flag & 0x40 != 0:
            self.bytes += bytes.skip(2,byteCode=True)
        
class UnknownEvent_02_06(Event):
    def parse(self,bytes):
        self.name = 'unknown0206'
        self.bytes += bytes.skip(8,byteCode=True)
        
class UnknownEvent_02_07(Event):
    def parse(self,bytes):
        self.name = 'unknown0207'
        self.bytes += bytes.skip(4,byteCode=True)
        
class UnknownEvent_04_X2(Event):
    def parse(self,bytes):
        self.name = 'unknown04X2'
        self.bytes += bytes.skip(2,byteCode=True)
        
class UnknownEvent_04_16(Event):
    def parse(self,bytes):
        self.name = 'unknown0416'
        self.bytes += bytes.skip(24,byteCode=True)
        
class UnknownEvent_04_C6(Event):
    def parse(self,bytes):
        self.name = 'unknown04C6'
        self.bytes += bytes.skip(16,byteCode=True)
        
class UnknownEvent_04_18or87(Event):
    def parse(self,bytes):
        self.name = 'unknown0418-87'
        self.bytes += bytes.skip(4,byteCode=True)
        
class UnknownEvent_04_00(Event):
    def parse(self,bytes):
        self.name = 'unknown0400'
        self.bytes += byes.skip(10,byteCode=True)
        
class UnknownEvent_05_89(Event):
    def parse(self,bytes):
        self.name = 'unknown0589'
        self.bytes += bytes.skip(4,byteCode=True)
