from datetime import datetime

from sc2reader.parsers import *
from sc2reader.objects import *
from sc2reader.utils import LITTLE_ENDIAN, BIG_ENDIAN
from sc2reader.utils import timestamp_from_windows_time, AttributeDict

#################################################

class InitDataReader(object):
    def read(self, buffer, replay):
        
        # Game clients
        for p in range(buffer.read_byte()):
            name = buffer.read_string()
            if len(name) > 0:
                replay.player_names.append(name)
            buffer.skip(5) #Always all zeros UNKNOWN
        
        # UNKNOWN
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

class AttributeEventsReader(object):
    def read(self, buffer, replay):
        self.load_header(replay, buffer)
        
        replay.attributes = list()
        for i in range(0, buffer.read_int(LITTLE_ENDIAN)):
            replay.attributes.append(Attribute([
                    buffer.read_int(LITTLE_ENDIAN),     #Header
                    buffer.read_int(LITTLE_ENDIAN),     #Attr Id
                    buffer.read_byte(),                 #Player
                    buffer.read_chars(4)                #Value
                ]))
            
    def load_header(self, replay, buffer):
        buffer.skip(4)

class AttributeEventsReader_17326(AttributeEventsReader):
    def load_header(self, replay, buffer):
        buffer.skip(5)
        
##################################################

class DetailsReader(object):
    color_fields = ('a','r','g','b',)
    player_fields = ('name','bnet','race','color','?','?','handicap','?','result')

    def read(self, buffer, replay):
        data = buffer.read_data_struct()

        for pid, pdata in enumerate(data[0]):
            values = [v for k,v in sorted(pdata.iteritems())]
            pdata = AttributeDict(zip(self.player_fields, values))

            #Handle the basic player attributes
            player = Player(pid+1, pdata.name, replay)
            player.uid = pdata.bnet[4]
            player.subregion = pdata.bnet[2]
            player.handicap = pdata.handicap
            player.realm = replay.realm
            player.result = pdata.result
            # TODO?: get a map of realm,subregion => region in here

            # Now convert all different localizations to western if we can
            # TODO: recognize current locale and use that instead of western
            # TODO: fill in the LOCALIZED_RACES table
            player.actual_race = LOCALIZED_RACES.get(pdata.race, pdata.race)

            ''' Conversion to the new color object:
                    color_rgba is the color object itself
                    color_hex is color.hex
                    color is str(color)'''
            values = [v for k,v in sorted(pdata.color.iteritems())]
            player.color = Color(zip(self.color_fields, values))

            # Add player to replay
            replay.players.append(player)

        #Non-player details
        replay.map = data[1]
        replay.file_time = data[5]
        unix_timestamp = timestamp_from_windows_time(replay.file_time)
        replay.date = datetime.fromtimestamp(unix_timestamp)
        replay.utc_date = datetime.utcfromtimestamp(unix_timestamp)

##################################################

class MessageEventsReader(object):
    def read(self, buffer, replay):
        replay.messages, time = list(), 0

        while(buffer.left != 0):
            time += buffer.read_timestamp()
            player_id = buffer.read_byte() & 0x0F
            flags = buffer.read_byte()
            
            if flags & 0xF0 == 0x80:
                # Pings, TODO: save and use data somewhere
                if flags & 0x0F == 3:
                    x = buffer.read_int(LITTLE_ENDIAN)
                    y = buffer.read_int(LITTLE_ENDIAN)
                # Some sort of header code
                elif flags & 0x0F == 0:
                    buffer.skip(4) # UNKNOWN
                    # XXX why?
                    replay.other_people.add(player_id)
            
            elif flags & 0x80 == 0:
                target = flags & 0x03
                length = buffer.read_byte()
                
                # Flags for additional length in message
                if flags & 0x08:
                    length += 64
                if flags & 0x10:
                    length += 128
                    
                text = buffer.read_chars(length)
                replay.messages.append(Message(time, player_id, target, text))

####################################################

class GameEventsBase(object):
    def read(self, buffer, replay):
        replay.events, frames = list(), 0
        
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
            #print "Type %X - Code %X - Start %X" % (type,code,start)

            parser = PARSERS.get(type,lambda x:None)(code)

            if parser == None:
                msg = "Unknown event: %X - %X at %X"
                raise TypeError(msg % (type, code, start))
            
            event = parser(buffer, frames, type, code, pid)

            buffer.align()
            event.bytes = buffer.read_range(start,buffer.cursor)
            replay.events.append(event)


    def get_setup_parser(self, code):
        if   code in (0x0B,0x0C,0x2C): return self.parse_join_event
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
        elif code == 0x88: return self.parse_0488_event
        elif code == 0x00: return self.parse_0400_event
        elif code & 0x0F == 0x02: return self.parse_04X2_event
        elif code & 0x0F == 0x0C: return self.parse_04XC_event
        
class GameEventsReader(GameEventsBase,Unknown2Parser,Unknown4Parser,ActionParser,SetupParser,CameraParser):
    pass

class GameEventsReader_16561(GameEventsBase,Unknown2Parser,Unknown4Parser,ActionParser_16561,SetupParser,CameraParser):
    pass

class GameEventsReader_18574(GameEventsBase,Unknown2Parser,Unknown4Parser,ActionParser_18574,SetupParser,CameraParser):
    pass
