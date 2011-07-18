from datetime import datetime

from .parsers import *
from .objects import *
from .utils import LITTLE_ENDIAN, BIG_ENDIAN
from .utils import AttributeDict


class InitDataReader(object):
    def __call__(self,buffer, replay):
        init_data = AttributeDict()

        # The first block of the replay.initData file represents a list of
        # human player names; computers are no recorded. This list appears to
        # always be 16 long, with "" names filling in the balance. Each name
        # is followed by a 5 byte string that appears to be always all zeros.
        player_names = list()
        for player in range(buffer.read_byte()):
            name = buffer.read_string()
            buffer.skip(5)
            if name:
                player_names.append(name)

        # The next block contains information about the structure of the MPQ
        # archive. We don't read this information because we've got mpyq for
        # that. Its split into 3 sections because of the variable length segment
        # in the middle that prevents bulk skipping.
        buffer.skip(24)
        init_data.sc_account_id = buffer.read_string()
        buffer.skip(684)

        # The final block of this file that we concern ourselves with is a list
        # of what appears to be map data with the s2ma header on each element.
        # Each element consists of two unknown bytes, a realm id (e.g EU or US)
        # and a map hash which probably ties back to the sc2map files.
        map_data = list()
        while( buffer.read_chars(4).lower() == 's2ma' ):
            unknown = buffer.read_chars(2)
            realm = buffer.read_string(2).lower()
            map_hash = buffer.read_chars(32)
            map_data.append(MapData(unknown,realm,map_hash))

        # We insert the data into the init_data entry in our replay.raw dict
        # for later use during processing. Realm is promoted for convenience
        # since it is guarenteed to be consistent across all the entries.
        init_data.map_data = map_data
        init_data.player_names = player_names
        init_data.realm = init_data.map_data[0].realm
        replay.raw.init_data = init_data


class AttributeEventsReader(object):
    header_length = 4

    def __call__(self, buffer, replay):
        attribute_events = list()

        # The replay.attribute.events file is comprised of a small header and
        # single long list of attributes with the 0x00 00 03 E7 header on each
        # element. Each element holds a four byte attribute id code, a one byte
        # player id, and a four byte value code. Unlike the other files, this
        # file is stored in little endian format.
        #
        # See: ``objects.Attribute`` for attribute id and value lookup logic
        #
        buffer.skip(self.header_length)
        for i in range(buffer.read_int(LITTLE_ENDIAN)):
            attribute_events.append(Attribute([
                    buffer.read_int(LITTLE_ENDIAN),
                    buffer.read_int(LITTLE_ENDIAN),
                    buffer.read_byte(),
                    buffer.read_chars(4)
                ]))

        replay.raw.attribute_events = attribute_events


class AttributeEventsReader_17326(AttributeEventsReader):
    # The header length is increased from 4 to 5 bytes from patch 17326 and on.
    header_length = 5


class DetailsReader(object):
    def __call__(self, buffer, replay):
        # The entire details file is just a serialized data structure
        #
        # See: utils.ReplayBuffer.read_data_struct for a format description
        #
        # The general file structure is as follows:
        #   TODO: add the data types for each node in the structure
        #
        #   List of Players:
        #       Name
        #       BnetData:
        #           unknown1
        #           subregion_id
        #           unknown2
        #           bnet_id
        #       actual_race (Terran, Protoss, Zerg)
        #       ColorData:
        #           alpha (0-255)
        #           red (0-255)
        #           green (0-255)
        #           blue (0-255)
        #       Unknown1
        #       Unknown2
        #       handicap (0-100)
        #       Unknown3
        #       Result (0,1,2) - Frequently 2, indicating unknown. 1 for win.
        #   Map
        #   Unknown1
        #   Unknown2
        #   Unknown3
        #   file_time - Time file was created/replay was made
        #   Unknown4
        #   Unknown5
        #   Unknown6
        #   Unknown7
        #   Unknown8
        #   Unknown9
        #   Unknown10
        #   Unknown11
        #
        data = buffer.read_data_struct()

        # To make things a little more meaningful in the rest of the code we
        # step through all the gathered data and map it into namedtuples so that
        # we don't need to use data[0][0][1][3] to get the battle.net player id.
        # The field names are documented in the namedtuples section of the
        # objects file. The ordered_values function extracts the values while
        # maintaining key order required for propper mapping
        ordered_values = lambda dict: [v for k,v in sorted(dict.iteritems())]

        # Because named tuples are read only, we need to build them in pieces
        # from the bottom up instead of in place from the top down.
        players = list()
        for pid, pdata in enumerate(data[0]):
            pdata[1] = BnetData(*ordered_values(pdata[1]))
            pdata[3] = ColorData(*ordered_values(pdata[3]))
            player = PlayerData(*ordered_values(pdata))
            players.append(player)
        data[0] = players
        replay.raw.details = Details(*ordered_values(data))


class MessageEventsReader(object):
    def __call__(self, buffer, replay):
        # The replay.message.events file is a single long list containing three
        # different element types (minimap pings, player messages, and some sort
        # of network packets); each differentiated by flags.
        message_events = AttributeDict()
        message_events.pings = list()
        message_events.messages = list()
        message_events.packets = list()

        time = 0
        while(buffer.left):
            # All the element types share the same time, pid, flags header.
            time += buffer.read_timestamp()
            pid = buffer.read_byte() & 0x0F
            flags = buffer.read_byte()

            # The 0x83 flag indicates a minimap ping and contains the x and
            # y coordinates of that ping as the payload.
            if flags == 0x83:
                x = buffer.read_int(LITTLE_ENDIAN)
                y = buffer.read_int(LITTLE_ENDIAN)
                message_events.pings.append(PingData(time,pid,flags,x,y))

            # The 0x80 flag marks a network packet. I believe these mark packets
            # send over the network to establish latency or connectivity.
            elif flags == 0x80:
                packet = PacketData(time,pid,flags,buffer.read_chars(4))
                message_events.packets.append(packet)

            # A flag set without the 0x80 bit set is a player message. Messages
            # store a target (allies or all) as well as the message text.
            elif flags & 0x80 == 0:
                target,extension = flags & 0x03, (flags & 0x18) << 3
                text = buffer.read_chars(buffer.read_byte() + extension)
                message = MessageData(time, pid, flags, target, text)
                replay.messages.append(message)

        replay.raw.message_events = message_events

####################################################

class GameEventsBase(object):

    def __call__(self, buffer, replay):
        PARSERS = {
            0x00: self.get_setup_parser,
            0x01: self.get_action_parser,
            0x02: self.get_unknown2_parser,
            0x03: self.get_camera_parser,
            0x04: self.get_unknown4_parser
        }

        game_events, frames = list(), 0

        while not buffer.empty:
            #Save the start so we can trace for debug purposes
            start = buffer.cursor

            frames += buffer.read_timestamp()
            pid,type,code = buffer.shift(5), buffer.shift(3), buffer.read_byte()
            #print "Type %X - Code %X - Start %X" % (type,code,start)

            parser = PARSERS.get(type,lambda x:None)(code)

            if parser == None:
                msg = "Unknown event: %X - %X at %X"
                raise TypeError(msg % (type, code, start))

            event = parser(buffer, frames, type, code, pid)

            buffer.align()
            event.bytes = buffer.read_range(start,buffer.cursor)
            game_events.append(event)

        replay.raw.game_events = game_events

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
