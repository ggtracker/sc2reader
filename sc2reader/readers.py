# -*- coding: utf-8 -*-
from __future__ import absolute_import

import struct

from collections import defaultdict
from itertools import chain

from sc2reader.exceptions import ParseError, ReadError
from sc2reader.objects import *
from sc2reader.events.game import *
from sc2reader.events.message import *
from sc2reader.events.tracker import *
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
                    clan_tag = None,
                    highest_league = None,
                    combined_race_levels = None,
                    random_seed = data.read_uint32(),
                    race_preference = data.read_uint8() if data.read_bool() else None, #38
                    team_preference = data.read_uint8() if data.read_bool() else None, #39
                    test_map = data.read_bool(),
                    test_auto = data.read_bool(),
                    examine = data.read_bool(),
                    custom_interface = None,
                    observe = data.read_bits(2),
                ) for i in range(data.read_bits(5))
            ],

            game_description = dict( # 48
                random_value = None,
                game_cache_name = None,
                game_options = dict( #40
                        lock_teams = None,
                        teams_together = None,
                        advanced_shared_control = None,
                        random_races = None,
                        battle_net = None,
                        amm = None,
                        competitive = None,
                        no_victory_or_defeat = None,
                        fog = None,
                        observers = None,
                        user_difficulty = None,
                        client_debug_flags = None,
                    ),
                game_speed = None,
                game_type = None,
                max_users = None,
                max_observers = None,
                max_players = None,
                max_teams = None,
                max_colors = None,
                max_races = None,
                max_controls = None,
                map_size_x = None,
                map_size_y = None,
                map_file_sync_checksum = None,
                map_file_name = None,
                map_author_name = None,
                mod_file_sync_checksum = None,
                slot_descriptions = [dict( #47
                        allowed_colors = None,
                        allowed_races = None,
                        allowedDifficulty = None,
                        allowedControls = None,
                        allowed_observe_types = None,
                        allowed_ai_builds = None,
                    ) for i in range(0)],
                default_difficulty = None,
                default_AI_build = None,
                cache_handles = [],
                is_blizzardMap = None,
                is_premade_ffa = None,
                is_coop_mode = None,
            ),

            lobby_state = dict( #56
                phase = None,
                max_users = None,
                max_observers = None,
                slots = [dict( #54
                        control = None,
                        user_id = None,
                        team_id = None,
                        colorPref = None,
                        race_pref = None,
                        difficulty = None,
                        ai_build = None,
                        handicap = None,
                        observe = None,
                        working_set_slot_id = None,
                        rewards = [],
                        toon_handle = None,
                        licenses = [],
                    ) for i in range(0)], # 58
                random_seed = None,
                host_user_id = None,
                is_single_player = None,
                game_duration = None,
                default_difficulty = None,
                default_ai_build = 0,
            ),
        )

        distance = data.read_range(data.tell(), data.length).find('s2ma')
        data.read_aligned_bytes(distance)

        map_data = list()
        while data.peek(4) == 's2ma':
            depot_file = DepotFile(data.read_aligned_bytes(40))
            init_data['game_description']['cache_handles'].append(depot_file)

        init_data.setdefault('game_description',dict())['cache_handles'] = map_data
        return init_data

class InitDataReader_23260(Reader):

    def __call__(self, data, replay):
        data = BitPackedDecoder(data)

        init_data = dict( #58
            player_init_data = [dict( #38
                    name = data.read_aligned_bytes(data.read_uint8()),
                    clan_tag = None,
                    highest_league = None,
                    combined_race_levels = None,
                    random_seed = data.read_uint32(),
                    race_preference = data.read_uint8() if data.read_bool() else None, #38
                    team_preference = data.read_uint8() if data.read_bool() else None, #39
                    test_map = data.read_bool(),
                    test_auto = data.read_bool(),
                    examine = data.read_bool(),
                    custom_interface = None,
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
                        allowed_ai_builds = None
                    ) for i in range(data.read_bits(5))],
                default_difficulty = data.read_bits(6),
                default_AI_build = None,
                cache_handles = [
                    DepotFile(data.read_aligned_bytes(40)) for i in range(data.read_bits(6))
                ],
                is_blizzardMap = data.read_bool(),
                is_premade_ffa = data.read_bool(),
                is_coop_mode = None,
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
                        ai_build = None,
                        handicap = data.read_bits(7),
                        observe = data.read_bits(2),
                        working_set_slot_id = None,
                        rewards = [data.read_uint32() for i in range(data.read_bits(5))], # 52
                        toon_handle = data.read_aligned_bytes(data.read_bits(7)), # 14
                        licenses = [data.read_uint32() for i in range(data.read_bits(9))], # 53
                    ) for i in range(data.read_bits(5))], # 58
                random_seed = data.read_uint32(),
                host_user_id = data.read_bits(4) if data.read_bool() else None, # 52
                is_single_player = data.read_bool(), # 27
                game_duration = data.read_uint32(), # 4
                default_difficulty = data.read_bits(6), # 1
                default_ai_build = 0
            ),
        )

        return init_data

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

        return init_data


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


class GameEventsReader_Base(Reader):

    def __init__(self):
        self.EVENT_DISPATCH = {
            0: (None, self.unknown_event),
            5: (None, self.finished_loading_sync_event),
            7: (None, self.bank_file_event),
            8: (None, self.bank_section_event),
            9: (None, self.bank_key_event),
            10: (None, self.bank_value_event),
            11: (None, self.bank_signature_event),
            12: (UserOptionsEvent, self.user_options_event),
            22: (None, self.save_game_event),
            23: (None, self.save_game_done_event),
            25: (PlayerLeaveEvent, self.player_leave_event),
            26: (None, self.game_cheat_event),
            27: (create_command_event, self.command_event),
            28: (SelectionEvent, self.selection_delta_event),
            29: (create_control_group_event, self.control_group_update_event),
            30: (None, self.selection_sync_check_event),
            31: (None, self.resource_trade_event),
            32: (None, self.trigger_chat_message_event),
            33: (None, self.ai_communicate_event),
            34: (None, self.set_absolute_game_speed_event),
            35: (None, self.add_absolute_game_speed_event),
            36: (None, self.trigger_ping_event),
            37: (None, self.broadcast_cheat_event),
            38: (None, self.alliance_event),
            39: (None, self.unit_click_event),
            40: (None, self.unit_highlight_event),
            41: (None, self.trigger_reply_selected_event),
            44: (None, self.trigger_skipped_event),
            45: (None, self.trigger_sound_length_query_event),
            46: (None, self.trigger_sound_offset_event),
            47: (None, self.trigger_transmission_offset_event),
            48: (None, self.trigger_transmission_complete_event),
            49: (CameraEvent, self.camera_update_event),
            50: (None, self.trigger_abort_mission_event),
            51: (None, self.trigger_purchase_made_event),
            52: (None, self.trigger_purchase_exit_event),
            53: (None, self.trigger_planet_mission_launched_event),
            54: (None, self.trigger_planet_panel_canceled_event),
            55: (None, self.trigger_dialog_control_event),
            56: (None, self.trigger_sound_length_sync_event),
            57: (None, self.trigger_conversation_skipped_event),
            58: (None, self.trigger_mouse_clicked_event),
            59: (None, self.trigger_mouse_moved_event),
            60: (None, self.achievement_awarded_event),
            63: (None, self.trigger_planet_panel_replay_event),
            64: (None, self.trigger_soundtrack_done_event),
            65: (None, self.trigger_planet_mission_selected_event),
            66: (None, self.trigger_key_pressed_event),
            67: (None, self.trigger_movie_function_event),
            68: (None, self.trigger_planet_panel_birth_complete_event),
            69: (None, self.trigger_planet_panel_death_complete_event),
            70: (None, self.resource_request_event),
            71: (None, self.resource_request_fulfill_event),
            72: (None, self.resource_request_cancel_event),
            73: (None, self.trigger_research_panel_exit_event),
            74: (None, self.trigger_research_panel_purchase_event),
            75: (None, self.trigger_research_panel_selection_changed_event),
            76: (None, self.lag_message_event),
            77: (None, self.trigger_mercenary_panel_exit_event),
            78: (None, self.trigger_mercenary_panel_purchase_event),
            79: (None, self.trigger_mercenary_panel_selection_changed_event),
            80: (None, self.trigger_victory_panel_exit_event),
            81: (None, self.trigger_battle_report_panel_exit_event),
            82: (None, self.trigger_battle_report_panel_play_mission_event),
            83: (None, self.trigger_battle_report_panel_play_scene_event),
            84: (None, self.trigger_battle_report_panel_selection_changed_event),
            85: (None, self.trigger_victory_panel_play_mission_again_event),
            86: (None, self.trigger_movie_started_event),
            87: (None, self.trigger_movie_finished_event),
            88: (None, self.decrement_game_time_remaining_event),
            89: (None, self.trigger_portrait_loaded_event),
            90: (None, self.trigger_custom_dialog_dismissed_event),
            91: (None, self.trigger_game_menu_item_selected_event),
            92: (None, self.trigger_camera_move_event),
            93: (None, self.trigger_purchase_panel_selected_purchase_item_changed_event),
            94: (None, self.trigger_purchase_panel_selected_purchase_category_changed_event),
            95: (None, self.trigger_button_pressed_event),
            96: (None, self.trigger_game_credits_finished_event),
            97: (None, self.trigger_cutscene_bookmark_fired_event),
            98: (None, self.trigger_cutscene_end_scene_fired_event),
            99: (None, self.trigger_cutscene_conversation_line_event),
            100: (None, self.trigger_cutscene_conversation_line_missing_event),
        }

    def __call__(self, data, replay):
        data = BitPackedDecoder(data)
        game_events = list()

        # method short cuts, avoid dict lookups
        EVENT_DISPATCH = self.EVENT_DISPATCH
        debug = replay.opt.debug
        tell = data.tell
        read_frames =  data.read_frames
        read_bits = data.read_bits
        byte_align = data.byte_align
        append = game_events.append

        try:
            fstamp = 0
            event_start = 0
            data_length = data.length
            while event_start != data_length:
                fstamp += read_frames()
                pid = read_bits(5)
                event_type = read_bits(7)
                event_class, event_parser = EVENT_DISPATCH.get(event_type, (None, None))
                if event_parser != None:
                    event_data = event_parser(data)
                    if event_class != None:
                        event = event_class(fstamp, pid, event_data)
                        append(event)
                        if debug:
                            event.bytes = data.read_range(event_start, tell())
                    else:
                        pass # Skipping unused events

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

    # Don't want to do this more than once
    SINGLE_BIT_MASKS = [0x1 << i for i in range(2**9)]

    def read_selection_bitmask(self, data, mask_length):
        bits_left = mask_length
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
        # True => Deselect, False => Keep
        return [(bit_mask & bit != 0) for bit in self.SINGLE_BIT_MASKS[:mask_length]]

class GameEventsReader_16117(GameEventsReader_Base):

    def unknown_event(self, data):
        return dict(
            unknown = data.read_bytes(2)
        )

    def finished_loading_sync_event(self, data):
        return None

    def bank_file_event(self, data):
        return dict(
            name = data.read_aligned_bytes(data.read_bits(7)),
        )

    def bank_section_event(self, data):
        return dict(
            name = data.read_aligned_bytes(data.read_bits(6)),
        )

    def bank_key_event(self, data):
        return dict(
            name = data.read_aligned_bytes(data.read_bits(6)),
            type = data.read_uint32(),
            data = data.read_aligned_bytes(data.read_bits(7)),
        )

    def bank_value_event(self, data):
        return dict(
            type = data.read_uint32(),
            name = data.read_aligned_bytes(data.read_bits(6)),
            data = data.read_aligned_bytes(data.read_bits(12)),
        )

    def bank_signature_event(self, data):
        return dict(
            signature=[data.read_uint8() for i in range(data.read_bits(4))],
            toon_handle = None,
        )

    def user_options_event(self, data):
        return dict(
            # I'm just guessing which flags are available here
            game_fully_downloaded = data.read_bool(),
            development_cheats_enabled = data.read_bool(),
            multiplayer_cheats_enabled = data.read_bool(),
            sync_checksumming_enabled = data.read_bool(),
            is_map_to_map_transition = None,
            use_ai_beacons = None,
            base_build_num = None,
            starting_rally = None,
        )

    def save_game_event(self, data):
        return dict(
            file_name = data.read_aligned_bytes(data.read_bits(11)),
            automatic = data.read_bool(),
            overwrite = data.read_bool(),
            name = data.read_aligned_bytes(data.read_uint8(8)),
            description = data.read_aligned_bytes(data.read_bits(10)),
        )

    def save_game_done_event(self, data):
        return None

    def player_leave_event(self, data):
        return None

    def game_cheat_event(self, data):
        return dict(
            point = dict(
                x = data.read_uint32()-2147483648,
                y = data.read_uint32()-2147483648,
            ),
            time = data.read_uint32()-2147483648,
            verb = data.read_aligned_bytes(data.read_bits(10)),
            arguments = data.read_aligned_bytes(data.read_bits(10)),
        )

    def command_event(self, data):
        # TODO: No idea what this is supposed to be like
        data.read_bits(4)
        data.read_bytes(7)
        switch = data.read_uint8()
        if switch in (0x30,0x50):
            data.read_bytes(1)
        data.read_bytes(24)

        # Still, return something with a consistent structure
        return dict(
            flags = None,
            ability = None,
            data = ('None',None),
            other_unit_tag = None,
        )

    def selection_delta_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            subgroup_index = data.read_bits(8),
            remove_mask = ('Mask', self.read_selection_bitmask(data, data.read_bits(8))),
            add_subgroups = [dict(
                    unit_link = data.read_uint16(),
                    subgroup_priority = None,
                    intra_subgroup_priority = data.read_uint8(),
                    count = data.read_bits(8),
                ) for i in range(data.read_bits(8))],
            add_unit_tags = [data.read_uint32() for i in range(data.read_bits(8))],
        )

    def control_group_update_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            control_group_update = data.read_bits(2),
            remove_mask = ('None',None),
        )

    def selection_sync_check_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            selection_sync_data = dict(
                count = data.read_bits(8),
                subgroup_count = data.read_bits(8),
                active_subgroup_index = data.read_bits(8),
                unit_tags_checksum = data.read_uint32(),
                subgroup_indices_checksum = data.read_uint32(),
                subgroups_checksum = data.read_uint32(),
            )
        )

    def resource_trade_event(self, data):
        return dict(
            recipient_id = data.read_bits(4),
            resources = [data.read_uint32()-2147483648 for i in range(data.read_bits(3))],
        )

    def trigger_chat_message_event(self, data):
        return dict(
            message = data.read_aligned_bytes(data.read_bits(10)),
        )

    def ai_communicate_event(self, data):
        return dict(
            beacon = data.read_uint8()-128,
            ally = data.read_uint8()-128,
            flags = data.read_uint8()-128,
            build = data.read_uint8()-128,
            target_unit_tag = data.read_uint32(),
            target_unit_link = data.read_uint16(),
            target_upkeep_player_id = data.read_uint8()-128,
            target_control_player_id = data.read_uint8()-128,
            target_point = dict(
                    x = data.read_uint32()-2147483648,
                    y = data.read_uint32()-2147483648,
                    z = data.read_uint32()-2147483648,
                ),
        )

    def set_absolute_game_speed_event(self, data):
        return dict(
            speed = data.read_bits(3),
        )

    def add_absolute_game_speed_event(self, data):
        return dict(
            delta = data.read_uint8()-128,
        )

    def trigger_ping_event(self, data):
        return dict(
            point = dict(
                    x = data.read_uint32()-2147483648,
                    y = data.read_uint32()-2147483648,
                ),
            unit_tag = data.read_uint32(),
            pinged_minimap = data.read_bool(),
        )

    def broadcast_cheat_event(self, data):
        return dict(
            verb = data.read_aligned_bytes(data.read_bits(10)),
            arguments = data.read_aligned_bytes(data.read_bits(10)),
        )

    def alliance_event(self, data):
        return dict(
            alliance = data.read_uint32(),
            control = data.read_uint32(),
        )

    def unit_click_event(self, data):
        return dict(
            unit_tag = data.read_uint32(),
        )

    def unit_highlight_event(self, data):
        return dict(
            unit_tag = data.read_uint32(),
            flags = data.read_uint8(),
        )

    def trigger_reply_selected_event(self, data):
        return dict(
            conversation_id = data.read_uint32()-2147483648,
            reply_id = data.read_uint32()-2147483648,
        )

    def trigger_skipped_event(self, data):
        return None

    def trigger_sound_length_query_event(self, data):
        return dict(
            sound_hash = data.read_uint32(),
            length = data.read_uint32(),
        )

    def trigger_sound_offset_event(self, data):
        return dict(
            sound = data.read_uint32(),
        )

    def trigger_transmission_offset_event(self, data):
        return dict(
            transmission_id = data.read_uint32()-2147483648,
        )

    def trigger_transmission_complete_event(self, data):
        return dict(
            transmission_id = data.read_uint32()-2147483648,
        )

    def camera_update_event(self, data):
        return dict(
            target = dict(
                    x = data.read_uint16(),
                    y = data.read_uint16(),
                ),
            distance = data.read_uint16() if data.read_bool() else None,
            pitch = data.read_uint16() if data.read_bool() else None,
            yaw = data.read_uint16() if data.read_bool() else None,
        )

    def trigger_abort_mission_event(self, data):
        return None

    def trigger_purchase_made_event(self, data):
        return dict(
            purchase_item_id = data.read_uint32()-2147483648,
        )

    def trigger_purchase_exit_event(self, data):
        return None

    def trigger_planet_mission_launched_event(self, data):
        return dict(
            difficulty_level = data.read_uint32()-2147483648,
        )

    def trigger_planet_panel_canceled_event(self, data):
        return None

    def trigger_dialog_control_event(self, data):
        return dict(
            control_id = data.read_uint32()-2147483648,
            event_type = data.read_uint32()-2147483648,
            event_data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Checked', data.read_bool()),
                    2: lambda: ('ValueChanged', data.read_uint32()),
                    3: lambda: ('SelectionChanged', data.read_uint32()-2147483648),
                    4: lambda: ('TextChanged', data.read_aligned_bytes(data.read_bits(11))),
                }[data.read_bits(3)](),
        )

    def trigger_sound_length_sync_event(self, data):
        return dict(
            sync_info = dict(
                sound_hash = [data.read_uint32() for i in range(data.read_bits(8))],
                length = [data.read_uint32() for i in range(data.read_bits(8))],
            )
        )

    def trigger_conversation_skipped_event(self, data):
        return dict(
            skip_type = data.read_int(1),
        )

    def trigger_mouse_clicked_event(self, data):
        return dict(
            button = data.read_uint32(),
            down = data.read_bool(),
            position_ui = dict(
                    x = data.read_bits(11),
                    y = data.read_bits(11),
                ),
            position_world = dict(
                    x = data.read_bits(20),
                    y = data.read_bits(20),
                    z = data.read_uint32()-2147483648,
                ),
        )

    def trigger_mouse_moved_event(self, data):
        return dict(
            position_ui = dict(
                    x = data.read_bits(11),
                    y = data.read_bits(11),
                ),
            position_world = dict(
                    x = data.read_bits(20),
                    y = data.read_bits(20),
                    z = data.read_uint32()-2147483648,
                ),
        )

    def achievement_awarded_event(self, data):
        return dict(
            achievement_link = data.read_uint16(),
        )

    def trigger_planet_panel_replay_event(self, data):
        return None

    def trigger_soundtrack_done_event(self, data):
        return dict(
            soundtrack = data.read_uint32(),
        )

    def trigger_planet_mission_selected_event(self, data):
        return dict(
            planet_id = data.read_uint32()-2147483648,
        )

    def trigger_key_pressed_event(self, data):
        return dict(
            key = data.read_uint8()-128,
            flags = data.read_uint8()-128,
        )

    def trigger_movie_function_event(self, data):
        return dict(
            function_name = data.read_aligned_bytes(data.read_bits(7)),
        )

    def trigger_planet_panel_birth_complete_event(self, data):
        return None

    def trigger_planet_panel_death_complete_event(self, data):
        return None

    def resource_request_event(self, data):
        return dict(
            resources = [data.read_uint32()-2147483648 for i in range(data.read_bits(3))],
        )

    def resource_request_fulfill_event(self, data):
        return dict(
            request_id = data.read_uint32()-2147483648,
        )

    def resource_request_cancel_event(self, data):
        return dict(
            request_id = data.read_uint32()-2147483648,
        )

    def trigger_research_panel_exit_event(self, data):
        return None

    def trigger_research_panel_purchase_event(self, data):
        return None

    def trigger_research_panel_selection_changed_event(self, data):
        return dict(
            item_id = data.read_uint32()-2147483648,
        )

    def lag_message_event(self, data):
        return dict(
            player_id = data.read_bits(4),
        )

    def trigger_mercenary_panel_exit_event(self, data):
        return None

    def trigger_mercenary_panel_purchase_event(self, data):
        return None

    def trigger_mercenary_panel_selection_changed_event(self, data):
        return dict(
            item_id = data.read_uint32()-2147483648,
        )

    def trigger_victory_panel_exit_event(self, data):
        return None

    def trigger_battle_report_panel_exit_event(self, data):
        return None

    def trigger_battle_report_panel_play_mission_event(self, data):
        return dict(
            battle_report_id = data.read_uint32()-2147483648,
            difficulty_level = data.read_uint32()-2147483648,
        )

    def trigger_battle_report_panel_play_scene_event(self, data):
        return dict(
            battle_report_id = data.read_uint32()-2147483648,
        )

    def trigger_battle_report_panel_selection_changed_event(self, data):
        return dict(
            battle_report_id = data.read_uint32()-2147483648,
        )

    def trigger_victory_panel_play_mission_again_event(self, data):
        return dict(
            difficulty_level = data.read_uint32()-2147483648,
        )

    def trigger_movie_started_event(self, data):
        return None

    def trigger_movie_finished_event(self, data):
        return None

    def decrement_game_time_remaining_event(self, data):
        return dict(
            decrement_ms = data.read_bits(19)
        )

    def trigger_portrait_loaded_event(self, data):
        return dict(
            portrait_id = data.read_uint32()-2147483648,
        )

    def trigger_custom_dialog_dismissed_event(self, data):
        return dict(
            result = data.read_uint32()-2147483648,
        )

    def trigger_game_menu_item_selected_event(self, data):
        return dict(
            game_menu_item_index = data.read_uint32()-2147483648,
        )

    def trigger_camera_move_event(self, data):
        return dict(
            reason = data.read_uint8()-128,
        )

    def trigger_purchase_panel_selected_purchase_item_changed_event(self, data):
        return dict(
            item_id = data.read_uint32()-2147483648,
        )

    def trigger_purchase_panel_selected_purchase_category_changed_event(self, data):
        return dict(
            category_id = data.read_uint32()-2147483648,
        )

    def trigger_button_pressed_event(self, data):
        return dict(
            button = data.read_uint16(),
        )

    def trigger_game_credits_finished_event(self, data):
        return None

    def trigger_cutscene_bookmark_fired_event(self, data):
        return dict(
            cutscene_id = data.read_uint32()-2147483648,
            bookmark_name = data.read_aligned_bytes(data.read_bits(7)),
        )

    def trigger_cutscene_end_scene_fired_event(self, data):
        return dict(
            cutscene_id = data.read_uint32()-2147483648,
        )

    def trigger_cutscene_conversation_line_event(self, data):
        return dict(
            cutscene_id = data.read_uint32()-2147483648,
            conversation_line = data.read_aligned_bytes(data.read_bits(7)),
            alt_conversation_line = data.read_aligned_bytes(data.read_bits(7)),
        )

    def trigger_cutscene_conversation_line_missing_event(self, data):
        return dict(
            cutscene_id = data.read_uint32()-2147483648,
            conversation_line = data.read_aligned_bytes(data.read_bits(7)),
        )


class GameEventsReader_16561(GameEventsReader_16117):

    def command_event(self, data):
        return dict(
            flags = data.read_bits(17),
            ability = dict(
                    ability_link = data.read_uint16(),
                    ability_command_index = data.read_bits(5),
                    ability_command_data = data.read_uint8() if data.read_bool() else None,
                ) if data.read_bool() else None,
            data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('TargetPoint', dict(
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            )
                        )),
                    2: lambda: ('TargetUnit', dict(
                            flags = data.read_uint8(),
                            timer = data.read_uint8(),
                            unit_tag = data.read_uint32(),
                            unit_link = data.read_uint16(),
                            control_player_id = None,
                            upkeep_player_id = data.read_bits(4) if data.read_bool() else None,
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            ),
                        )),
                    3: lambda: ('Data',dict(data=data.read_uint32())),
                }[data.read_bits(2)](),
            other_unit_tag = data.read_uint32() if data.read_bool() else None
        )

    def selection_delta_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            subgroup_index = data.read_bits(8),
            remove_mask = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Mask', self.read_selection_bitmask(data, data.read_bits(8))),
                    2: lambda: ('OneIndices', [data.read_bits(8) for i in range(data.read_bits(8))]),
                    3: lambda: ('ZeroIndices', [data.read_bits(8) for i in range(data.read_bits(8))]),
                }[data.read_bits(2)](),
            add_subgroups = [dict(
                    unit_link = data.read_uint16(),
                    subgroup_priority = None,
                    intra_subgroup_priority = data.read_uint8(),
                    count = data.read_bits(8),
                ) for i in range(data.read_bits(8))],
            add_unit_tags = [data.read_uint32() for i in range(data.read_bits(8))],
        )

    def control_group_update_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            control_group_update = data.read_bits(2),
            remove_mask = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Mask', self.read_selection_bitmask(data, data.read_bits(8))),
                    2: lambda: ('OneIndices', [data.read_bits(8) for i in range(data.read_bits(8))]),
                    3: lambda: ('ZeroIndices', [data.read_bits(8) for i in range(data.read_bits(8))]),
                }[data.read_bits(2)](),
        )

class GameEventsReader_18574(GameEventsReader_16561):

    def bank_signature_event(self, data):
        return dict(
            signature=[data.read_uint8() for i in range(data.read_bits(5))],
            toon_handle = None,
        )

    def command_event(self, data):
        return dict(
            flags = data.read_bits(18),
            ability = dict(
                    ability_link = data.read_uint16(),
                    ability_command_index = data.read_bits(5),
                    ability_command_data = data.read_uint8() if data.read_bool() else None,
                ) if data.read_bool() else None,
            data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('TargetPoint', dict(
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            )
                        )),
                    2: lambda: ('TargetUnit', dict(
                            flags = data.read_uint8(),
                            timer = data.read_uint8(),
                            unit_tag = data.read_uint32(),
                            unit_link = data.read_uint16(),
                            control_player_id = None,
                            upkeep_player_id = data.read_bits(4) if data.read_bool() else None,
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            ),
                        )),
                    3: lambda: ('Data',dict(data=data.read_uint32())),
                }[data.read_bits(2)](),
            other_unit_tag = data.read_uint32() if data.read_bool() else None
        )


class GameEventsReader_19595(GameEventsReader_18574):

    def command_event(self, data):
        return dict(
            flags = data.read_bits(18),
            ability = dict(
                    ability_link = data.read_uint16(),
                    ability_command_index = data.read_bits(5),
                    ability_command_data = data.read_uint8() if data.read_bool() else None,
                ) if data.read_bool() else None,
            data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('TargetPoint', dict(
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            )
                        )),
                    2: lambda: ('TargetUnit', dict(
                            flags = data.read_uint8(),
                            timer = data.read_uint8(),
                            unit_tag = data.read_uint32(),
                            unit_link = data.read_uint16(),
                            control_player_id = data.read_bits(4) if data.read_bool() else None,
                            upkeep_player_id = data.read_bits(4) if data.read_bool() else None,
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            ),
                        )),
                    3: lambda: ('Data',dict(data=data.read_uint32())),
                }[data.read_bits(2)](),
            other_unit_tag = data.read_uint32() if data.read_bool() else None
        )

    def trigger_transmission_offset_event(self, data):
        # I'm not actually sure when this second int is introduced..
        return dict(
            transmission_id = data.read_uint32()-2147483648,
            thread = data.read_uint32(),
        )

class GameEventsReader_22612(GameEventsReader_19595):

    def user_options_event(self, data):
        return dict(
            game_fully_downloaded = data.read_bool(),
            development_cheats_enabled = data.read_bool(),
            multiplayer_cheats_enabled = data.read_bool(),
            sync_checksumming_enabled = data.read_bool(),
            is_map_to_map_transition = data.read_bool(),
            use_ai_beacons = data.read_bool(),
            base_build_num = None,
            starting_rally = None,
        )

    def command_event(self, data):
        return dict(
            flags = data.read_bits(20),
            ability = dict(
                    ability_link = data.read_uint16(),
                    ability_command_index = data.read_bits(5),
                    ability_command_data = data.read_uint8() if data.read_bool() else None,
                ) if data.read_bool() else None,
            data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('TargetPoint', dict(
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            )
                        )),
                    2: lambda: ('TargetUnit', dict(
                            flags = data.read_uint8(),
                            timer = data.read_uint8(),
                            unit_tag = data.read_uint32(),
                            unit_link = data.read_uint16(),
                            control_player_id = data.read_bits(4) if data.read_bool() else None,
                            upkeep_player_id = data.read_bits(4) if data.read_bool() else None,
                            point = dict(
                                x = data.read_bits(20),
                                y = data.read_bits(20),
                                z = data.read_uint32()-2147483648,
                            ),
                        )),
                    3: lambda: ('Data',dict(data=data.read_uint32())),
                }[data.read_bits(2)](),
            other_unit_tag = data.read_uint32() if data.read_bool() else None
        )

    def selection_delta_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            subgroup_index = data.read_bits(9),
            remove_mask = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Mask', self.read_selection_bitmask(data, data.read_bits(9))),
                    2: lambda: ('OneIndices', [data.read_bits(9) for i in range(data.read_bits(9))]),
                    3: lambda: ('ZeroIndices', [data.read_bits(9) for i in range(data.read_bits(9))]),
                }[data.read_bits(2)](),
            add_subgroups = [dict(
                    unit_link = data.read_uint16(),
                    subgroup_priority = None,
                    intra_subgroup_priority = data.read_uint8(),
                    count = data.read_bits(9),
                ) for i in range(data.read_bits(9))],
            add_unit_tags = [data.read_uint32() for i in range(data.read_bits(9))],
        )

    def control_group_update_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            control_group_update = data.read_bits(2),
            remove_mask = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Mask', self.read_selection_bitmask(data, data.read_bits(9))),
                    2: lambda: ('OneIndices', [data.read_bits(9) for i in range(data.read_bits(9))]),
                    3: lambda: ('ZeroIndices', [data.read_bits(9) for i in range(data.read_bits(9))]),
                }[data.read_bits(2)](),
        )

    def selection_sync_check_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            selection_sync_data = dict(
                count = data.read_bits(9),
                subgroup_count = data.read_bits(9),
                active_subgroup_index = data.read_bits(9),
                unit_tags_checksum = data.read_uint32(),
                subgroup_indices_checksum = data.read_uint32(),
                subgroups_checksum = data.read_uint32(),
            )
        )


class GameEventsReader_HotS_Beta(GameEventsReader_22612):

    def user_options_event(self, data):
        return dict(
            game_fully_downloaded = data.read_bool(),
            development_cheats_enabled = data.read_bool(),
            multiplayer_cheats_enabled = data.read_bool(),
            sync_checksumming_enabled = data.read_bool(),
            is_map_to_map_transition = data.read_bool(),
            starting_rally = data.read_bool(),
            base_build_num = data.read_uint32(),
            use_ai_beacons = None,
        )

    def selection_delta_event(self, data):
        return dict(
            control_group_index = data.read_bits(4),
            subgroup_index = data.read_bits(9),
            remove_mask = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Mask', self.read_selection_bitmask(data, data.read_bits(9))),
                    2: lambda: ('OneIndices', [data.read_bits(9) for i in range(data.read_bits(9))]),
                    3: lambda: ('ZeroIndices', [data.read_bits(9) for i in range(data.read_bits(9))]),
                }[data.read_bits(2)](),
            add_subgroups = [dict(
                    unit_link = data.read_uint16(),
                    subgroup_priority = data.read_uint8(),
                    intra_subgroup_priority = data.read_uint8(),
                    count = data.read_bits(9),
                ) for i in range(data.read_bits(9))],
            add_unit_tags = [data.read_uint32() for i in range(data.read_bits(9))],
        )

    def camera_update_event(self, data):
        return dict(
            target = dict(
                    x = data.read_uint16(),
                    y = data.read_uint16(),
                ) if data.read_bool() else None,
            distance = data.read_uint16() if data.read_bool() else None,
            pitch = data.read_uint16() if data.read_bool() else None,
            yaw = data.read_uint16() if data.read_bool() else None,
        )

    def trigger_sound_length_sync_event(self, data):
        return dict(
            sync_info = dict(
                sound_hash = [data.read_uint32() for i in range(data.read_bits(7))],
                length = [data.read_uint32() for i in range(data.read_bits(7))],
            )
        )

    def trigger_dialog_control_event(self, data):
        return dict(
            control_id = data.read_uint32()-2147483648,
            event_type = data.read_uint32()-2147483648,
            event_data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Checked', data.read_bool()),
                    2: lambda: ('ValueChanged', data.read_uint32()),
                    3: lambda: ('SelectionChanged', data.read_uint32()-2147483648),
                    4: lambda: ('TextChanged', data.read_aligned_bytes(data.read_bits(11))),
                    5: lambda: ('MouseButton', data.read_uint32())
                }[data.read_bits(3)](),
        )

class GameEventsReader_HotS(GameEventsReader_HotS_Beta):

    def __init__(self):
        super(GameEventsReader_HotS, self).__init__()

        self.EVENT_DISPATCH.update({
            7: (UserOptionsEvent, self.user_options_event),     #Override
            9: (None, self.bank_file_event),                    #Override
            10: (None, self.bank_section_event),                #Override
            11: (None, self.bank_key_event),                    #Override
            12: (None, self.bank_value_event),                  #Override
            13: (None, self.bank_signature_event),              #New
            14: (None, self.camera_save_event),                 #New
            21: (None, self.save_game_event),                   #New
            22: (None, self.save_game_done_event),              #Override
            23: (None, self.load_game_done_event),              #Override
            43: (None, self.hijack_replay_game_event),          #New
            62: (None, self.trigger_target_mode_update_event),  #New
            101: (PlayerLeaveEvent, self.game_user_leave_event),#New
            102: (None, self.game_user_join_event),             #New
        })
        del self.EVENT_DISPATCH[8]
        del self.EVENT_DISPATCH[25]
        del self.EVENT_DISPATCH[76]

    def bank_signature_event(self, data):
        return dict(
            signature = [data.read_uint8() for i in range(data.read_bits(5))],
            toon_handle = data.read_aligned_bytes(data.read_bits(7))
        )

    def camera_save_event(self, data):
        return dict(
            which = data.read_bits(3),
            target = dict(
                x = data.read_uint16(),
                y = data.read_uint16(),
            )
        )

    def load_game_done_event(self, data):
        return None

    def hijack_replay_game_event(self, data):
        return dict(
            user_infos = [dict(
                    game_unit_id = data.read_bits(4),
                    observe = data.read_bits(2),
                    name = data.read_aligned_bytes(data.read_uint8()),
                    toon_handle = data.read_aligned_bytes(data.read_bits(7)) if data.read_bool() else None,
                    clan_tag = data.read_aligned_bytes(data.read_uint8()) if data.read_bool() else None,
                ) for i in range(data.read_bits(5))],
            method = data.read_bits(1),
        )

    def trigger_dialog_control_event(self, data):
        return dict(
            control_id = data.read_uint32()-2147483648,
            event_type = data.read_uint32()-2147483648,
            event_data = { #Choice
                    0: lambda: ('None', None),
                    1: lambda: ('Checked', data.read_bool()),
                    2: lambda: ('ValueChanged', data.read_uint32()),
                    3: lambda: ('SelectionChanged', data.read_uint32()-2147483648),
                    4: lambda: ('TextChanged', data.read_aligned_bytes(data.read_bits(11))),
                    5: lambda: ('MouseButton', data.read_uint32())
                }[data.read_bits(3)](),
        )

    def trigger_target_mode_update_event(self, data):
        return dict(
            ability_link = data.read_uint16(),
            ability_command_index = data.read_bits(5),
            state = data.read_uint8()-128,
        )

    def game_user_leave_event(self, data):
        return None

    def game_user_join_event(self, data):
        return dict(
            observe = data.read_bits(2),
            name = data.read_aligned_bytes(data.read_bits(8)),
            toon_handle = data.read_aligned_bytes(data.read_bits(7)) if data.read_bool() else None,
            clan_tag = data.read_aligned_bytes(data.read_uint8()) if data.read_bool() else None,
        )


class TrackerEventsReader_Base(Reader):

    def __init__(self):
        self.EVENT_DISPATCH = {
            0: PlayerStatsEvent,
            1: UnitBornEvent,
            2: UnitDiedEvent,
            3: UnitOwnerChangeEvent,
            4: UnitTypeChangeEvent,
            5: UpgradeCompleteEvent,
            6: UnitInitEvent,
            7: UnitDoneEvent,
            8: UnitPositionsEvent,
        }

    def __call__(self, data, replay):
        decoder = BitPackedDecoder(data)

        frames = 0
        events = list()
        while not decoder.done():
            frames += decoder.read_struct()
            etype = decoder.read_struct()
            event_data = decoder.read_struct()
            event = self.EVENT_DISPATCH[etype](frames, event_data)
            events.append(event)

        return events

