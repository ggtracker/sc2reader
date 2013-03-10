# -*- coding: utf-8 -*-
from __future__ import absolute_import

import struct

from collections import defaultdict
from itertools import chain

from sc2reader.exceptions import ParseError, ReadError
from sc2reader.objects import *
from sc2reader.events import *
from sc2reader.utils import AttributeDict
from sc2reader.decoders import BitPackedDecoder, ByteDecoder

class Reader(object):
    def __init__(self, **options):
        self.options = options

    def __call__(self, data, replay):
        raise NotImplementedError

class InitDataReader_Base(Reader):

    def __call__(self, data, replay):
        data = BitPackedDecoder(data)

        init_data = dict( #58
            player_init_data = [dict( #38
                    name = data.read_aligned_bytes(data.read_uint8()),
                    random_seed = data.read_uint32(),
                    race_preference = data.read_uint8() if data.read_bool() else None, #38
                    team_preference = data.read_uint8() if data.read_bool() else None, #39
                    test_map = data.read_bool(),
                    test_auto = data.read_bool(),
                    examine = data.read_bool(),
                    observe = data.read_bits(2),
                ) for i in range(data.read_bits(5))
            ],
        )

        distance = data.read_range(data.tell(), data.length).find('s2ma')
        data.read_aligned_bytes(distance)

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
        while data.peek(4) == 's2ma':
            map_data.append(DepotFile(data.read_aligned_bytes(40)))

        return AttributeDict(
            map_data=map_data,
            player_names=[d['name'] for d in init_data['player_init_data'] if d['name']],
            sc_account_id=None,#sc_account_id,
        )

class InitDataReader_23260(Reader):

    def __call__(self, data, replay):
        data = BitPackedDecoder(data)

        init_data = dict( #58
            player_init_data = [dict( #38
                    name = data.read_aligned_bytes(data.read_uint8()),
                    random_seed = data.read_uint32(),
                    race_preference = data.read_uint8() if data.read_bool() else None, #38
                    team_preference = data.read_uint8() if data.read_bool() else None, #39
                    test_map = data.read_bool(),
                    test_auto = data.read_bool(),
                    examine = data.read_bool(),
                    observe = data.read_bits(2),
                ) for i in range(data.read_bits(5))
            ],

            game_description = dict( # 48
                random_value = data.read_uint32(), # 4
                game_cache_name = data.read_aligned_bytes(data.read_bits(10)), # 24
                game_options = dict( #40
                        lock_teams = data.read_bool(), #27
                        teams_together = data.read_bool(),
                        advanced_shared_control = data.read_bool(),
                        random_races = data.read_bool(),
                        battle_net = data.read_bool(),
                        amm = data.read_bool(),
                        competitive = data.read_bool(),
                        no_victory_or_defeat = data.read_bool(),
                        fog = data.read_bits(2), #19
                        observers = data.read_bits(2), #19
                        user_difficulty = data.read_bits(2), #19
                        client_debug_flags = data.read_uint64(), #15
                    ),
                game_speed = data.read_bits(3),
                game_type = data.read_bits(3),
                max_users = data.read_bits(5),
                max_observers = data.read_bits(5),
                max_players = data.read_bits(5),
                max_teams = data.read_bits(4)+1,
                max_colors = data.read_bits(6),
                max_races = data.read_uint8()+1,
                max_controls = data.read_uint8()+1,
                map_size_x = data.read_uint8(),
                map_size_y = data.read_uint8(),
                map_file_sync_checksum = data.read_uint32(),
                map_file_name = data.read_aligned_bytes(data.read_bits(11)),
                map_author_name = data.read_aligned_bytes(data.read_uint8()),
                mod_file_sync_checksum = data.read_uint32(),
                slot_descriptions = [dict( #47
                        allowed_colors = data.read_bits(data.read_bits(6)),
                        allowed_races = data.read_bits(data.read_uint8()),
                        allowedDifficulty = data.read_bits(data.read_bits(6)),
                        allowedControls = data.read_bits(data.read_uint8()),
                        allowed_observe_types = data.read_bits(data.read_bits(2)),
                    ) for i in range(data.read_bits(5))],
                default_difficulty = data.read_bits(6),
                cache_handles = [
                    DepotFile(data.read_aligned_bytes(40)) for i in range(data.read_bits(6))
                ],
                is_blizzardMap = data.read_bool(),
                is_premade_ffa = data.read_bool(),
            ),

            lobby_state = dict( #56
                phase = data.read_bits(3),
                max_users = data.read_bits(5),
                max_observers = data.read_bits(5),
                slots = [dict( #54
                        control = data.read_uint8(),
                        user_id = data.read_bits(4) if data.read_bool() else None,
                        team_id = data.read_bits(4),
                        colorPref = data.read_bits(5) if data.read_bool() else None,
                        race_pref = data.read_uint8() if data.read_bool() else None,
                        difficulty = data.read_bits(6),
                        handicap = data.read_bits(7),
                        observe = data.read_bits(2),
                        rewards = [data.read_uint32() for i in range(data.read_bits(5))], # 52
                        toon_handle = data.read_aligned_bytes(data.read_bits(7)), # 14
                        licenses = [data.read_uint32() for i in range(data.read_bits(9))], # 53
                    ) for i in range(data.read_bits(5))], # 58
                random_seed = data.read_uint32(),
                host_user_id = data.read_bits(4) if data.read_bool() else None, # 52
                is_single_player = data.read_bool(), # 27
                game_duration = data.read_uint32(), # 4
                default_difficulty = data.read_bits(6), # 1
            ),
        )

        return AttributeDict(
            map_data=init_data['game_description']['cache_handles'],
            player_names=[d['name'] for d in init_data['player_init_data'] if d['name']],
            sc_account_id=None,#sc_account_id,
        )

class InitDataReader_24764(InitDataReader_Base):

    def __call__(self, data, replay):
        data = BitPackedDecoder(data)

        init_data = dict(
            player_init_data = [dict(
                    name = data.read_aligned_bytes(data.read_uint8()),
                    clan_tag = data.read_aligned_bytes(data.read_uint8()) if data.read_bool() else "", # 36
                    highest_league = data.read_uint8() if data.read_bool() else None, #20
                    combined_race_levels = data.read_uint32() if data.read_bool() else None, #37
                    random_seed = data.read_uint32(),
                    race_preference = data.read_uint8() if data.read_bool() else None, #38
                    team_preference = data.read_uint8() if data.read_bool() else None, #39
                    test_map = data.read_bool(),
                    test_auto = data.read_bool(),
                    examine = data.read_bool(),
                    custom_interface = data.read_bool(),
                    observe = data.read_bits(2),
                ) for i in range(data.read_bits(5))
            ],

            game_description = dict(
                random_value = data.read_uint32(), # 4
                game_cache_name = data.read_aligned_bytes(data.read_bits(10)), # 24
                game_options = dict(
                        lock_teams = data.read_bool(), #27
                        teams_together = data.read_bool(),
                        advanced_shared_control = data.read_bool(),
                        random_races = data.read_bool(),
                        battle_net = data.read_bool(),
                        amm = data.read_bool(),
                        competitive = data.read_bool(),
                        no_victory_or_defeat = data.read_bool(),
                        fog = data.read_bits(2), #19
                        observers = data.read_bits(2), #19
                        user_difficulty = data.read_bits(2), #19
                        client_debug_flags = data.read_uint64(), #15
                    ),
                game_speed = data.read_bits(3),
                game_type = data.read_bits(3),
                max_users = data.read_bits(5),
                max_observers = data.read_bits(5),
                max_players = data.read_bits(5),
                max_teams = data.read_bits(4)+1,
                max_colors = data.read_bits(6),
                max_races = data.read_uint8()+1,
                max_controls = data.read_uint8()+1,
                map_size_x = data.read_uint8(),
                map_size_y = data.read_uint8(),
                map_file_sync_checksum = data.read_uint32(),
                map_file_name = data.read_aligned_bytes(data.read_bits(11)),
                map_author_name = data.read_aligned_bytes(data.read_uint8()),
                mod_file_sync_checksum = data.read_uint32(),
                slot_descriptions = [dict( #50
                        allowed_colors = data.read_bits(data.read_bits(6)),
                        allowed_races = data.read_bits(data.read_uint8()),
                        allowedDifficulty = data.read_bits(data.read_bits(6)),
                        allowedControls = data.read_bits(data.read_uint8()),
                        allowed_observe_types = data.read_bits(data.read_bits(2)),
                        allowed_ai_builds = data.read_bits(data.read_bits(7)),
                    ) for i in range(data.read_bits(5))],
                default_difficulty = data.read_bits(6),
                default_AI_build = data.read_bits(7),
                cache_handles = [
                    DepotFile(data.read_aligned_bytes(40)) for i in range(data.read_bits(6))
                ],
                is_blizzardMap = data.read_bool(),
                is_premade_ffa = data.read_bool(),
                is_coop_mode = data.read_bool(),
            ),

            lobby_state = dict(
                phase = data.read_bits(3),
                max_users = data.read_bits(5),
                max_observers = data.read_bits(5),
                slots = [dict(
                        control = data.read_uint8(),
                        user_id = data.read_bits(4) if data.read_bool() else None,
                        team_id = data.read_bits(4),
                        colorPref = data.read_bits(5) if data.read_bool() else None,
                        race_pref = data.read_uint8() if data.read_bool() else None,
                        difficulty = data.read_bits(6),
                        ai_build = data.read_bits(7),
                        handicap = data.read_bits(7),
                        observe = data.read_bits(2),
                        working_set_slot_id = data.read_uint8() if data.read_bool() else None,
                        rewards = [data.read_uint32() for i in range(data.read_bits(6))],
                        toon_handle = data.read_aligned_bytes(data.read_bits(7)), # 14
                        licenses = [data.read_uint32() for i in range(data.read_bits(9))], # 56
                    ) for i in range(data.read_bits(5))], # 58
                random_seed = data.read_uint32(),
                host_user_id = data.read_bits(4) if data.read_bool() else None, # 52
                is_single_player = data.read_bool(), # 27
                game_duration = data.read_uint32(), # 4
                default_difficulty = data.read_bits(6), # 1
                default_ai_build = data.read_bits(7), # 0
            ),
        )
        return AttributeDict(
            map_data=init_data['game_description']['cache_handles'],
            player_names=[d['name'] for d in init_data['player_init_data'] if d['name']],
            sc_account_id=None,#sc_account_id,
        )


class AttributesEventsReader_Base(Reader):
    header_length = 4
    offset=False

    def __call__(self, data, replay):
        # The replay.attribute.events file is comprised of a small header and
        # single long list of attributes with the 0x00 00 03 E7 header on each
        # element. Each element holds a four byte attribute id code, a one byte
        # player id, and a four byte value code. Unlike the other files, this
        # file is stored in little endian format.
        #
        # See: ``objects.Attribute`` for attribute id and value lookup logic
        #
        data = ByteDecoder(data, endian='LITTLE')
        attribute_events = list()
        data.read_bytes(self.header_length)
        for attribute in range(data.read_uint32()):
            info = struct.unpack('<IIB4s', data.read(13))
            attribute_events.append(Attribute(*info))

        return attribute_events


class AttributesEventsReader_17326(AttributesEventsReader_Base):
    # The header length is increased from 4 to 5 bytes from patch 17326 and on.
    header_length = 5


class DetailsReader_Base(Reader):
    PlayerData = namedtuple('PlayerData',['name','bnet','race','color','unknown1','unknown2','handicap','unknown3','result'])
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','dependencies','unknown8','unknown9','unknown10'])

    def __call__(self, data, replay):
        # The entire details file is just a serialized data structure
        #
        # See: utils.Replaydata.read_struct for a format description
        #
        # The general file structure is as follows:
        #   TODO: add the data types for each node in the structure
        #
        #   List of Players:
        #       Name
        #       BnetData:
        #           unknown1
        #           unknown2
        #           subregion_id
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
        #       Team Number - according to András
        #       Result (0,1,2) - (Unknown, Win, Loss), thanks András
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
        details = BitPackedDecoder(data).read_struct()

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
            player = self.PlayerData(*ordered_values(pdata))
            players.append(player)
        details[0] = players
        details[10] = [DepotFile(bytes) for bytes in details[10]]
        # As a final touch, label all extracted information using the Details
        # named tuple from objects.py
        return self.Details(*ordered_values(details))

class DetailsReader_22612(DetailsReader_Base):
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','dependencies','unknown8','unknown9','unknown10', 'unknown11'])

class DetailsReader_Beta(DetailsReader_Base):
    Details = namedtuple('Details',['players','map','unknown1','unknown2','os','file_time','utc_adjustment','unknown4','unknown5','unknown6','dependencies','unknown8','unknown9','unknown10', 'unknown11', 'unknown12'])

class DetailsReader_Beta_24764(DetailsReader_Beta):
    PlayerData = namedtuple('PlayerData',['name','bnet','race','color','unknown1','unknown2','handicap','unknown3','result','unknown4'])

class MessageEventsReader_Base(Reader):
    TARGET_BITS=3
    def __call__(self, data, replay):
        # The replay.message.events file is a single long list containing three
        # different element types (minimap pings, player messages, and some sort
        # of network packets); each differentiated by flags.
        data = BitPackedDecoder(data)
        pings = list()
        messages = list()
        packets = list()

        frame = 0
        while not data.done():
            # All the element types share the same time, pid, flags header.
            frame += data.read_frames()
            pid = data.read_bits(5)
            t = data.read_bits(3)
            flags = data.read_uint8()

            if flags in (0x83,0x89):
                # We need some tests for this, probably not right
                x = data.read_uint32()
                y = data.read_uint32()
                pings.append(PingEvent(frame, pid, flags, x, y))

            elif flags == 0x80:
                info = data.read_bytes(4)
                packets.append(PacketEvent(frame, pid, flags, info))

            elif flags & 0x80 == 0:
                lo_mask = 2**self.TARGET_BITS-1
                hi_mask = 0xFF ^ lo_mask
                target = flags & lo_mask
                extension = (flags & hi_mask) << 3
                length = data.read_uint8()
                text = data.read_bytes(length + extension)
                messages.append(ChatEvent(frame, pid, flags, target, text, (flags, lo_mask, hi_mask, length, extension)))

        return AttributeDict(pings=pings, messages=messages, packets=packets)

class MessageEventsReader_Beta_24247(MessageEventsReader_Base):
    TARGET_BITS=4

class GameEventsReader_Base(object):
    PLAYER_JOIN_FLAGS = 4
    PLAYER_ABILITY_FLAGS = 17
    ABILITY_TEAM_FLAG = False
    UNIT_INDEX_BITS = 8
    HOTKEY_OVERLAY = 0

    def __init__(self):
        self.EVENT_DISPATCH = {
            0x05: self.game_start_event,
            0x07: self.beta_join_event,
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

    def __call__(self, data, replay):
        data = BitPackedDecoder(data)
        game_events = list()
        fstamp = 0
        debug = replay.opt.debug
        data_length = data.length
        read_frames =  data.read_frames
        read_bits = data.read_bits
        read_uint8 = data.read_uint8
        tell = data.tell
        read_bytes = data.read_bytes
        byte_align = data.byte_align
        append = game_events.append
        event_start = 0

        try:
            while event_start != data_length:
                fstamp += read_frames()
                pid = read_bits(5)
                event_type = read_bits(7)

                # Check for a lookup
                if event_type in self.EVENT_DISPATCH:
                    event = self.EVENT_DISPATCH[event_type](data, fstamp, pid, event_type)
                    if debug:
                        event.bytes = data.read_range(event_start, tell())
                    append(event)

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
                elif event_type == 0x48:
                    read_bytes(4)
                elif event_type == 0x4C:
                    read_bits(4)
                elif event_type == 0x59:
                    read_bytes(4)
                elif event_type == 0x00:
                    read_bytes(1)

                # Otherwise throw a read error
                else:
                    raise ReadError("Event type {0} unknown at position {1}.".format(hex(event_type),hex(event_start)), event_type, event_start, replay, game_events, data)

                byte_align()
                event_start = tell()

            return game_events
        except ParseError as e:
            raise ReadError("Parse error '{0}' unknown at position {1}.".format(e.msg, hex(event_start)), event_type, event_start, replay, game_events, data)
        except EOFError as e:
            raise ReadError("EOFError error '{0}' unknown at position {1}.".format(e.msg, hex(event_start)), event_type, event_start, replay, game_events, data)



class GameEventsReader_16117(GameEventsReader_Base):
    def game_start_event(self, data, fstamp, pid, event_type):
        return GameStartEvent(fstamp, pid, event_type)

    def beta_join_event(self, data, fstamp, pid, event_type):
        flags = data.read_bytes(5)
        return BetaJoinEvent(fstamp, pid, event_type, flags)

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
        switch = data.read_uint8()
        if switch in (0x30,0x50):
            data.read_bytes(1)
        data.read_bytes(24)
        return AbilityEvent(fstamp, pid, event_type, None, None)

    def player_selection_event(self, data, fstamp, pid, event_type):
        bank = data.read_bits(4)
        subgroup = data.read_bits(self.UNIT_INDEX_BITS) #??
        overlay = self._parse_selection_update(data)

        type_count = data.read_bits(self.UNIT_INDEX_BITS)
        unit_type_info = [(data.read_uint16(), data.read_uint8(), data.read_bits(self.UNIT_INDEX_BITS)) for index in range(type_count)]

        unit_count = data.read_bits(self.UNIT_INDEX_BITS)
        unit_ids = [data.read_uint32() for index in range(unit_count)]

        unit_types = chain(*[[utype]*count for (utype, flags, count) in unit_type_info])
        unit_flags = chain(*[[flags]*count for (utype, flags, count) in unit_type_info])
        units = list(zip(unit_ids, unit_types, unit_flags))
        return SelectionEvent(fstamp, pid, event_type, bank, units, overlay)

    def player_hotkey_event(self, data, fstamp, pid, event_type):
        hotkey = data.read_bits(4)
        action = data.read_bits(2)

        if self.HOTKEY_OVERLAY:
            overlay = self._parse_selection_update(data)
        else:
            overlay = (1,0)

        if action == 0:
            return SetToHotkeyEvent(fstamp, pid, event_type, hotkey, overlay)
        elif action == 1:
            return AddToHotkeyEvent(fstamp, pid, event_type, hotkey, overlay)
        elif action == 2:
            return GetFromHotkeyEvent(fstamp, pid, event_type, hotkey, overlay)
        else:
            raise ParseError("Hotkey Action '{0}' unknown".format(hotkey))

    def player_send_resource_event(self, data, fstamp, pid, event_type):
        target = data.read_bits(4)-1 # Convert from 1-offset to 0-offset
        unknown = data.read_bits(4) #??
        minerals = data.read_bits(32)
        vespene = data.read_bits(32)
        terrazine = data.read_bits(32) #??
        custom = data.read_bits(32) #??
        return SendResourceEvent(fstamp, pid, event_type, target, minerals, vespene, terrazine, custom)

    def player_request_resource_event(self, data, fstamp, pid, event_type):
        flags = data.read_bits(3) #??
        custom = minerals = vespene = terrazine = 0
        if data.read_bool():
            custom = data.read_bits(31) #??
        if data.read_bool():
            minerals = data.read_bits(31)
        if data.read_bool():
            vespene = data.read_bits(31)
        if data.read_bool():
            terrazine = data.read_bits(31) #??
        return RequestResourceEvent(fstamp, pid, event_type, minerals, vespene, terrazine, custom)

    def camera_event(self, data, fstamp, pid, event_type):
        # From https://github.com/Mischanix/sc2replay-csharp/wiki/replay.game.events
        x = data.read_uint16()/256.0
        y = data.read_uint16()/256.0
        distance = pitch = yaw = height = 0
        if data.read_bool():
            distance = data.read_uint16()/256.0
        if data.read_bool():
            #Note: this angle is relative to the horizontal plane, but the editor shows the angle relative to the vertical plane. Subtract from 90 degrees to convert.
            pitch = data.read_uint16() #?
            pitch = 45 * (((((pitch * 0x10 - 0x2000) << 17) - 1) >> 17) + 1) / 4096.0
        if data.read_bool():
            #Note: this angle is the vector from the camera head to the camera target projected on to the x-y plane in positive coordinates. So, default is 90 degrees, while insert and delete produce 45 and 135 degrees by default.
            yaw = data.read_uint16() #?
            yaw = 45 * (((((yaw * 0x10 - 0x2000) << 17) - 1) >> 17) + 1) / 4096.0
        if data.read_bool():
            height_offset = data.read_uint16()/256.0
        return CameraEvent(fstamp, pid, event_type, x, y, distance, pitch, yaw, height)


class GameEventsReader_16561(GameEventsReader_16117):
    HOTKEY_OVERLAY = 1

    # Don't want to do this more than once
    SINGLE_BIT_MASKS = [0x1 << i for i in range(2**9)]

    def _parse_selection_update(self, data):
        update_type = data.read_bits(2)
        if update_type == 1:
            # If the mask_length is not a multiple of 8 the bit_shift on
            # the data buffer will change and cause the last byte to be
            # an odd length. This correctly sizes the last byte.
            bits_left = mask_length = data.read_bits(self.UNIT_INDEX_BITS)
            bits = data.read_bits(mask_length)
            mask = list()
            shift_diff = (mask_length+data._bit_shift)%8 - data._bit_shift
            if shift_diff > 0:
                mask = [bits & data._lo_masks[shift_diff]]
                bits = bits >> shift_diff
                bits_left -= shift_diff
            elif shift_diff < 0:
                mask = [bits & data._lo_masks[8+shift_diff]]
                bits = bits >> (8+shift_diff)
                bits_left -= 8+shift_diff

            # Now shift the rest of the bits off into the mask in byte-sized
            # chunks in reverse order. No idea why it'd be stored like this.
            while bits_left!=0:
                mask.insert(0,bits & 0xFF)
                bits = bits >> 8
                bits_left -= 8

            # Compile the finished mask into a large integer for bit checks
            bit_mask = sum([c<<(i*8) for i,c in enumerate(mask)])

            # Change mask representation from an int to a bit array with
            #   True => Deselect, False => Keep
            mask = [(bit_mask & bit != 0) for bit in self.SINGLE_BIT_MASKS[:mask_length]]

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

        default_ability = not data.read_bool()
        if not default_ability:
            ability = data.read_uint16() << 5 | data.read_bits(5)
            default_actor = not data.read_bool()
        else:
            ability = 0

        target_type = data.read_bits(2)
        if target_type == 1:
            x = data.read_bits(20)/4096.0
            y = data.read_bits(20)/4096.0
            z = data.read_uint32()
            z = (z>>1)/8192.0 * pow(-1, z & 0x1)
            unknown = data.read_bool()
            return LocationAbilityEvent(fstamp, pid, event_type, ability, flags, (x, y, z))

        elif target_type == 2:
            player = team = None

            data.read_bytes(2)
            unit = (data.read_uint32(), data.read_uint16())
            if fstamp == 9007 or unit[0] == 0x94880002:
                print fstamp, hex(unit[0])
            if self.ABILITY_TEAM_FLAG and data.read_bool():
                team = data.read_bits(4)

            if data.read_bool():
                player = data.read_bits(4)

            x = data.read_bits(20)/4096.0
            y = data.read_bits(20)/4096.0
            z = data.read_uint32()
            z = (z>>1)/8192.0 * pow(-1, z & 0x1)
            unknown = data.read_bool()
            return TargetAbilityEvent(fstamp, pid, event_type, ability, flags, unit, player, team, (x, y, z))

        elif target_type == 3:
            unit_id = data.read_uint32()
            unknown = data.read_bool()
            return SelfAbilityEvent(fstamp, pid, event_type, ability, flags, unit_id)

        else:
            return AbilityEvent(fstamp, pid, event_type, ability, flags)


class GameEventsReader_18574(GameEventsReader_16561):
    PLAYER_ABILITY_FLAGS = 18

class GameEventsReader_19595(GameEventsReader_18574):
    ABILITY_TEAM_FLAG = True

class GameEventsReader_22612(GameEventsReader_19595):
    PLAYER_JOIN_FLAGS = 5 # or 6
    PLAYER_ABILITY_FLAGS = 20
    UNIT_INDEX_BITS = 9 # Now can select up to 512 units

class GameEventsReader_Beta(GameEventsReader_22612):

    def __init__(self):
        super(GameEventsReader_Beta, self).__init__()
        self.EVENT_DISPATCH[0x65] = self.beta_win_event
        self.EVENT_DISPATCH[0x2B] = self.beta_end_game_event

    def beta_win_event(self, data, fstamp, pid, event_type):
        flags = 0
        return BetaWinEvent(fstamp, pid, event_type, flags)

    def beta_end_game_event(self, data, fstamp, pid, event_type):
        flags = data.read_bits(4)
        count = data.read_uint8()
        for name in range(count):
            data.read_bytes(data.read_uint8())
        data.read_uint8()
        return UnknownEvent(fstamp, pid, event_type)

    def camera_event(self, data, fstamp, pid, event_type):
        x = y= distance = pitch = yaw = height = 0
        if data.read_bool():
            x = data.read_uint16()/256.0
            y = data.read_uint16()/256.0
        if data.read_bool():
            distance = data.read_uint16()/256.0
        if data.read_bool():
            #Note: this angle is relative to the horizontal plane, but the editor shows the angle relative to the vertical plane. Subtract from 90 degrees to convert.
            pitch = data.read_uint16() #?
            pitch = 45 * (((((pitch * 0x10 - 0x2000) << 17) - 1) >> 17) + 1) / 4096.0
        if data.read_bool():
            #Note: this angle is the vector from the camera head to the camera target projected on to the x-y plane in positive coordinates. So, default is 90 degrees, while insert and delete produce 45 and 135 degrees by default.
            yaw = data.read_uint16() #?
            yaw = 45 * (((((yaw * 0x10 - 0x2000) << 17) - 1) >> 17) + 1) / 4096.0
        return CameraEvent(fstamp, pid, event_type, x, y, distance, pitch, yaw, height)

    def player_selection_event(self, data, fstamp, pid, event_type):
        bank = data.read_bits(4)
        subgroup = data.read_bits(self.UNIT_INDEX_BITS) #??
        overlay = self._parse_selection_update(data)

        type_count = data.read_bits(self.UNIT_INDEX_BITS)
        unit_type_info = [(data.read_uint16(), data.read_uint16(), data.read_bits(self.UNIT_INDEX_BITS)) for index in range(type_count)]

        unit_count = data.read_bits(self.UNIT_INDEX_BITS)
        unit_ids = [data.read_uint32() for index in range(unit_count)]

        unit_types = chain(*[[utype]*count for (utype, flags, count) in unit_type_info])
        unit_flags = chain(*[[flags]*count for (utype, flags, count) in unit_type_info])
        units = list(zip(unit_ids, unit_types, unit_flags))
        return SelectionEvent(fstamp, pid, event_type, bank, units, overlay)

class GameEventsReader_Beta_23925(GameEventsReader_Beta):
    PLAYER_JOIN_FLAGS = 32
