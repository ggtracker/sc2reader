#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

import sc2reader
from sc2reader.utils import get_files
from sc2reader.exceptions import ReadError

def doFile(filename, arguments):
    '''Prints summary information about SC2 replay file'''
    try:
        replay = sc2reader.read_file(filename, debug=True)
    except ReadError as e:
        prev = e.game_events[-1]
        print "\nVersion {0} replay:\n\t{1}".format(e.replay.release_string, e.replay.filename)
        print "\t{0}, Type={1:X}, Code={2:X}".format(e.msg, e.type,e.code)
        print "\tPrevious Event: {0}".format(prev.name)
        print "\t\t"+prev.bytes.encode('hex')
        print "\tFollowing Bytes:"
        print "\t\t"+e.buffer.read_range(e.location,e.location+30).encode('hex')
        print "Error with '{0}': ".format(filename)
        print e
        return
    except TypeError as e:
        print "Error with '%s': " % filename,
        print e
        return
    except ValueError as e:
        print "Error with '%s': " % filename,
        print e
        return

    if arguments.map:
        print "   Map:      {0}".format(replay.map)
    if arguments.length:
        print "   Length:   {0}".format(replay.length)
    if arguments.date:
        print "   Date:     {0}".format(replay.date)
    if arguments.teams:
        races = list()
        for team in replay.teams:
            races.append(''.join([player.pick_race[0] for player in team.players]))
        print "   Teams:    {0}".format("v".join(races))

        for team in replay.teams:
            print "      Team {0}\t{1} ({2})".format(team.number,team.players[0].name,team.players[0].pick_race[0])
            for player in team.players[1:]:
                print "              \t{0} ({1})".format(player.name,player.pick_race[0])
    if arguments.messages:
        print "   Messages:"
        for message in replay.messages:
            print "   {0}".format(message)
    if arguments.version:
        print "   Version:  {0}".format(replay.release_string)

    print

def main():
    parser = argparse.ArgumentParser(description='Prints basic information from SC2 replay files or directories.')
    parser.add_argument('paths', metavar='filename', type=str, nargs='+',
                        help="Paths to one or more SC2Replay files or directories")
    parser.add_argument('--date', action="store_true", default=True,
                      help="Print game date")
    parser.add_argument('--length', action="store_true", default=False,
                      help="Print game duration mm:ss in game time (not real time)")
    parser.add_argument('--map', action="store_true", default=True,
                      help="Print map name")
    parser.add_argument('--messages', action="store_true", default=False,
                      help="Print in-game player chat messages")
    parser.add_argument('--teams', action="store_true", default=True,
                      help="Print teams, their players, and the race matchup")
    parser.add_argument('--version', action="store_true", default=True,
                      help="Print the release string as seen in game")
    parser.add_argument('--recursive', action="store_true", default=True,
                      help="Recursively read through directories of replays")

    arguments = parser.parse_args()

    for path in arguments.paths:
        if arguments.recursive:
            files = get_files(path)
        else:
            files = get_files(path, depth=0)

        for file in files:
            print "\n--------------------------------------\n{0}\n".format(file)
            doFile(file, arguments)

if __name__ == '__main__':
    main()
