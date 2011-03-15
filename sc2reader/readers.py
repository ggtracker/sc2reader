from datetime import datetime

from sc2reader.parsers import *
from sc2reader.objects import *
from sc2reader.utils import ByteStream

class Reader(object):
    def reads(self, build):
        raise NotYetImplemented("This should return true if it parses they key, false if it doesn't")
    
    def read(bytes,object):
        raise NotYetImplemented("This should parse the bytes and return the populated object")
		
class ReplayInitDataReader(Reader):
    def reads(self, build):
        return True
        
    def read(self, filecontents, replay):
        bytes = ByteStream(filecontents)
        num_people = bytes.get_big_8()
        for p in range(1, num_people+1):
            name = bytes.get_string(bytes.get_big_8())
            
            if len(name) > 0:
                replay.player_names.append(name)
                
            bytes.skip(5) #Always all zeros
        
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
class AttributeEventsReader(object):
    def reads(self, build):
        return build < 17326
        
    def read(self, filecontents, replay):
        bytes = ByteStream(filecontents)
		
        self.load_header(replay, bytes)
        
        replay.attributes = list()
        data = defaultdict(dict)
        for i in range(0, bytes.get_little_32()):
            replay.attributes.append(self.load_attribute(replay, bytes))
            
    def load_header(self, replay, bytes):
        bytes.get_little_bytes(4)
        
    def load_attribute(self, replay, bytes):
        #Get the attribute data elements
        attr_data = [
                bytes.get_little_32(),                  #Header
                bytes.get_little_32(),                  #Attr Id
                bytes.get_little_8(),                   #Player
                bytes.get_little_bytes(4).encode("hex") #Value
            ]

        #Complete the decoding in the attribute object
        return Attribute(attr_data)

class AttributeEventsReader_17326(AttributeEventsReader):
    def reads(self, build):
        return build >= 17326

    def load_header(self, replay, bytes):
        bytes.get_little_bytes(5)
        
##################################################
# replay.details parsing classes
##################################################
class ReplayDetailsReader(Reader):
    def reads(self, build):
        return True
    
    def read(self, filecontents, replay):
        data =  ByteStream(filecontents).parse_serialized_data()

        for pid, pdata in enumerate(data[0]):
            replay.players.append(Player(pid+1, pdata, replay.realm)) #pid's start @ 1
            
        replay.map = data[1].decode("hex")
        replay.file_time = data[5]

        # TODO: This doesn't seem to produce exactly correct results, ie. often off by one
        # second compared to file timestamps reported by Windows.
        # This might be due to wrong value of the magic constant 116444735995904000
        # or rounding errors. Ceiling or Rounding the result didn't produce consistent
        # results either.
        replay.date = datetime.fromtimestamp((replay.file_time-116444735995904000)/10000000)
        replay.utc_date = datetime.utcfromtimestamp((replay.file_time-116444735995904000)/10000000)
        
        replay.details_data = data

##################################################
# replay.message.events parsing classes
##################################################
class MessageEventsReader(Reader):
    def reads(self, build):
        return True
    
    def read(self, filecontents, replay):
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
                    replay.other_people.add(player_id)
            
            elif flags & 0x80 == 0:
                target = flags & 0x03
                length = bytes.get_big_8()
                
                if flags & 0x08:
                    length += 64
                    
                if flags & 0x10:
                    length += 128
                    
                text = bytes.get_string(length)
                replay.messages.append(Message(time, player_id, target, text))

####################################################
# replay.game.events parsing classes
####################################################
class GameEventsReader(object):
    def reads(self, build):
        return build < 16561

    def read(self, filecontents, replay):
        #set up an event list, start the timer, and process the file contents
        replay.events, frames, bytes = list(), 0, ByteStream(filecontents)
        
        while bytes.remaining > 0:
            #Save the start so we can trace for debug purposes
            start = bytes.cursor

            #First section is always a timestamp marking the elapsed time
            #since the last eventObjectlisted
            new_frames = bytes.get_timestamp()
            frames += new_frames
            
            #Next is a compound byte where the first 3 bits XXX00000 mark the
            #event_type, the 4th bit 000X0000 marks the eventObjectas local or global,
            #and the remaining bits 0000XXXX mark the player id number.
            #The following byte completes the unique eventObjectidentifier
            first, event_code = bytes.get_big_8(), bytes.get_big_8()
            event_type, pid = first >> 5, first & 0x1F
            
            if event_type not in self.parsers.keys():
                msg = "Unknown event_type: %s at location %s"
                raise TypeError(msg % (hex(event_type),hex(start)))
                
            for parser, loads in self.parsers[event_type]:
                if loads(event_code):
                    event =  parser.load(bytes, frames, event_type, event_code, pid)
                    event.bytes = bytes.get_range(start,bytes.cursor)
                    replay.events.append(event)
                    break
            else:
                raise TypeError("Unknown event: %s - %s at %s" % (hex(event_type), hex(event_code), hex(start)))
            
    def __init__(self):
        self.parsers = {
            0x00: [
                (PlayerJoinEventParser(), lambda code: code == 0x0B ),
                (GameStartEventParser(), lambda code: code == 0x05 ),],
            0x01: [
                (PlayerLeaveEventParser(), lambda code: code == 0x09 ),
                (AbilityEventParser(), lambda code: code & 0x0F == 0xB and code >> 4 <= 0x9 ),
                (SelectionEventParser(), lambda code: code & 0x0F == 0xC and code >> 4 <= 0xA ),
                (HotkeyEventParser(), lambda code: code & 0x0F == 0xD and code >> 4 <= 0x9 ),
                (ResourceTransferEventParser(), lambda code: code & 0x0F == 0xF and code >> 4 <= 0x9 ),],
            0x02: [
                (UnknownEventParser_0206(), lambda code: code == 0x06 ),
                (UnknownEventParser_0207(), lambda code: code == 0x07 ),
                (UnknownEventParser_020E(), lambda code: code == 0x0E ),],
            0x03: [
                (CameraMovementEventParser_87(), lambda code: code == 0x87 ),
                (CameraMovementEventParser_08(), lambda code: code == 0x08 ),
                (CameraMovementEventParser_18(), lambda code: code == 0x18 ),
                (CameraMovementEventParser_X1(), lambda code: code & 0x0F == 1 ),],
            0x04: [
                (UnknownEventParser_04X2(), lambda code: code & 0x0F == 2 ),
                (UnknownEventParser_0416(), lambda code: code == 0x16 ),
                (UnknownEventParser_04C6(), lambda code: code == 0xC6 ),
                (UnknownEventParser_0487(), lambda code: code == 0x87 ),
                (UnknownEventParser_0400(), lambda code: code == 0x00 ),],
            0x05: [
                (UnknownEventParser_0589(), lambda code: code == 0x89 ),],
        }
    
class GameEventsReader_16561(GameEventsReader):
    def reads(self, build):
        return 16561 <= build < 17326
    
    def __init__(self):
        self.parsers = {
            0x00: [
                (PlayerJoinEventParser(), lambda code: code == 0x0B ),
                (GameStartEventParser(), lambda code: code == 0x05 ),],
            0x01: [
                (PlayerLeaveEventParser(), lambda code: code == 0x09 ),
                (AbilityEventParser_16561(), lambda code: code & 0x0F == 0xB and code >> 4 <= 0x9 ),
                (SelectionEventParser_16561(), lambda code: code & 0x0F == 0xC and code >> 4 <= 0xA ),
                (HotkeyEventParser_16561(), lambda code: code & 0x0F == 0xD and code >> 4 <= 0x9 ),
                (ResourceTransferEventParser_16561(), lambda code: code & 0x0F == 0xF and code >> 4 <= 0x8 ),],
            0x02: [
                (UnknownEventParser_0206(), lambda code: code == 0x06 ),
                (UnknownEventParser_0207(), lambda code: code == 0x07 ),
                (UnknownEventParser_020E(), lambda code: code == 0x0E ),],
            0x03: [
                (CameraMovementEventParser_87(), lambda code: code == 0x87 ),
                (CameraMovementEventParser_08(), lambda code: code == 0x08 ),
                (CameraMovementEventParser_18(), lambda code: code == 0x18 ),
                (CameraMovementEventParser_X1(), lambda code: code & 0x0F == 1 ),],
            0x04: [
                (UnknownEventParser_0487(), lambda code: code == 0x87 ),
                (UnknownEventParser_04C6(), lambda code: code == 0xC6 ),
                (UnknownEventParser_04XC(), lambda code: code & 0x0F == 0x0C ),],
            0x05: [
                (UnknownEventParser_0589(), lambda code: code == 0x89 ),],
        }

class GameEventsReader_17326(GameEventsReader):
    def reads(self, build):
        return build >= 17326
    
    def __init__(self):
        self.parsers = {
            0x00: [
                (PlayerJoinEventParser(), lambda code: code == 0x0C or code == 0x2C ),
                (GameStartEventParser(), lambda code: code == 0x05 ),],
            0x01: [
                (PlayerLeaveEventParser(), lambda code: code == 0x09 ),
                (AbilityEventParser_16561(), lambda code: code & 0x0F == 0xB and code >> 4 <= 0x9 ),
                (SelectionEventParser_16561(), lambda code: code & 0x0F == 0xC and code >> 4 <= 0xA ),
                (HotkeyEventParser_16561(), lambda code: code & 0x0F == 0xD and code >> 4 <= 0x9 ),
                (ResourceTransferEventParser_16561(), lambda code: code & 0x0F == 0xF and code >> 4 <= 0x9 ),],
            0x02: [
                (UnknownEventParser_0206(), lambda code: code == 0x06 ),
                (UnknownEventParser_0207(), lambda code: code == 0x07 ),
                (UnknownEventParser_020E(), lambda code: code == 0x0E ),],
            0x03: [
                (CameraMovementEventParser_87(), lambda code: code == 0x87 ),
                (CameraMovementEventParser_08(), lambda code: code == 0x08 ),
                (CameraMovementEventParser_18(), lambda code: code == 0x18 ),
                (CameraMovementEventParser_X1(), lambda code: code & 0x0F == 1 ),],
            0x04: [
                (UnknownEventParser_0487(), lambda code: code == 0x87 ),
                (UnknownEventParser_04C6(), lambda code: code == 0xC6 ),
                (UnknownEventParser_04XC(), lambda code: code & 0x0F == 0x0C ),],
            0x05: [
                (UnknownEventParser_0589(), lambda code: code == 0x89 ),],
        }

"""I don't know if these are actually needed yet
            (UnknownEventParser_04X2(), lambda code: code & 0x0F == 2 ),
            (UnknownEventParser_0416(), lambda code: code == 0x16 ),
            (UnknownEventParser_0400(), lambda code: code == 0x00 ),
"""