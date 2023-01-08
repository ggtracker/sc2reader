#!/usr/bin/env python

import sc2reader
from sc2reader.factories.plugins.replay import toJSON


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prints replay data to a json string.")
    parser.add_argument(
        "--indent",
        "-i",
        type=int,
        default=None,
        help="The per-line indent to use when printing a human readable json string",
    )
    parser.add_argument(
        "path",
        metavar="path",
        type=str,
        nargs=1,
        help="Path to the replay to serialize.",
    )
    args = parser.parse_args()

    factory = sc2reader.factories.SC2Factory()
    try:
        factory.register_plugin(
            "Replay", toJSON(indent=args.indent)
        )
    except TypeError:
        factory.register_plugin("Replay", toJSON(indent=args.indent))
    replay_json = factory.load_replay(args.path[0])
    print(replay_json)


if __name__ == "__main__":
    main()
