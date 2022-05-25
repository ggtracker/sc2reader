#!/usr/bin/env python

import os
import argparse

import sc2reader
from sc2reader import utils
from sc2reader.exceptions import ReadError


def printReplay(filepath, arguments):
    """Prints summary information about SC2 replay file"""
    try:
        replay = sc2reader.load_replay(filepath, debug=True)

        if arguments.map:
            print(f"   Map:      {replay.map_name}")
        if arguments.length:
            print(f"   Length:   {replay.game_length} minutes")
        if arguments.date:
            print(f"   Date:     {replay.start_time}")
        if arguments.teams:
            lineups = [team.lineup for team in replay.teams]
            print("   Teams:    {}".format("v".join(lineups)))
            for team in replay.teams:
                print(
                    "      Team {}\t{} ({})".format(
                        team.number, team.players[0].name, team.players[0].pick_race[0]
                    )
                )
                for player in team.players[1:]:
                    print(
                        "              \t{} ({})".format(
                            player.name, player.pick_race[0]
                        )
                    )
        if arguments.observers:
            print("   Observers:")
            for observer in replay.observers:
                print(f"      {observer.name}")

        if arguments.messages:
            print("   Messages:")
            for message in replay.messages:
                print(f"   {message}")
        if arguments.version:
            print(f"   Version:  {replay.release_string}")

        print
    except ReadError as e:
        raise
        return
        prev = e.game_events[-1]
        print(
            "\nVersion {} replay:\n\t{}".format(
                e.replay.release_string, e.replay.filepath
            )
        )
        print(f"\t{e.msg}, Type={e.type:X}")
        print(f"\tPrevious Event: {prev.name}")
        print("\t\t" + prev.bytes.encode("hex"))
        print("\tFollowing Bytes:")
        print("\t\t" + e.buffer.read_range(e.location, e.location + 30).encode("hex"))
        print(f"Error with '{filepath}': ")
        print(e)
    except Exception as e:
        print(f"Error with '{filepath}': ")
        print(e)
        raise


def printGameSummary(filepath, arguments):
    summary = sc2reader.load_game_summary(filepath)

    if arguments.map:
        print(f"   Map:      {summary.map_name}")
    if arguments.length:
        print(f"   Length:   {summary.game_length} minutes")
    if arguments.date:
        print(f"   Date:     {summary.start_time}")
    if arguments.teams:
        lineups = [team.lineup for team in summary.teams]
        print("   Teams:    {}".format("v".join(lineups)))
        for team in summary.teams:
            print(f"      Team {team.number}\t{team.players[0]}")
            for player in team.players[1:]:
                print(f"              \t{player}")
    if arguments.builds:
        for player in summary.players:
            print(f"\n== {player} ==\n")
            for order in summary.build_orders[player.pid]:
                msg = "  {0:0>2}:{1:0>2}  {2:<35} {3:0>2}/{4}"
                print(
                    msg.format(
                        order.time / 60,
                        order.time % 60,
                        order.order,
                        order.supply,
                        order.total_supply,
                    )
                )
        print("")


def main():
    parser = argparse.ArgumentParser(
        description="""Prints basic information from Starcraft II replay and
        game summary files or directories."""
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recursively read through directories of Starcraft II files [default on]",
    )

    required = parser.add_argument_group("Required Arguments")
    required.add_argument(
        "paths",
        metavar="filename",
        type=str,
        nargs="+",
        help="Paths to one or more Starcraft II files or directories",
    )

    shared_args = parser.add_argument_group("Shared Arguments")
    shared_args.add_argument(
        "--date", action="store_true", default=True, help="print game date [default on]"
    )
    shared_args.add_argument(
        "--length",
        action="store_true",
        default=False,
        help="print game duration mm:ss in game time (not real time) [default off]",
    )
    shared_args.add_argument(
        "--map", action="store_true", default=True, help="print map name [default on]"
    )
    shared_args.add_argument(
        "--teams",
        action="store_true",
        default=True,
        help="print teams, their players, and the race matchup [default on]",
    )
    shared_args.add_argument(
        "--observers", action="store_true", default=True, help="print observers"
    )

    replay_args = parser.add_argument_group("Replay Options")
    replay_args.add_argument(
        "--messages",
        action="store_true",
        default=False,
        help="print(in-game player chat messages [default off]",
    )
    replay_args.add_argument(
        "--version",
        action="store_true",
        default=True,
        help="print(the release string as seen in game [default on]",
    )

    s2gs_args = parser.add_argument_group("Game Summary Options")
    s2gs_args.add_argument(
        "--builds",
        action="store_true",
        default=False,
        help="print(player build orders (first 64 items) [default off]",
    )

    arguments = parser.parse_args()
    for path in arguments.paths:
        depth = -1 if arguments.recursive else 0
        for filepath in utils.get_files(path, depth=depth):
            name, ext = os.path.splitext(filepath)
            if ext.lower() == ".sc2replay":
                print(
                    f"\n--------------------------------------\n{filepath}\n"
                )
                printReplay(filepath, arguments)
            elif ext.lower() == ".s2gs":
                print(
                    f"\n--------------------------------------\n{filepath}\n"
                )
                printGameSummary(filepath, arguments)


if __name__ == "__main__":
    main()
