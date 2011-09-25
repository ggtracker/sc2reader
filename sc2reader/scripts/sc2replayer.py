#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
import termios
import fcntl

import sc2reader
from sc2reader.objects import *

def myGetch():
    fd = sys.stdin.fileno()
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    try:
        while 1:
            try:
                c = sys.stdin.read(1)
                break
            except IOError: pass
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="""Step by step replay of game events; shows only the
        Initialization, Ability, and Selection events by default. Press any
        key to advance through the events in sequential order.""",
        epilog="And that's all folks")

    parser.add_argument('FILE',type=str,
        help="The file you would like to replay")
    parser.add_argument('--player',default=0, type=int,
        help="The number of the player you would like to watch. Defaults to 0 (All).")
    parser.add_argument('--bytes',default=False,action="store_true",
        help="Displays the byte code of the event in hex after each event.")
    parser.add_argument('--hotkeys',default=False,action="store_true",
        help="Shows the hotkey events in the event stream.")
    parser.add_argument('--cameras',default=False,action="store_true",
        help="Shows the camera events in the event stream.")

    return parser.parse_args()

def main():
    args = get_args()
    replay = sc2reader.read_file(args.FILE,debug=True)
    print "Release {0}".format(replay.release_string)
    print "{0} on {1}".format(replay.type,replay.map)
    for player in replay.players:
        print player
    print "\n--------------------------\n\n"

    # Allow picking of the player to 'watch'
    if args.player:
        events = replay.player[args.player].events
    else:
        events = replay.events

    # Loop through the events
    data = sc2reader.config.build_data[replay.build]
    for event in events:
        # Use their options to filter the event stream
        if isinstance(event,AbilityEvent) or\
                   isinstance(event,SelectionEvent) or\
                   isinstance(event,PlayerJoinEvent) or\
                   isinstance(event, PlayerLeaveEvent) or\
                   isinstance(event,GameStartEvent) or\
                   (args.hotkeys and isinstance(event,HotkeyEvent)) or\
                   (args.cameras and isinstance(event,CameraEvent)):

            event.apply(data)
            print event
            if args.bytes:
                print "\t"+event.bytes.encode('hex')
                
            if re.search('UNKNOWN|ERROR', str(event)):
                myGetch()


if __name__ == '__main__':
    main()
