from time import ctime
from collections import defaultdict

from objects import Attribute, Message, Player, Event
from eventparsers import *
from utils import ByteStream
from exceptions import ParseError

from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

#################################################
# Parser Dispatch Functions
#################################################
def get_detail_parser(build):
    #This file format appears to have never changed
    return DetailParser()
    
def get_attribute_parser(build):
    if build >= 17326:
        return AttributeParser_17326()
    
    #All versions prior to 17326 have been the same
    return AttributeParser()
    
def get_event_parser(build):
    if build >= 17326:
        return EventParser_17326()
    if build >= 16561:
        return EventParser_16561()
    
    #All versions prior to 16561 appear to be the same
    return EventParser()
    
def get_message_parser(build):
    #format appears to have not changed
    return MessageParser()

def get_initdata_parser(build):
    return InitdataParser()
    
class InitdataParser(object):
    def load(self,replay,filecontents):
        bytes = ByteStream(filecontents)
        num_players = bytes.get_big_8()
        for p in range(0,num_players):
            name_length = bytes.get_big_8()
            name = bytes.get_string(name_length)
            bytes.skip(5)
        
        bytes.skip(5) # Unknown
        bytes.get_string(4) # Always Dflt
        bytes.skip(15) #Unknown
        id_length = bytes.get_big_8()
        sc_account_id = bytes.get_string(id_length)
        bytes.skip(684) # Fixed Length data for unknown purpose
        while( bytes.get_string(4).lower() == 's2ma' ):
            bytes.skip(2)
            replay.realm = bytes.get_string(2).lower()
            unknown_map_hash = bytes.get_bytes(32)
            
#################################################
# replay.attributes.events Parsing classes
#################################################
class AttributeParser(object):
    def load_header(self, replay, bytes):
        bytes.skip(4)              #Always start with 4 nulls
        self.count = bytes.get_little_32()       #get total attribute count
    
    def load_attribute(self, replay, bytes):
        #Get the attribute data elements
        attr_data = [
                bytes.get_little_32(),                  #Header
                bytes.get_little_32(),                  #Attr Id
                bytes.get_little_8(),                   #Player
                bytes.get_little_bytes(4).encode("hex")  #Value
            ]

        #Complete the decoding in the attribute object
        return Attribute(attr_data)
        
    def load(self, replay, filecontents):
        bytes = ByteStream(filecontents)
		
        self.load_header(replay, bytes)
        
        replay.attributes = list()
        data = defaultdict(dict)
        for i in range(0, self.count):
            attr = self.load_attribute(replay, bytes)
            replay.attributes.append(attr)

            # Uknown attributes get named as such and are not stored
            # because we don't know what they are
            # Index by player,  then name for ease of access later on
            if attr.name != "Unknown":
                data[attr.player][attr.name] = attr.value
            
        #Get global settings first
        replay.speed = data[16]['Game Speed']
        
        #TODO: Do we need the category variable at this point?
        replay.category = data[16]['Category']
        replay.is_ladder = (replay.category == "Ladder")
        replay.is_private = (replay.category == "Private")
        
        replay.type = data[16]['Game Type']

        #Set player attributes as available,  requires already populated player list
        for pid, attributes in data.iteritems():
            if pid == 16: continue
            player = replay.player[pid]
            player.color = attributes['Color']
            player.team = attributes['Teams'+replay.type]
            player.choosen_race = attributes['Race']
            player.difficulty = attributes['Difficulty']
            #Computer players can't record games
            player.type = attributes['Player Type']
            if player.type == "Computer":
                player.recorder = False

class AttributeParser_17326(AttributeParser):
	def load_header(self, replay, bytes):
		bytes.skip(5)              #Always start with 4 nulls
		self.count = bytes.get_little_32()       #get total attribute count

##################################################
# replay.details parsing classes
##################################################
class DetailParser(object):
    def load(self, replay, filecontents):
        data =  ByteStream(filecontents).parse_serialized_data()
        
        for pid, pdata in enumerate(data[0]):
            replay.add_player(Player(pid+1, pdata, replay.realm)) #shift the id to start @ 1
            
        replay.map = data[1].decode("hex")
        replay.file_time = data[5]
        replay.date = ctime( (data[5]-116444735995904000)/10000000 )
        
        replay.details_data = data

##################################################
# replay.message.events parsing classes
##################################################
class MessageParser(object):
    def load(self, replay, filecontents):
        replay.messages = list()
        bytes, time = ByteStream(filecontents), 0

        while(bytes.remaining!=0):
            time += bytes.get_timestamp()
            player_id = bytes.get_big_8() & 0x0F
            flags = bytes.get_big_8()
            
            if flags & 0xF0 == 0x80:
            
                #ping or something?
                if flags & 0x0F == 3:
                    bytes.skip(8)

                #some sort of header code
                elif flags & 0x0F == 0:
                    bytes.skip(4)
                    if player_id <= len(replay.players):
                        replay.player[player_id].recorder = False
                    else:
                        pass #This "player" is an observer or something
            
            elif flags & 0x80 == 0:
                target = flags & 0x03
                length = bytes.get_big_8()
                
                if flags & 0x08:
                    length += 64
                    
                if flags & 0x10:
                    length += 128
                    
                text = bytes.get_string(length)
                replay.messages.append(Message(time, replay.player[player_id], target, text))
            
        recorders = [player for player in replay.players if player and player.recorder==True]
        if len(recorders) > 1:
            raise ValueError("There should be 1 and only 1 recorder; %s were found" % len(recorders))
        elif len(recorders) == 0:
            #If there are no recorders,  then the recorder must not be a player,  spectator or referee then
            replay.recorder = None
        else:
            replay.recorder = recorders[0]

####################################################
# replay.game.events parsing classes
####################################################
class EventParser(object):
    parser_map = {
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
            (UnknownEventParser_0487(), lambda e: e.code == 0x87 ),
            (UnknownEventParser_0400(), lambda e: e.code == 0x00 ),],
        0x05: [
            (UnknownEventParser_0589(), lambda e: e.code == 0x89 ),],
    }

    def load(self, replay, filecontents):
        #set up an event list,  start the timer,  and process the file contents
        replay.events, elapsed_time, bytes = list(), 0, ByteStream(filecontents)
        
        while bytes.remaining > 0:
            #First section is always a timestamp marking the elapsed time
            #since the last eventObjectlisted
            location = hex(bytes.cursor)
            time_diff, event_bytes = bytes.get_timestamp(byte_code=True)
            elapsed_time += time_diff
            
            event_bytes += bytes.peek(2)
            #Next is a compound byte where the first 3 bits XXX00000 mark the
            #event_type,  the 4th bit 000X0000 marks the eventObjectas local or global, 
            #and the remaining bits 0000XXXX mark the player id number.
            #The following byte completes the unique eventObjectidentifier
            first, event_code = bytes.get_big_8(), bytes.get_big_8()
            event_type, global_flag, player_id = first >> 5, first & 0x10, first & 0xF

            #Create a barebones event from the gathered information
            event = Event(elapsed_time, event_type, event_code, 
                        global_flag, player_id, location, event_bytes)
            
            try:
                #Get the parser and load the data into the event
                replay.events.append(self.get_parser(event).load(event, bytes))
            except TypeError as e:
                raise ParseError(e.message, replay, event, bytes)
            
    def get_parser(self, event):
        if event.type not in self.parser_map.keys():
            raise TypeError("Unknown event_type: %s at location %s" % (hex(event.type), event.location))
		
        for parser, accept in self.parser_map[event.type]:
            if accept(event):
                return parser
        
        raise TypeError("Unknown event: %s - %s at %s" % (hex(event.type), hex(event.code), event.location))

class EventParser_16561(EventParser):
    parser_map = {
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
            (UnknownEventParser_0487(), lambda e: e.code == 0x87 ),
            (UnknownEventParser_04C6(), lambda e: e.code == 0xC6 ),
            (UnknownEventParser_04XC(), lambda e: e.code & 0x0F == 0x0C ),],
        0x05: [
            (UnknownEventParser_0589(), lambda e: e.code == 0x89 ),],
    }

"""
            (UnknownEventParser_04X2(), lambda e: e.code & 0x0F == 2 ),
            (UnknownEventParser_0416(), lambda e: e.code == 0x16 ),
            (UnknownEventParser_0400(), lambda e: e.code == 0x00 ),



            (UnknownEventParser_04X2(), lambda e: e.code & 0x0F == 2 ),
            (UnknownEventParser_0416(), lambda e: e.code == 0x16 ),
            (UnknownEventParser_0400(), lambda e: e.code == 0x00 ),
"""

class EventParser_17326(EventParser):
	parser_map = {
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
            (UnknownEventParser_0487(), lambda e: e.code == 0x87 ),
            (UnknownEventParser_04C6(), lambda e: e.code == 0xC6 ),
            (UnknownEventParser_04XC(), lambda e: e.code & 0x0F == 0x0C ),],
        0x05: [
            (UnknownEventParser_0589(), lambda e: e.code == 0x89 ),],
    }