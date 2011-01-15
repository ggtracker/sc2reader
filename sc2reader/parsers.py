from time import ctime
from collections import defaultdict

from objects import Attribute,Message,Player,Event
from eventparsers import *
from utils import ByteStream

#################################################
# Parser Dispatch Functions
#################################################
def getDetailParser(build):
    #This file format appears to have never changed
    return DetailParser()
    
def getAttributeParser(build):
    if build >= 17326:
        return AttributeParser_17326()
    
    #All versions prior to 17326 have been the same
    return AttributeParser()
    
def getEventParser(build):
    if build >= 17326:
        return EventParser_17326()
    if build >= 16561:
        return EventParser_16561()
    
    #All versions prior to 16561 appear to be the same
    return EventParser()
    
def getMessageParser(build):
    #format appears to have not changed
    return MessageParser()

#################################################
# replay.attributes.events Parsing classes
#################################################
class AttributeParser(object):
    def loadHeader(self,replay,bytes):
        bytes.skip(4,byteCode=True)              #Always start with 4 nulls
        self.count = bytes.getLittleInt(4)       #get total attribute count
    
    def loadAttribute(self,replay,bytes):
        #Get the attribute data elements
        attr_data = [
                bytes.getBig(4),        #Header
                bytes.getLittleInt(4),  #Attr Id
                bytes.getBigInt(1),      #Player
                bytes.getLittle(4)      #Value
            ]

        #Complete the decoding in the attribute object
        return Attribute(attr_data)
        
    def load(self,replay,filecontents):
        bytes = ByteStream(filecontents)
		
        self.loadHeader(replay,bytes)
        
        replay.attributes = list()
        data = defaultdict(dict)
        for i in range(0,self.count):
            attr = self.loadAttribute(replay,bytes)
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

class AttributeParser_17326(AttributeParser):
	def loadHeader(self,replay,bytes):
		bytes.skip(5,byteCode=True)              #Always start with 4 nulls
		self.count = bytes.getLittleInt(4)       #get total attribute count

##################################################
# replay.details parsing classes
##################################################
class DetailParser(object):
    def load(self,replay,filecontents):
        data =  ByteStream(filecontents).parseSerializedData()
        
        replay.players = [None] #Pad the front for proper IDs
        for pid,pdata in enumerate(data[0]):
            replay.players.append(Player(pid+1,pdata)) #shift the id to start @ 1
            
        replay.map = data[1].decode("hex")
        replay.file_time = data[5]
        replay.date = ctime( (data[5]-116444735995904000)/10000000 )

##################################################
# replay.message.events parsing classes
##################################################
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
                    if playerId < len(replay.players):
                        replay.players[playerId].recorder = False
                    else:
                        pass #This "player" is an observer or something
            
            elif flags & 0x80 == 0:
                target = flags & 0x03
                length = bytes.getBigInt(1)
                
                if flags & 0x08:
                    length += 64
                    
                if flags & 0x10:
                    length += 128
                    
                text = bytes.getString(length)
                replay.messages.append(Message(time,playerId,target,text))
            
        recorders = [player for player in replay.players if player and player.recorder==True]
        if len(recorders) != 1:
            raise ValueError("There should be 1 and only 1 recorder; %s were found" % len(recorders))
        replay.recorder = recorders[0]

####################################################
# replay.game.events parsing classes
####################################################
class EventParser(object):
    parserMap = {
        0x00: [
            (PlayerJoinEventParser(), lambda e: e.code == 0x0B ),
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

class EventParser_16561(EventParser):
    parserMap = {
        0x00: [
            (PlayerJoinEventParser(), lambda e: e.code == 0x0B ),
            (GameStartEventParser(), lambda e: e.code == 0x05 ),
            (WierdInitializationEventParser(), lambda e: e.code == 0x15 )],
        0x01: [
            (PlayerLeaveEventParser(), lambda e: e.code == 0x09 ),
            (AbilityEventParser_16561(), lambda e: e.code & 0x0F == 0xB and e.code >> 4 <= 0x9 ),
            (SelectionEventParser_16561(), lambda e: e.code & 0x0F == 0xC and e.code >> 4 <= 0xA ),
            (HotkeyEventParser_16561(), lambda e: e.code & 0x0F == 0xD and e.code >> 4 <= 0x9 ),
            (ResourceTransferEventParser_16561(), lambda e: e.code & 0x0F == 0xF and e.code >> 4 <= 0x8 ),],
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

class EventParser_17326(EventParser):
	parserMap = {
        0x00: [
            (PlayerJoinEventParser(), lambda e: e.code == 0x0C or e.code == 0x2C ),
            (GameStartEventParser(), lambda e: e.code == 0x05 ),
            (WierdInitializationEventParser(), lambda e: e.code == 0x15 )],
        0x01: [
            (PlayerLeaveEventParser(), lambda e: e.code == 0x09 ),
            (AbilityEventParser_16561(), lambda e: e.code & 0x0F == 0xB and e.code >> 4 <= 0x9 ),
            (SelectionEventParser_16561(), lambda e: e.code & 0x0F == 0xC and e.code >> 4 <= 0xA ),
            (HotkeyEventParser_16561(), lambda e: e.code & 0x0F == 0xD and e.code >> 4 <= 0x9 ),
            (ResourceTransferEventParser_16561(), lambda e: e.code & 0x0F == 0xF and e.code >> 4 <= 0x9 ),],
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
            (UnknownEventParser_0400(), lambda e: e.code == 0x00 ),
            (UnknownEventParser_041C(), lambda e: e.code == 0x1C ),],
        0x05: [
            (UnknownEventParser_0589(), lambda e: e.code == 0x89 ),],
    }