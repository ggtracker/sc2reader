from __future__ import absolute_import

from collections import defaultdict
from itertools import chain

from sc2reader.exceptions import ParseError, ReadError
from sc2reader.objects import *
from sc2reader.events import *
from sc2reader.utils import AttributeDict, BIG_ENDIAN, LITTLE_ENDIAN

class Reader(object):
    def __init__(self, **options):
        self.options = options

    def __call__(self, data, replay):
        raise NotImplementedError

class InitDataReader_Base(Reader):
    def __call__(self, data, replay):
        # The first block of the replay.initData file represents a list of
        # human player names; computers are no recorded. This list appears to
        # always be 16 long, with "" names filling in the balance. Each name
        # is followed by a 5 byte string that appears to be always all zeros.
        player_names = list()
        for player in range(data.read_byte()):
            name = data.read_string()
            data.skip(5)
            if name:
                player_names.append(name)

        # The next block contains information about the structure of the MPQ
        # archive. We don't read this information because we've got mpyq for
        # that. Its split into 3 sections because of the variable length segment
        # in the middle that prevents bulk skipping. The last section also
        # appears to be variable length, hack it to do a find for the section
        # we are looking for.
        data.skip(24)
        sc_account_id = data.read_string()
        distance = data.read_range(data.tell(), data.length).find('s2ma')
        data.skip(distance)

        # The final block of this file that we concern ourselves with is a list
        # of what appears to be map data with the s2ma header on each element.
        # Each element consists of two unknown bytes, a realm id (e.g EU or US)
        # and a map hash which probably ties back to the sc2map files.
        #
        # Some replays don't seem to have a maps section at all, now we can't
        # know what gateway its from? Very strange...
        #
        # TODO: Figure out how we could be missing a maps section.
        map_data = list()
        while data.read(4) == 's2ma':
            gateway = data.read(4).strip('\00 ').lower()
            # There must be a better way to get this little endian
            map_hash = data.read(32).encode('hex')
            map_data.append(MapData(gateway,map_hash))

        # Return the extracted information inside an AttributeDict.
        return AttributeDict(
            map_data=map_data,
            player_names=player_names,
            sc_account_id=sc_account_id,
        )


class AttributesEventsReader_Base(Reader):
    header_length = 4

    def __call__(self, data, replay):
        # The replay.attribute.events file is comprised of a small header and
        # single long list of attributes with the 0x00 00 03 E7 header on each
        # element. Each element holds a four byte attribute id code, a one byte
        # player id, and a four byte value code. Unlike the other files, this
        # file is stored in little endian format.
        #
        # See: ``objects.Attribute`` for attribute id and value lookup logic
        #
        attribute_events = list()
        data.skip(self.header_length)
        for attribute in range(data.read_int(LITTLE_ENDIAN)):
            info = [
                    data.read_int(LITTLE_ENDIAN),
                    data.read_int(LITTLE_ENDIAN),
                    data.read_byte(),
                    data.read(4).strip('\00 ')[::-1]
                ]
            #print hex(info[1]), "P"+str(info[2]), info[3]
            attribute_events.append(Attribute(info))

        return attribute_events


class AttributesEventsReader_17326(AttributesEventsReader_Base):
    # The header length is increased from 4 to 5 bytes from patch 17326 and on.
    header_length = 5


class DetailsReader_Base(Reader):
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','unknown7','unknown8','unknown9','unknown10'])
    def __call__(self, data, replay):
        # The entire details file is just a serialized data structure
        #
        # See: utils.Replaydata.read_data_struct for a format description
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
        #   utc_adjustment
        #   Unknown4
        #   Unknown5
        #   Unknown6
        #   Unknown7
        #   Unknown8
        #   Unknown9
        #   Unknown10
        #
        details = data.read_data_struct()

        # To make things a little more meaningful in the rest of the code we
        # step through all the gathered data and map it into namedtuples so that
        # we don't need to use data[0][0][1][3] to get the battle.net player id.
        # The field names are documented in the namedtuples section of the
        # objects file. The ordered_values function extracts the values while
        # maintaining key order required for proper mapping
        ordered_values = lambda dict: [v for k,v in sorted(dict.iteritems())]

        # Because named tuples are read only, we need to build them in pieces
        # from the bottom up instead of in place from the top down.
        players = list()
        for pdata in details[0]:
            pdata[1] = BnetData(*ordered_values(pdata[1]))
            pdata[3] = ColorData(*ordered_values(pdata[3]))
            player = PlayerData(*ordered_values(pdata))
            players.append(player)
        details[0] = players

        # As a final touch, label all extracted information using the Details
        # named tuple from objects.py
        return self.Details(*ordered_values(details))

class DetailsReader_22612(DetailsReader_Base):
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','unknown7','unknown8','unknown9','unknown10', 'unknown11'])

class MessageEventsReader_Base(Reader):
    def __call__(self, data, replay):
        # The replay.message.events file is a single long list containing three
        # different element types (minimap pings, player messages, and some sort
        # of network packets); each differentiated by flags.
        pings = list()
        messages = list()
        packets = list()

        frame = 0
        #print data.peek(data.length).encode('hex')
        while not data.is_empty:
            # All the element types share the same time, pid, flags header.
            #print data.peek(75)
            #print data.peek(75).encode('hex')
            frame += data.read_timestamp()
            pid = data.read_bits(5)
            t = data.read_bits(3)
            flags = data.read_byte()

            #print "P"+str(pid), hex(flags)
            if flags == 0x83:
                # We need some tests for this
                x = data.read_int(LITTLE_ENDIAN)
                y = data.read_int(LITTLE_ENDIAN)
                pings.append(PingEvent(frame, pid, flags, x, y))

            elif flags == 0x80:
                info = data.read_bytes(4)
                packets.append(PacketEvent(frame, pid, flags, info))

            elif flags & 0x80 == 0:
                target = flags & 0x07
                extension = (flags & 0x18) << 3
                length = data.read_byte()
                #print "Length {}, Extension {}".format(length,extension)
                text = data.read_bytes(length + extension)
                messages.append(ChatEvent(frame, pid, flags, target, text))

        return AttributeDict(pings=pings, messages=messages, packets=packets)


class GameEventsReader_Base(object):
    PLAYER_JOIN_FLAGS = 4
    PLAYER_ABILITY_FLAGS = 17
    ABILITY_TEAM_FLAG = False
    UNIT_INDEX_BITS = 8

    def __call__(self, data, replay):
        EVENT_DISPATCH = {
            0x05: self.game_start_event,
            0x0B: self.player_join_event,
            0x0C: self.player_join_event,
            0x19: self.player_leave_event,
            0x1B: self.player_ability_event,
            0x1C: self.player_selection_event,
            0x1D: self.player_hotkey_event,
            0x1F: self.player_send_resource_event,
            0x31: self.camera_event,
            0x46: self.player_request_resource_event,
        }

        game_events = list()
        fstamp = 0
        debug = replay.opt.debug
        data_length = data.length
        read_timestamp =  data.read_timestamp
        read_bits = data.read_bits
        read_bytes = data.read_bytes
        byte_align = data.byte_align
        append = game_events.append
        event_start = 0

        try:
            while event_start != data_length:
                event = None
                fstamp += read_timestamp()
                pid = read_bits(5)
                event_type = read_bits(7)

                # Check for a lookup
                if event_type in EVENT_DISPATCH:
                    event = EVENT_DISPATCH[event_type](data, fstamp, pid, event_type)

                # Otherwise maybe it is an unknown chunk
                elif event_type == 0x26:
                    read_bytes(8)
                elif event_type == 0x27:
                    read_bytes(4)
                elif event_type == 0x37:
                    read_bytes(8)
                elif event_type == 0x38:
                    arr1 = [read_bits(32) for i in range(read_bits(8))]
                    arr2 = [read_bits(32) for i in range(read_bits(8))]
                elif event_type == 0x3c:
                    read_bytes(2)
                elif event_type == 0x47:
                    read_bytes(4)
                elif event_type == 0x4C:
                    read_bits(4)
                elif event_type == 0x59:
                    read_bytes(4)

                # Otherwise throw a read error
                else:
                    raise ReadError("Event type {} unknown at position {}.".format(hex(event_type),hex(event_start)), event_type, event_start, replay, game_events, data)

                byte_align()

                if event:
                    if debug:
                        event.bytes = data.read_range(event_start, data.tell())
                    append(event)

                event_start = data.tell()

            return game_events
        except ParseError as e:
            raise ReadError("Parse error '{}' unknown at position {}.".format(e.msg, hex(event_start)), event_type, event_start, replay, game_events, data)
        except EOFError as e:
            raise ReadError("EOFError error '{}' unknown at position {}.".format(e.msg, hex(event_start)), event_type, event_start, replay, game_events, data)



class GameEventsReader_16117(GameEventsReader_Base):
    def game_start_event(self, data, fstamp, pid, event_type):
        return GameStartEvent(fstamp, pid, event_type)

    def player_join_event(self, data, fstamp, pid, event_type):
        unknown_flags = data.read_bits(self.PLAYER_JOIN_FLAGS)
        return PlayerJoinEvent(fstamp, pid, event_type, unknown_flags)

    def player_leave_event(self, data, fstamp, pid, event_type):
        return PlayerLeaveEvent(fstamp, pid, event_type)

    def _parse_selection_update(self, data):
        return (1, data.read_bits(data.read_bits(self.UNIT_INDEX_BITS)))

    def player_ability_event(self, data, fstamp, pid, event_type):
        data.read_bits(4)
        data.read_bytes(7)
        switch = data.read_bits(8)
        if switch in (0x30,0x50):
            data.read_bytes(1)
        data.read_bytes(24)
        return AbilityEvent(fstamp, pid, event_type, None)

    def player_selection_event(self, data, fstamp, pid, event_type):
        bank = data.read_bits(4)
        subgroup = data.read_bits(self.UNIT_INDEX_BITS) #??
        overlay = self._parse_selection_update(data)

        type_count = data.read_bits(self.UNIT_INDEX_BITS)
        unit_types = [(data.read_short(BIG_ENDIAN) << 8 | data.read_byte(),data.read_bits(self.UNIT_INDEX_BITS)) for index in range(type_count)]

        unit_count = data.read_bits(self.UNIT_INDEX_BITS)
        unit_ids = [data.read_bits(32) for index in range(unit_count)]

        unit_types = chain(*[[utype]*count for (utype, count) in unit_types])
        units = list(zip(unit_ids, unit_types))
        return SelectionEvent(fstamp, pid, event_type, bank, units, overlay)

    def player_hotkey_event(self, data, fstamp, pid, event_type):
        hotkey = data.read_bits(4)
        action = data.read_bits(2)
        overlay = self._parse_selection_update(data)

        if action == 0:
            return SetToHotkeyEvent(fstamp, pid, event_type, hotkey, overlay)
        elif action == 1:
            return AddToHotkeyEvent(fstamp, pid, event_type, hotkey, overlay)
        elif action == 2:
            return GetFromHotkeyEvent(fstamp, pid, event_type, hotkey, overlay)
        else:
            raise ParseError("Hotkey Action '{}' unknown".format(hotkey))

    def player_send_resource_event(self, data, fstamp, pid, event_type):
        target = data.read_bits(4)
        unknown = data.read_bits(4) #??
        minerals = data.read_bits(32)
        vespene = data.read_bits(32)
        terrazine = data.read_bits(32) #??
        custom = data.read_bits(32) #??
        return SendResourceEvent(fstamp, pid, event_type, target, minerals, vespene, terrazine, custom)

    def player_request_resource_event(self, data, fstamp, pid, event_type):
        flags = data.read_bits(3) #??
        custom = minerals = vespene = terrazine = 0
        if data.read_bits(1):
            custom = data.read_bits(31) #??
        if data.read_bits(1):
            minerals = data.read_bits(31)
        if data.read_bits(1):
            vespene = data.read_bits(31)
        if data.read_bits(1):
            terrazine = data.read_bits(31) #??
        return RequestResourceEvent(fstamp, pid, event_type, minerals, vespene, terrazine, custom)

    def camera_event(self, data, fstamp, pid, event_type):
        # From https://github.com/Mischanix/sc2replay-csharp/wiki/replay.game.events
        x = data.read_bits(16)/256.0
        y = data.read_bits(16)/256.0
        distance = pitch = yaw = height = 0
        if data.read_bits(1):
            distance = data.read_bits(16)/256.0
        if data.read_bits(1):
            #Note: this angle is relative to the horizontal plane, but the editor shows the angle relative to the vertical plane. Subtract from 90 degrees to convert.
            pitch = data.read_bits(16) #?
            pitch = 45 * (((((pitch * 0x10 - 0x2000) << 17) - 1) >> 17) + 1) / 4096.0
        if data.read_bits(1):
            #Note: this angle is the vector from the camera head to the camera target projected on to the x-y plane in positive coordinates. So, default is 90 degrees, while insert and delete produce 45 and 135 degrees by default.
            yaw = data.read_bits(16) #?
            yaw = 45 * (((((yaw * 0x10 - 0x2000) << 17) - 1) >> 17) + 1) / 4096.0
        if data.read_bits(1):
            height_offset = data.read_bits(16)/256.0
        return CameraEvent(fstamp, pid, event_type, x, y, distance, pitch, yaw, height)


class GameEventsReader_16561(GameEventsReader_16117):
    # Don't want to do this more than once
    SINGLE_BIT_MASKS = [0x1 << i for i in range(500)]

    def _parse_selection_update(self, data):
        update_type = data.read_bits(2)
        if update_type == 1:
            mask_length = data.read_bits(self.UNIT_INDEX_BITS)

            # Mask is written in byte chunks
            mask = data.read_bytes(mask_length/8)
            if mask_length%8:
                mask += chr(data.read_bits(mask_length%8))

            # And must be reversed to put the bits in order
            bit_mask = sum([ord(c)<<(i*8) for i,c in enumerate(mask)])

            # Represent the mask as a simple bit array with
            # True => Deselect, False => Keep
            mask = [bit_mask & bit for bit in self.SINGLE_BIT_MASKS[:mask_length]]

        elif update_type == 2:
            index_count = data.read_bits(self.UNIT_INDEX_BITS)
            mask = [data.read_bits(self.UNIT_INDEX_BITS) for index in range(index_count)]
        elif update_type == 3:
            index_count = data.read_bits(self.UNIT_INDEX_BITS)
            mask = [data.read_bits(self.UNIT_INDEX_BITS) for index in range(index_count)]
        else:
            mask = None

        return (update_type, mask)

    def player_ability_event(self, data, fstamp, pid, event_type):
        # TODO: Use the flag information
        # See sc2replay-csharp wiki for details
        flags = data.read_bits(self.PLAYER_ABILITY_FLAGS)

        default_ability = not data.read_bits(1)
        if not default_ability:
            ability = data.read_bits(16) << 5 | data.read_bits(5)
            default_actor = not data.read_bits(1)
        else:
            ability = 0

        target_type = data.read_bits(2)
        if target_type == 1:
            x = data.read_bits(20)/4096.0
            y = data.read_bits(20)/4096.0
            z = data.read_bits(32)
            z = (z>>1)/8192.0 * pow(-1, z & 0x1)
            unknown = data.read_bits(1)
            return LocationAbilityEvent(fstamp, pid, event_type, ability, (x, y, z))

        elif target_type == 2:
            player = team = None

            data.read_bits(8)
            data.read_bits(8)
            unit = (data.read_bits(32), data.read_bits(16))

            if self.ABILITY_TEAM_FLAG and data.read_bits(1):
                team = data.read_bits(4)

            if data.read_bits(1):
                player = data.read_bits(4)

            x = data.read_bits(20)/4096.0
            y = data.read_bits(20)/4096.0
            z = data.read_bits(32)
            z = (z>>1)/8192.0 * pow(-1, z & 0x1)
            unknown = data.read_bits(1)
            return TargetAbilityEvent(fstamp, pid, event_type, ability, unit, player, team, (x, y, z))

        elif target_type == 3:
            unit_id = data.read_bits(32)
            unknown = data.read_bits(1)
            return SelfAbilityEvent(fstamp, pid, event_type, ability, unit_id)

        else:
            return AbilityEvent(fstamp, pid, event_type, ability)


class GameEventsReader_18574(GameEventsReader_16561):
    PLAYER_ABILITY_FLAGS = 18

class GameEventsReader_19595(GameEventsReader_18574):
    ABILITY_TEAM_FLAG = True

class GameEventsReader_22612(GameEventsReader_19595):
    PLAYER_JOIN_FLAGS = 5 # or 6
    PLAYER_ABILITY_FLAGS = 20
    UNIT_INDEX_BITS = 9 # Now can select up to 512 units
