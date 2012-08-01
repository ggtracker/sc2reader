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

    def __call__(self, buffer, replay):
        raise NotImplementedError

class InitDataReader_Base(Reader):
    def __call__(self,buffer, replay):
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
        # in the middle that prevents bulk skipping. The last section also
        # appears to be variable length, hack it to do a find for the section
        # we are looking for.
        buffer.skip(24)
        sc_account_id = buffer.read_string()
        distance = buffer.read_range(buffer.cursor, buffer.length).find('s2ma')
        buffer.skip(distance)

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
        while buffer.read_chars(4).lower() == 's2ma':
            unknown = buffer.read_chars(2)
            gateway = buffer.read_string(2).lower()
            # There must be a better way to get this little endian
            map_hash = buffer.read_chars(32)
            map_data.append(MapData(unknown,gateway,map_hash))

        # Return the extracted information inside an AttributeDict.
        return AttributeDict(
            map_data=map_data,
            player_names=player_names,
            sc_account_id=sc_account_id,
        )


class AttributesEventsReader_Base(Reader):
    header_length = 4

    def __call__(self, buffer, replay):
        # The replay.attribute.events file is comprised of a small header and
        # single long list of attributes with the 0x00 00 03 E7 header on each
        # element. Each element holds a four byte attribute id code, a one byte
        # player id, and a four byte value code. Unlike the other files, this
        # file is stored in little endian format.
        #
        # See: ``objects.Attribute`` for attribute id and value lookup logic
        #
        attribute_events = list()
        buffer.skip(self.header_length)
        for attribute in range(buffer.read_int(LITTLE_ENDIAN)):
            attribute_events.append(Attribute([
                    buffer.read_int(LITTLE_ENDIAN),
                    buffer.read_int(LITTLE_ENDIAN),
                    buffer.read_byte(),
                    buffer.read_chars(4)
                ]))

        return attribute_events


class AttributesEventsReader_17326(AttributesEventsReader_Base):
    # The header length is increased from 4 to 5 bytes from patch 17326 and on.
    header_length = 5


class DetailsReader_Base(Reader):
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','unknown7','unknown8','unknown9','unknown10'])
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
        #   utc_adjustment
        #   Unknown4
        #   Unknown5
        #   Unknown6
        #   Unknown7
        #   Unknown8
        #   Unknown9
        #   Unknown10
        #
        data = buffer.read_data_struct()

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
        for pdata in data[0]:
            pdata[1] = BnetData(*ordered_values(pdata[1]))
            pdata[3] = ColorData(*ordered_values(pdata[3]))
            player = PlayerData(*ordered_values(pdata))
            players.append(player)
        data[0] = players

        # As a final touch, label all extracted information using the Details
        # named tuple from objects.py
        return self.Details(*ordered_values(data))

class DetailsReader_22612(DetailsReader_Base):
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','unknown7','unknown8','unknown9','unknown10', 'unknown11'])

class MessageEventsReader_Base(Reader):
    def __call__(self, buffer, replay):
        # The replay.message.events file is a single long list containing three
        # different element types (minimap pings, player messages, and some sort
        # of network packets); each differentiated by flags.
        pings = list()
        messages = list()
        packets = list()

        frame = 0
        while(buffer.left):
            # All the element types share the same time, pid, flags header.
            frame += buffer.read_timestamp()
            pid = buffer.read_byte() & 0x0F
            flags = buffer.read_byte()

            if flags == 0x83:
                pings.append(PingEvent(frame, pid, flags, buffer))
            elif flags == 0x80:
                packets.append(PacketEvent(frame, pid, flags, buffer))
            elif flags & 0x80 == 0:
                messages.append(ChatEvent(frame, pid, flags, buffer))

        return AttributeDict(pings=pings, messages=messages, packets=packets)


class GameEventsReader_Base(Reader):

    def __call__(self, buffer, replay):
        # The game events file is a single long list of game events identified
        # by both a type and a code. For convenience, we dispatch the handling
        # of each unique event type to a separate function to handle the code
        # specific dispatching.
        PARSERS = {
            0x00: self.get_setup_parser,
            0x01: self.get_action_parser,
            0x02: self.get_unknown2_parser,
            0x03: self.get_camera_parser,
            0x04: self.get_unknown4_parser
        }

        game_events, frames = list(), 0

        # Locals are faster!
        tell = buffer.io.tell
        read_timestamp = buffer.read_timestamp
        shift = buffer.shift
        read_byte = buffer.read_byte
        debug = replay.opt.debug
        append = game_events.append
        align = buffer.align

        while buffer.left:
            #Save the start so we can trace for debug purposes
            start = tell()

            # Each event has the same header which consists of 1-3 bytes for a
            # count of the number of frames since the last recorded event, a
            # byte split 5-3 bitwise for the player id (0-16) and the event
            # type (0-4). A final header byte representing the code uniquely
            # identifies the class of event we are handling.
            frames += read_timestamp()
            pid = shift(5)
            type = shift(3)
            code = read_byte()


            try:
                # Use the PARSERS dispatch dict to delegate handling of the
                # particular event code to the corresponding event type handler.
                # The is handler should return the appropriate event parser
                # which should then return the raw event data for storage.
                parser = PARSERS[type](code)
                event = parser(buffer, frames, type, code, pid)

                # Because events are parsed in a bitwise fashion, they sometimes
                # leave the buffer in a bitshifted state. Each new event always
                # starts byte aligned so make sure that the buffer does too.
                align()

                # For debugging purposes, we may wish to record the event.bytes
                # associated with this event; including the event header bytes.
                if debug:
                    event.bytes = buffer.read_range(start, buffer.cursor)

                append(event)

            except KeyError:
                # If the type is not a key in the PARSERS lookup table we
                # probably incorrectly parsed the previous event
                # TODO: Raise an error instead an store the previous event
                raise ReadError("Unknown event type", type, code, start, replay, game_events, buffer)

            except ParseError:
                # For some reason, the type handler that we delegated to didn't
                # recognize the event code that we extracted.
                # TODO: Do something meaningful here
                raise ReadError("Unknown event code", type, code, start, replay, game_events, buffer)

            except ReadError as e:
                raise ReadError(e.msg, replay, game_events, buffer, start)

        return game_events

    def get_setup_parser(self, code):
        # The setup events typically form a header of sorts to the file with
        # each player (in no particular order) registering a join event and
        # the game starting immediately afterwords. On occasion, for unknown
        # reasons, other events (particularly camera events) will register
        # before the game has actually started. Weird.
        if   code in (0x0B, 0x0C, 0x2C): return self.parse_join_event
        elif code in (0x05,): return self.parse_start_event
        else:
            raise ParseError("Unknown Setup Parser Code {0}".format(code))

    def get_action_parser(self, code):
        # The action events are always associated with a particular player and
        # generally encompass all possible player game actions.
        if   code == 0x09: return self.parse_leave_event
        elif code & 0x0F == 0xB: return self.parse_ability_event
        elif code & 0x0F == 0xC: return self.parse_selection_event
        elif code & 0x0F == 0xD: return self.parse_hotkey_event
        elif code & 0x0F == 0xF: return self.parse_transfer_event
        elif code & 0x0F == 0x6: return self.parse_game_save_event
        else:
            raise ParseError("Unknown Action Parser Code {0}".format(code))

    def get_unknown2_parser(self, code):
        # While its unclear what these events represent, they are MUCH more
        # frequent in custom maps; possibly indicating that they are related
        # to scripted actions as opposed to player actions.
        if   code == 0x06: return self.parse_0206_event
        elif code == 0x07: return self.parse_0207_event
        elif code == 0x0E: return self.parse_020E_event
        else:
            raise ParseError("Unknown Unknown2 Parser Code {0}".format(code))

    def get_camera_parser(self, code):
        # Each player's camera control events are recorded, separately from the
        # rest of the player actions since the camera viewport location/angle
        # has no meaningful impact on the course of the game. These events will
        # infrequently occur before the game starts for some unknown reason.
        if   code == 0x87: return self.parse_camera87_event
        elif code & 0x0F == 8: return self.parse_cameraX8_event
        elif code & 0x0F == 1: return self.parse_cameraX1_event
        elif code == 0x0a: return self.parse_camera0A_event
        else:
            raise ParseError("Unknown Camera Parser Code {0}".format(code))

    def get_unknown4_parser(self, code):
        # I don't know anything about these events. Any parse information for
        # these events was arrived at by guess and check with little to no idea
        # as to why it works or what the bytes represent. This was primarily an
        # effort of pattern matching over hundreds of replays.
        if   code == 0x16: return self.parse_0416_event
        elif code == 0xC6: return self.parse_04C6_event
        elif code == 0x87: return self.parse_0487_event
        elif code == 0x88: return self.parse_0488_event
        elif code == 0x00: return self.parse_0400_event
        elif code & 0x0F == 0x02: return self.parse_04X2_event
        elif code & 0x0F == 0x0C: return self.parse_04XC_event
        else:
            raise ParseError("Unknown Unknown4 Parser Code {0}".format(code))

    def parse_join_event(self, buffer, frames, type, code, pid):
        return PlayerJoinEvent(frames, pid, type, code)

    def parse_start_event(self, buffer, frames, type, code, pid):
        return GameStartEvent(frames, pid, type, code)

    def parse_leave_event(self, buffer, frames, type, code, pid):
        return PlayerLeaveEvent(frames, pid, type, code)

    def parse_game_save_event(self, buffer, frames, type, code, pid):
        raise ParseError("Unparsable game save event found.");

    def parse_ability_event(self, buffer, frames, type, code, pid):
        buffer.skip(7)
        switch = buffer.read_byte()
        if switch in (0x30,0x50):
            buffer.read_byte()
        buffer.skip(24)
        return AbilityEvent(frames, pid, type, code, None)

    def parse_selection_event(self, buffer, frames, type, code, pid):
        bank = code >> 4
        selFlags = buffer.read_byte()
        dsuCount = buffer.read_byte()
        buffer.read(bits=dsuCount)

        # <count> (<type_id>, <count>,)*
        object_types = [ (buffer.read_object_type(read_modifier=True), buffer.read_byte(), ) for i in range(buffer.read_byte()) ]
        # <count> (<object_id>,)*
        object_ids = [ buffer.read_object_id() for i in range(buffer.read_byte()) ]

        # repeat types count times
        object_types = chain(*[[object_type,]*count for (object_type, count) in object_types])
        objects = zip(object_ids, object_types)

        return SelectionEvent(frames, pid, type, code, bank, objects, None)

    def parse_hotkey_event(self, buffer, frames, type, code, pid):
        hotkey = code >> 4
        action, read = buffer.shift(2), buffer.shift(1)

        if read:
            mask = buffer.read(bits=buffer.read_byte())
            overlay = lambda a: Selection.mask(a, mask)
        else:
            overlay = None

        if action == 0:
            return SetToHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        elif action == 1:
            return AddToHotkeyEvent(frames, pid, type, code, hotkey, overlay)
        elif action == 2:
            return GetFromHotkeyEvent(frames, pid, type, code, hotkey, overlay)

    def parse_transfer_event(self, buffer, frames, type, code, pid):
        def read_resource(buffer):
            block = buffer.read_int(BIG_ENDIAN)
            base, multiplier, extension = block >> 8, block & 0xF0, block & 0x0F
            return base*multiplier+extension

        target = code >> 4
        buffer.skip(1) #Always 84
        minerals,vespene = read_resource(buffer), read_resource(buffer)
        buffer.skip(8)

        return ResourceTransferEvent(frames, pid, type, code, target, minerals, vespene)

    def parse_camera87_event(self, buffer, frames, type, code, pid):
        #There are up to 3 pieces to read depending on values encountered
        for i in range(3):
            if buffer.read_int(BIG_ENDIAN) & 0xF0 == 0:
                break

        return CameraMovementEvent(frames, pid, type, code)

    def parse_cameraX8_event(self, buffer, frames, type, code, pid):
        # No idea why these two cases are ever so slightly different. There
        # must be a pattern in here somewhere that I haven't found yet.
        #
        # TODO: Find out why we occasionally shift by 2 instead of 3
        if code == 0x88:
            flags = buffer.read_byte()
            extra = buffer.read_byte()
            buffer.skip( (code & 0xF0 | flags & 0x0F) << 2 )

        else:
            flags = buffer.read_byte()
            extra = buffer.read_byte()
            buffer.skip( (code & 0xF0 | flags & 0x0F) << 3 )

        return CameraMovementEvent(frames, pid, type, code)

    def parse_cameraX1_event(self, buffer, frames, type, code, pid):
        # TODO: Figure out what all this zoom and rotate stuff is about
        x = ((code & 0xF0) << 8 | sum(buffer.read(bits=12)))/256.0
        y = buffer.read_short()/256.0

        flags = buffer.shift(4) << 4
        if flags & 0x10 != 0:
            # zoom=?
            flags = buffer.read_short(BIG_ENDIAN)
        if flags & 0x20 != 0:
            # zoom=?
            flags = buffer.read_short(BIG_ENDIAN)
        if flags & 0x40 != 0:
            # rotate=?
            buffer.skip(2)

        return CameraMovementEvent(frames, pid, type, code)

    def parse_camera0A_event(self, buffer, frames, type, code, pid):
        # Not really sure wtf is up with this event
        # I've only seen it a dozen times. Always (?) a custom game
        for i in range(6):
            if not buffer.read_int(BIG_ENDIAN) & 0xF0:
                break

        return CameraMovementEvent(frames, pid, type, code)

    def parse_0206_event(self, buffer, frames, type, code, pid):
        buffer.skip(8)
        return UnknownEvent(frames, pid, type, code)

    def parse_0207_event(self, buffer, frames, type, code, pid):
        buffer.skip(4)
        return UnknownEvent(frames, pid, type, code)

    def parse_020E_event(self, buffer, frames, type, code, pid):
        buffer.skip(4)
        return UnknownEvent(frames, pid, type, code)

    def parse_0416_event(self, buffer, frames, type, code, pid):
        buffer.skip(24)
        return UnknownEvent(frames, pid, type, code)

    def parse_04C6_event(self, buffer, frames, type, code, pid):
        buffer.skip(16)
        return UnknownEvent(frames, pid, type, code)

    def parse_0487_event(self, buffer, frames, type, code, pid):
        buffer.skip(4) #Always 00 00 00 01 ??
        return UnknownEvent(frames, pid, type, code)

    def parse_0400_event(self, buffer, frames, type, code, pid):
        buffer.skip(10)
        return UnknownEvent(frames, pid, type, code)

    def parse_04X2_event(self, buffer, frames, type, code, pid):
        buffer.skip(2)
        return UnknownEvent(frames, pid, type, code)

    def parse_0488_event(self, buffer, frames, type, code, pid):
        buffer.skip(4) #Always 00 00 00 01 ?? or 00 00 00 03
        return UnknownEvent(frames, pid, type, code)

    def parse_04XC_event(self, buffer, frames, type, code, pid):
        #no body
        return UnknownEvent(frames, pid, type, code)




class GameEventsReader_16561(GameEventsReader_Base):
    def parse_overlay(self, buffer, mode):
        if mode == 0x01: # deselect overlay mask
            data = buffer.read_bitmask()
        elif mode == 0x02: # deselect mask
            data = [buffer.read_byte() for i in range(buffer.read_byte())]
        elif mode == 0x03: # replace mask
            data = [buffer.read_byte() for i in range(buffer.read_byte())]
        else:
            data=None

        return mode, data

    def parse_selection_event(self, buffer, frames, type, code, pid):

        bank = code >> 4
        first = buffer.read_byte() # TODO ?

        deselect = self.parse_overlay(buffer, buffer.shift(2))

        # <count> (<type_id>, <count>,)*
        object_types = [ (buffer.read_object_type(read_modifier=True), buffer.read_byte(), ) for i in range(buffer.read_byte()) ]
        # <count> (<object_id>,)*
        object_ids = [ buffer.read_object_id() for i in range(buffer.read_byte()) ]

        # repeat types count times
        object_types = chain(*[[object_type,]*count for (object_type, count) in object_types])
        objects = zip(object_ids, object_types)

        return SelectionEvent(frames, pid, type, code, bank, objects, deselect)

    def parse_hotkey_event(self, buffer, frames, type, code, pid):
        hotkey = code >> 4
        action = buffer.shift(2)

        deselect = self.parse_overlay(buffer, buffer.shift(2))

        if action == 0:
            return SetToHotkeyEvent(frames, pid, type, code, hotkey, deselect)
        elif action == 1:
            return AddToHotkeyEvent(frames, pid, type, code, hotkey, deselect)
        elif action == 2:
            return GetFromHotkeyEvent(frames, pid, type, code, hotkey, deselect)
        else:
            raise ParseError("Hotkey Action '{0}' unknown")

    def parse_ability_event(self, buffer, frames, type, code, pid):
        flag = buffer.read_byte()
        atype = buffer.read_byte()

        if atype & 0x20: # command card
            return self.command_card(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x40: # location/move
            return self.right_click_move(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x80: # right-click on target?
            return self.right_click_target(buffer, frames, type, code, pid, flag, atype)

        raise ParseError()

    def command_card(self, buffer, frames, type, code, pid, flag, atype):
        ability = buffer.read_short(endian=BIG_ENDIAN)

        if flag in (0x29, 0x19, 0x14, 0x0c): # cancels
            # creation autoid number / object id
            ability = ability << 8 | buffer.read_byte()
            created_id = buffer.read_object_id()
            # TODO : expose the id
            return AbilityEvent(frames, pid, type, code, ability)

        else:
            ability_flags = buffer.shift(6)
            ability = ability << 8 | ability_flags

            if ability_flags & 0x10:
                x = buffer.read_short(BIG_ENDIAN)/256.0
                buffer.read(bits=5) # what is this for?
                y = buffer.read_short(BIG_ENDIAN)/256.0
                buffer.read(bits=5) # I'll just assume we should do it again
                buffer.read_hex(4)
                return LocationAbilityEvent(frames, pid, type, code, ability, (x,y))

            elif ability_flags & 0x20:
                # ability(3), object id (4),  object type (2), ?? (10)
                code = buffer.read_short() # code??
                target = (buffer.read_object_id(), buffer.read_object_type())
                buffer.read_hex(10)
                return TargetAbilityEvent(frames, pid, type, code, ability, target)

            else:
                return SelfAbilityEvent(frames,pid,type,code,ability)

    def right_click_target(self, buffer, frames, type, code, pid, flag, atype):
        # ability (2), object id (4), object type (2), ?? (10)
        ability = buffer.read_short(endian=BIG_ENDIAN)
        obj_id = buffer.read_object_id()
        obj_type = buffer.read_object_type()
        target = (obj_id, obj_type,)
        buffer.skip(10)
        return TargetAbilityEvent(frames, pid, type, code, ability, target)

    def right_click_move(self, buffer, frames, type, code, pid, flag, atype):
        #10 bytes total, coordinates have a different format?
        #X coordinate definitely is the first byte, with (hopefully) y next
        x = buffer.read_short(BIG_ENDIAN)/256.0
        y = buffer.read_short(BIG_ENDIAN)/256.0
        buffer.skip(6)
        return LocationAbilityEvent(frames, pid, type, code, None, (x,y))


class GameEventsReader_18574(GameEventsReader_16561):
    def cancel(self, buffer, frames, type, code, pid, flag, atype):
        ability = buffer.read_short(endian=BIG_ENDIAN)
        ability = ability << 8 | buffer.read_byte()

        # creation autoid number / object id
        created_id = buffer.read_object_id()
        # TODO : expose the id
        return AbilityEvent(frames, pid, type, code, ability)

    def parse_ability_event(self, buffer, frames, type, code, pid):
        """Moves the right click move to the top level"""
        flag = buffer.read_byte()
        atype = buffer.read_byte()

        if atype & 0x20: # cancels only now
            return self.cancel(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x40: # all command card abilities?
            return self.command_card(buffer, frames, type, code, pid, flag, atype)
        elif atype & 0x80: # right-click on target?
            return self.right_click_target(buffer, frames, type, code, pid, flag, atype)
        elif atype < 0x10: #new to patch 1.3.3, location now??
            return self.right_click_move(buffer, frames, type, code, pid, flag, atype)

        raise ParseError()

    def right_click_move(self, buffer, frames, type, code, pid, flag, atype):
        # This may port back to previous versions. Haven't checked
        # Can differ by up to (+/-1, +/-8) from sc2gears readings
        # See command_card implementation for details
        x = buffer.read_short(BIG_ENDIAN)/256.0
        buffer.shift(5) # what is this for, why 5 bits instead of 4?
        y = buffer.read_short(BIG_ENDIAN)/256.0
        buffer.read(bits=5) # I'll just assume we should do it again
        buffer.skip(4)
        return LocationAbilityEvent(frames, pid, type, code, 0x3601, (x,y))

    def right_click_target(self, buffer, frames, type, code, pid, flag, atype):
        # ability (2), object id (4), object type (2), ?? (10)
        ability = buffer.read_short(endian=BIG_ENDIAN)
        buffer.shift(1) # weird shift..
        target = (buffer.read_int(BIG_ENDIAN), buffer.read_short(BIG_ENDIAN))
        buffer.skip(9)
        return TargetAbilityEvent(frames, pid, type, code, ability, target)

    def command_card(self, buffer, frames, type, code, pid, flag, atype):
        # ability flags one longer now and shifted << 1
        ability = buffer.read_short(endian=BIG_ENDIAN)
        ability = ability << 8 | buffer.shift(7)

        if ability & 0x20:
            # Matches sc2gears, but has crazy alignments. Example:
            #   0c210b0440002a20b000546ab600007c3f
            #   88.0,87.3 ~ (0x58,0x57)
            #   20 0 010000
            #   b0 10110000
            #   00 00000000
            #   54 01010100
            #   6a 01101010
            #   b6 10110110
            #
            #   00000000.                |
            #    1011000.0               |
            #          0.0000000         |
            #   01011000.0000000         |
            #
            #   01010100.                |
            #        011.01010           |
            #           .      10110110  |
            #
            # TODO: Check if these are actually (somehow) the right numbers
            #x = ((buffer.shift(1) << 23) | (buffer.read_byte() << 15) | (buffer.read_byte() << 9)
            #y = (buffer.read_byte() << 16) | (buffer.read_byte() << 11) | (buffer.read_byte() << 2)
            #x = x/2.0**16
            #y = y/2.0**16
            #buffer.skip(4)
            #
            # This doesn't match sc2gears, but makes a hell of a lot more sense
            #   0c210b0440002a20b000546ab600007c3f
            #   (Xx/256.0, Yy/256.0)
            #
            #   20 X 010000
            #   b0 XXXXXXXx
            #   00 ?xxxxxxx
            #   54 YYYY????
            #   6a YYYYyyyy
            #   b6 ????yyyy
            #
            # Can differ by up to (+/-1, +/-8) from sc2gears readings
            x = buffer.read_short(BIG_ENDIAN)/256.0
            buffer.read(bits=5) # what is this for?
            y = buffer.read_short(BIG_ENDIAN)/256.0
            buffer.read(bits=4) # I'll just assume we should do it again
            buffer.skip(4)
            return LocationAbilityEvent(frames, pid, type, code, ability, (x,y))

        elif ability & 0x40:
            buffer.read_short()
            target = (buffer.read_int(BIG_ENDIAN),buffer.read_short(BIG_ENDIAN))
            buffer.skip(10)
            return TargetAbilityEvent(frames, pid, type, code, ability, target)

        else:
            return SelfAbilityEvent(frames, pid, type, code, ability)


class GameEventsReader_19595(GameEventsReader_18574):
    def command_card(self, buffer, frames, type, code, pid, flag, atype):
        # Why only read 7 of the bits?
        ability = buffer.read_short(endian=BIG_ENDIAN)
        ability = ability << 8 | buffer.shift(7)

        if ability & 0x20:
            # Can differ by up to (+/-1, +/-8) from sc2gears readings
            # See 18574 implementation for details
            x = buffer.read_short(BIG_ENDIAN)/256.0
            buffer.read(bits=5) # we could do some creative addition here
            y = buffer.read_short(BIG_ENDIAN)/256.0
            buffer.shift(4) # we could do some creative addition here
            buffer.skip(4)
            return LocationAbilityEvent(frames, pid, type, code, ability, (x,y))

        elif ability & 0x40:
            # extra byte long
            buffer.read_short()
            target = (buffer.read_int(BIG_ENDIAN),buffer.read_short(BIG_ENDIAN))
            buffer.skip(11)
            return TargetAbilityEvent(frames, pid, type, code, ability, target)

        else:
            return SelfAbilityEvent(frames, pid, type, code, ability)

    def right_click_target(self, buffer, frames, type, code, pid, flag, atype):
        # extra byte long
        ability = buffer.read_short(endian=BIG_ENDIAN)
        buffer.shift(1) # weird shift..
        target = (buffer.read_int(BIG_ENDIAN), buffer.read_short(BIG_ENDIAN))
        buffer.skip(10)
        return TargetAbilityEvent(frames, pid, type, code, ability, target)
