from datetime import datetime

from sc2reader.parsers import *
from sc2reader.objects import *
from sc2reader.utils import ReplayBuffer, LITTLE_ENDIAN, BIG_ENDIAN
from sc2reader.utils import key_in_bases, timestamp_from_windows_time

#####################################################
# Metaclass used to help enforce the usage contract
#####################################################
class MetaReader(type):
    def __new__(meta, class_name, bases, class_dict):
        if class_name != "Reader": #Parent class is exempt from checks
            assert 'file' in class_dict or key_in_bases('file',bases), \
                "%s must define the name of the file it reads" % class_name

            assert 'reads' in class_dict or key_in_bases('reads',bases), \
                "%s must define the 'boolean reads(self,build)' member" % class_name

            assert 'read' in class_dict or key_in_bases('read',bases), \
                "%s must define the 'void read(self, filecontents, replay)' member" % class_name

        return type.__new__(meta, class_name, bases, class_dict)

class Reader(object):
    __metaclass__ = MetaReader
		
#################################################

class ReplayInitDataReader(Reader):
    file = 'replay.initData'

    def reads(self, build):
        return True
        
    def read(self, filecontents, replay):
        buffer = ReplayBuffer(filecontents)
        
        for p in range(buffer.read_byte()):
            name = buffer.read_string()
            if len(name) > 0:
                replay.player_names.append(name)
                
            buffer.skip(5) #Always all zeros
        
        buffer.skip(5) # Unknown
        buffer.read_chars(4) # Always Dflt
        buffer.skip(15) #Unknown
        sc_account_id = buffer.read_string()
        
        buffer.skip(684) # Fixed Length data for unknown purpose
        
        while( buffer.read_chars(4).lower() == 's2ma' ):
            buffer.skip(2)
            replay.realm = buffer.read_string(2).lower()
            unknown_map_hash = buffer.read_chars(32)
            
#################################################

class AttributeEventsReader(Reader):
    file = 'replay.attributes.events'
    def reads(self, build):
        return build < 17326
        
    def read(self, filecontents, replay):
        buffer = ReplayBuffer(filecontents)
		
        self.load_header(replay, buffer)
        
        replay.attributes = list()
        for i in range(0, buffer.read_int(LITTLE_ENDIAN)):
            replay.attributes.append(Attribute([
                    buffer.read_int(LITTLE_ENDIAN),                  #Header
                    buffer.read_int(LITTLE_ENDIAN),                  #Attr Id
                    buffer.read_byte(),                              #Player
                    buffer.read_chars(4) #Value
                ]))
            
    def load_header(self, replay, buffer):
        buffer.read_chars(4,LITTLE_ENDIAN)

class AttributeEventsReader_17326(AttributeEventsReader):
    def reads(self, build):
        return build >= 17326

    def load_header(self, replay, buffer):
        buffer.read_chars(5,LITTLE_ENDIAN)
        
##################################################

class ReplayDetailsReader(Reader):
    file = 'replay.details'

    def reads(self, build):
        return True
    
    def read(self, filecontents, replay):
        print "STARTING DETAILS!!!!!!!!!!!!!"
        data =  ReplayBuffer(filecontents).read_data_struct()

        for pid, pdata in enumerate(data[0]):
            replay.players.append(Player(pid+1, pdata, replay.realm)) #pid's start @ 1
            
        replay.map = data[1]
        replay.file_time = data[5]

        # TODO: This doesn't seem to produce exactly correct results, ie. often off by one
        # second compared to file timestamps reported by Windows.
        # This might be due to wrong value of the magic constant 116444735995904000
        # or rounding errors. Ceiling or Rounding the result didn't produce consistent
        # results either.
        unix_timestamp = timestamp_from_windows_time(replay.file_time)
        replay.date = datetime.fromtimestamp(unix_timestamp)
        replay.utc_date = datetime.utcfromtimestamp(unix_timestamp)

##################################################

class MessageEventsReader(Reader):
    file = 'replay.message.events'

    def reads(self, build):
        return True
    
    def read(self, filecontents, replay):
        replay.messages = list()
        buffer, time = ReplayBuffer(filecontents), 0

        while(buffer.left!=0):
            time += buffer.read_timestamp()
            player_id = buffer.read_byte() & 0x0F
            flags = buffer.read_byte()
            
            if flags & 0xF0 == 0x80:
            
                #ping or something?
                if flags & 0x0F == 3:
                    x = buffer.read_int(LITTLE_ENDIAN)
                    y = buffer.read_int(LITTLE_ENDIAN)

                #some sort of header code
                elif flags & 0x0F == 0:
                    buffer.skip(4)
                    replay.other_people.add(player_id)
            
            elif flags & 0x80 == 0:
                target = flags & 0x03
                length = buffer.read_byte()
                
                if flags & 0x08:
                    length += 64
                    
                if flags & 0x10:
                    length += 128
                    
                text = buffer.read_chars(length)
                replay.messages.append(Message(time, player_id, target, text))

####################################################
class GameEventsBase(Reader):
    file = 'replay.game.events'
    def reads(self, build): return False
    
    def read(self, filecontents, replay):
        replay.events, frames, buffer = list(), 0, ReplayBuffer(filecontents)
        
        PARSERS = {
            0x00: self.get_setup_parser,
            0x01: self.get_action_parser,
            0x02: self.get_unknown2_parser,
            0x03: self.get_camera_parser,
            0x04: self.get_unknown4_parser
        }
        
        while not buffer.empty:
            #Save the start so we can trace for debug purposes
            start = buffer.cursor

            frames += buffer.read_timestamp()
            pid = buffer.shift(5)
            type, code = buffer.shift(3), buffer.read_byte()
            
            parser = PARSERS[type](code)
            if parser:
                event = parser(buffer, frames, type, code, pid)
                buffer.align()
                event.bytes = buffer.read_range(start,buffer.cursor)
                replay.events.append(event)
            else:
                msg = "Unknown event: %s - %s at %s"
                raise TypeError(msg % (hex(type), hex(code), hex(start)))

    def get_setup_parser(self, code):
        if   code in (0x0B,0x0C): return self.parse_join_event
        elif code == 0x05: return self.parse_start_event
        
    def get_action_parser(self, code):
        if   code == 0x09: return self.parse_leave_event
        elif code & 0x0F == 0xB: return self.parse_ability_event
        elif code & 0x0F == 0xC: return self.parse_selection_event
        elif code & 0x0F == 0xD: return self.parse_hotkey_event
        elif code & 0x0F == 0xF: return self.parse_transfer_event
        
    def get_unknown2_parser(self, code):
        if   code == 0x06: return self.parse_0206_event
        elif code == 0x07: return self.parse_0207_event
        elif code == 0x0E: return self.parse_020E_event
    
    def get_camera_parser(self, code):
        if   code == 0x87: return self.parse_camera87_event
        elif code == 0x08: return self.parse_camera08_event
        elif code == 0x18: return self.parse_camera18_event
        elif code & 0x0F == 1: return self.parse_cameraX1_event
        
    def get_unknown4_parser(self, code):
        if   code == 0x16: return self.parse_0416_event
        elif code == 0xC6: return self.parse_04C6_event
        elif code == 0x87: return self.parse_0487_event
        elif code == 0x00: return self.parse_0400_event
        elif code & 0x0F == 2: return self.parse_04X2_event
        
class GameEventsReader(GameEventsBase,Unknown2Parser,Unknown4Parser,ActionParser,SetupParser,CameraParser):
    def reads(self, build):
        return True
