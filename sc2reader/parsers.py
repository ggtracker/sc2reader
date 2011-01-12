from time import ctime
from collections import defaultdict

from objects import Attribute,Message,Player,Event
from utils import ByteStream
from data import abilities

def getDetailParser(build):
    return DetailParser()
    
def getAttributeParser(build):
    return AttributeParser()
    
def getEventParser(build):
    return EventParser()
    
def getMessageParser(build):
    return MessageParser()
		
		
class AttributeParser(object):
    def load(self,replay,filecontents):
        bytes = ByteStream(filecontents)
        bytes.skip(4,byteCode=True)                      #Always start with 4 nulls
        size = bytes.getLittleInt(4)       #get total attribute count

        replay.attributes = list()
        data = defaultdict(dict)
        for i in range(0,size):
            #Get the attribute data elements
            attr_data = [
                    bytes.getBig(4),        #Header
                    bytes.getLittleInt(4),  #Attr Id
                    bytes.getBigInt(1),      #Player
                    bytes.getLittle(4)      #Value
                ]

            #Complete the decoding in the attribute object
            attr = Attribute(attr_data)
            replay.attributes.append(attr)

            #Uknown attributes get named as such and are not stored
            #Index by player, then name for ease of access later on
            if attr.name != "Unknown":
                data[attr.player][attr.name] = attr.value
            
        #Get global settings first
        replay.speed = data[16]['Game Speed']
        replay.category = data[16]['Category']
        replay.type = data[16]['Game Type']

        #Set player attributes as available, requires already populated player list
        for pid,attributes in data.iteritems():
            if pid == 16: continue
            player = replay.players[pid]
            player.color = attributes['Color']
            player.team = attributes['Teams'+replay.type]
            player.race2 = attributes['Race']
            player.difficulty = attributes['Difficulty']

            #Computer players can't record games
            player.type = attributes['Player Type']
            if player.type == "Computer":
                player.recorder = False

class DetailParser(object):
    def load(self,replay,filecontents):
        data =  ByteStream(filecontents).parseSerializedData()

        replay.players = [None] #Pad the front for proper IDs
        for pid,pdata in enumerate(data[0]):
            replay.players.append(Player(pid+1,pdata)) #shift the id to start @ 1
            
        replay.map = data[1].decode("hex")
        replay.file_time = data[5]
        replay.date = ctime( (data[5]-116444735995904000)/10000000 )


class MessageParser(object):
    def load(self,replay,filecontents):
        replay.messages = list()
        bytes,time = ByteStream(filecontents),0

        while(bytes.length!=0):
            time += bytes.getTimestamp()
            playerId = bytes.getBigInt(1) & 0x0F
            flags = bytes.getBigInt(1)
            
            if flags & 0xF0 == 0x80:
            
                #ping or something?
                if flags & 0x0F == 3:
                    bytes.skip(8)

                #some sort of header code
                elif flags & 0x0F == 0:
                    bytes.skip(4)
                    replay.players[playerId].recorder = False
            
            elif flags & 0x80 == 0:
                replay.messages.append(Message(time,playerId,flags,bytes))
            
        recorders = [player for player in replay.players if player and player.recorder==True]
        if len(recorders) != 1:
            raise ValueError("There should be 1 and only 1 recorder; %s were found" % len(recorders))
        replay.recorder = recorders[0]

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
        
class PlayerLeaveEventParser(object):
    def load(self,event,bytes):
        #print "Time %s - Player %s has left the game" % (self.time,self.player)
        event.name = 'leave'
        return event
    
class WierdInitializationEventParser(object):
    def load(self,event,bytes):
        event.bytes += bytes.skip(19,byteCode=True)
        #print "Time %s - Wierd Initialization Event" % (self.time)
        event.name = 'weird'
        return event
        
        
class AbilityEventParser(object):
    def load(self,event,bytes):
        event.bytes += bytes.peek(5)
        first,atype = (bytes.getBigInt(1),bytes.getBigInt(1))
        event.ability = bytes.getBigInt(1) << 16 | bytes.getBigInt(1) << 8 | (bytes.getBigInt(1) & 0x3F)
        
        if event.ability in abilities:
            event.abilitystr = abilities[event.ability]
        else: 
            if atype == 0x20 or atype == 0x22: pause = True
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
            
        #deselection by byte counted indicators
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
    def load(self,event,bytes):
        event.name = 'hotkey'
        #print "Time %s - Player %s is using hotkey %s" % (self.timestr,self.player,eventCode >> 4)
        first,byte = bytes.getBigInt(1,byteCode=True)
        event.bytes += byte
        
        if first > 0x03:
            second,byte = bytes.getBigInt(1,byteCode=True)
            event.bytes += byte
            
            if first & 0x08:
                event.bytes += bytes.skip(second & 0x0F,byteCode=True)
            else:
                extras = first >> 3
                event.bytes += bytes.skip(extras,byteCode=True)
                #event.bytes += bytes.getBig(1) #Not sure why this is here, works fine w/out it?
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
        else:
            pass #print "No data associated with hotkey"
            
        return event
            
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

class CameraMovementEventParser_87(object):
    def load(self,event,bytes):
        event.name = 'cameramovement'
        event.bytes += bytes.skip(8,byteCode=True)
        return event

class CameraMovementEventParser_08(object):
    def load(self,event,bytes):
        event.name = 'cameramovement'
        event.bytes += bytes.skip(10,byteCode=True)
        return event
        
class CameraMovementEventParser_18(object):
    def load(self,event,bytes):
        event.name = 'cameramovement'
        event.bytes += bytes.skip(162,byteCode=True)
        return event
        
class CameraMovementEventParser_X1(object):
    def load(self,event,bytes):
        event.name = 'cameramovement'
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
        event.bytes += bytes.skip(16,byteCode=True)
        return event
        
class UnknownEventParser_0418or87(object):
    def load(self,event,bytes):
        event.name = 'unknown0418-87'
        event.bytes += bytes.skip(4,byteCode=True)
        return event
        
class UnknownEventParser_0400(object):
    def load(self,event,bytes):
        event.name = 'unknown0400'
        event.bytes += bytes.skip(10,byteCode=True)
        return event
        
class UnknownEventParser_0589(object):
    def load(self,event,bytes):
        event.name = 'unknown0589'
        event.bytes += bytes.skip(4,byteCode=True)
        return event
        
        
class EventParser(object):
    parserMap_pre16561 = {
        #Before I can fill this out I need to make a couple more event parsers
    }

    parserMap_post16561 = {
        0x00: [
            (PlayerJoinEventParser(), lambda e: e.code == 0x1B or e.code == 0x20 or e.code == 0x0B ),
            (GameStartEventParser(), lambda e: e.code == 0x05 ),
            (WierdInitializationEventParser(), lambda e: e.code == 0x15 )],
        0x01: [
            (PlayerLeaveEventParser(), lambda e: e.code == 0x09 ),
            (AbilityEventParser(), lambda e: e.code & 0x0F == 0xB and e.code >> 4 <= 0x9 ),
            (SelectionEventParser(), lambda e: e.code & 0x0F == 0xC and e.code >> 4 <= 0xA ),
            (HotkeyEventParser(), lambda e: e.code & 0x0F == 0xD and e.code >> 4 <= 0x9 ),
            (ResourceTransferEventParser(), lambda e: e.code & 0x0F == 0xF and e.code >> 4 <= 0x9 ),],
        0x02: [
            (UnknownEventParser_0206(), lambda e: e.code == 0x06 ),
            (UnknownEventParser_0207(), lambda e: e.code == 0x07 ),],
        0x03: [
            (CameraMovementEventParser_87(), lambda e: e.code == 0x87 ),
            (CameraMovementEventParser_08(), lambda e: e.code == 0x08 ),
            (CameraMovementEventParser_18(), lambda e: e.code == 0x18 ),
            (CameraMovementEventParser_X1(), lambda e: e.code & 0x0F == 1 ),],
        0x04: [
            (UnknownEventParser_04X2(), lambda e: e.code & 0x0F == 2 ),
            (UnknownEventParser_0416(), lambda e: e.code == 0x16 ),
            (UnknownEventParser_04C6(), lambda e: e.code == 0xC6 ),
            (UnknownEventParser_0418or87(), lambda e: e.code == 0x18 or e.code == 0x87 ),
            (UnknownEventParser_0400(), lambda e: e.code == 0x00 ),],
        0x05: [
            (UnknownEventParser_0589(), lambda e: e.code == 0x89 ),],
    }

    def load(self,replay,filecontents):
        #Set the correct parsermap based on the replay build number
        if replay.build < 16561:
            raise TypeError("Cannot currently parse pre-16561 build game.events files")
        elif replay.build >= 16561:
            self.parserMap = self.parserMap_post16561
        
        #set up an event list, start the timer, and process the file contents
        replay.events,elapsedTime,bytes = list(),0,ByteStream(filecontents)
        
        while bytes.length > 0:
            #First section is always a timestamp marking the elapsed time
            #since the last eventObjectlisted
            location = hex(bytes.cursor)
            timeDiff,eventBytes = bytes.getTimestamp(byteCode=True)
            elapsedTime += timeDiff
            
            eventBytes += bytes.peek(2)
            #Next is a compound byte where the first 3 bits XXX00000 mark the
            #eventType, the 4th bit 000X0000 marks the eventObjectas local or global,
            #and the remaining bits 0000XXXX mark the player id number.
            #The following byte completes the unique eventObjectidentifier
            first,eventCode = bytes.getBigInt(1),bytes.getBigInt(1)
            eventType,globalFlag,playerId = first >> 5,first & 0x10,first & 0xF
            
            #Create a barebones event from the gathered information
            event = Event(elapsedTime,eventType,eventCode,
                        globalFlag,playerId,location,eventBytes)
            
            #Get the parser and load the data into the event
            replay.events.append(self.getParser(event).load(event,bytes))
    
    def getParser(self,event):
        if event.type not in self.parserMap.keys():
            raise TypeError("Unknown eventType: %s at location %s" % (hex(event.type),event.location))
		
        for parser,accept in self.parserMap[event.type]:
            if accept(event): return parser
        
        raise TypeError("Unknown event: %s - %s at %s" % (hex(event.type),hex(event.code),event.location))
        
