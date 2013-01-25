#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script is intended for use debugging parse issues on replays.

    sc2parse [FILES..]

Recursively parses all the files. When exceptions are thrown it catches them
and attempts to print out any information that might be needed for debug. If
information you need isn't available feel free to add new handlers or add to
existing exception handlers.

Also sets logging to INFO so that missing unit type and ability type messages
are caught and reported. At some point these things should be moved to WARN.

If there are parse exceptions, this script should be run to generate an info
for the ticket filed.
"""

import sys
import sc2reader
import traceback

sc2reader.log_utils.log_to_console('INFO')

def main():
    for argument in sys.argv[1:]:
        for path in sc2reader.utils.get_files(argument,extension='SC2Replay'):
            try:
                replay = sc2reader.load_replay(path, debug=True, verbose=True)
            except sc2reader.exceptions.ReadError as e:
                print
                print path
                print '{build} - {real_type} on {map_name} - Played {start_time}'.format(**e.replay.__dict__)
                print '[ERROR]', e.message
                for event in e.game_events[-5:]:
                    print '{0} - {1}'.format(hex(event.type),event.bytes.encode('hex'))
                e.buffer.seek(e.location)
                print e.buffer.peek(50).encode('hex')
                print
            except Exception as e:
                print
                print path
                replay = sc2reader.load_replay(path, debug=True, load_level=1)
                print '{build} - {real_type} on {map_name} - Played {start_time}'.format(**replay.__dict__)
                print '[ERROR]', e.message
                for pid, attributes in replay.attributes.items():
                    print pid, attributes
                for pid, info in enumerate(replay.raw_data['replay.details'].players):
                    print pid, info
                print replay.raw_data['replay.initData'].player_names
                traceback.print_exc()
                print


if __name__ == '__main__':
    main()