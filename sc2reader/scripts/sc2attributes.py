# -*- coding: utf-8 -*-
#
# Recursively searches for s2gs files in specified paths. Adds
# new attributes and values and allows the user to choose when
# conflicts are detected.
#
# Usage: sc2attributes PATH...
#
# Cannot be run from an egg installation because attributes.json
# must be writable. Install from source when you want to use this.
#
# ----------------------------------------------------------------
#
# The file has the following structure:
#
#   sc2reader/data/attributes.json - {
#       "attributes": { json object },
#       "decisions": "pickled python object",
#   }
#
# Why we need to track decisions:
#
# Sometimes the attribute names or values can change over time
# or have values we don't like. When the script detects conflicts
# between the s2gs names and the existing attribute names it
# notifies the user and asks for a decision. In order to save the
# user from making the same decisions over and over again we save
# those decisions. The decisions are pickled instead of in json
# because the data structure is too complex for the json format.
#
from __future__ import absolute_import, print_function, unicode_literals, division

import argparse
import json
import os
import pickle
import traceback

import sc2reader

try:
    raw_input  # Python 2
except NameError:
    raw_input = input  # Python 3

decisions = dict()


def main():
    global decisions

    parser = argparse.ArgumentParser(
        description="Recursively parses replay files, intended for debugging parse issues."
    )
    parser.add_argument(
        "folders", metavar="folder", type=str, nargs="+", help="Path to a folder"
    )
    args = parser.parse_args()

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(
        os.path.join(scripts_dir, "..", "data", "attributes.json")
    )

    attributes = dict()
    if os.path.exists(data_path):
        with open(data_path, "r") as data_file:
            data = json.load(data_file)
            attributes = data.get("attributes", attributes)
            decisions = pickle.loads(data.get("decisions", "(dp0\n."))

    for folder in args.folders:
        for path in sc2reader.utils.get_files(folder, extension="s2gs"):
            try:
                summary = sc2reader.load_game_summary(path)
                for prop in summary.parts[0][5]:
                    group_key = prop[0][1]
                    group_name = summary.translations["enUS"][group_key]
                    attribute_values = dict()
                    if str(group_key) in attributes:
                        attribute_name, attribute_values = attributes[str(group_key)]
                        if attribute_name != group_name:
                            group_name = get_choice(
                                group_key, attribute_name, group_name
                            )

                    for value in prop[1]:
                        value_key = value[0].strip("\x00 ").replace(" v ", "v")
                        value_name = summary.lang_sheets["enUS"][value[1][0][1]][
                            value[1][0][2]
                        ]
                        if str(value_key) in attribute_values:
                            attribute_value_name = attribute_values[str(value_key)]
                            if value_name != attribute_value_name:
                                value_name = get_choice(
                                    (group_key, value_key),
                                    attribute_value_name,
                                    value_name,
                                )

                        attribute_values[str(value_key)] = value_name

                    attributes["{0:0>4}".format(group_key)] = (
                        group_name,
                        attribute_values,
                    )
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    raise
                else:
                    traceback.print_exc()

    with open(data_path, "w") as data_file:
        data = dict(attributes=attributes, decisions=pickle.dumps(decisions))
        json.dump(data, data_file, indent=2, sort_keys=True)


def get_choice(s2gs_key, old_value, new_value):
    global decisions

    # This way old/new values can be swapped and decision is remembered
    key = frozenset([s2gs_key, old_value, new_value])
    if key not in decisions:
        print(
            "Naming conflict on {0}: {1} != {2}".format(s2gs_key, old_value, new_value)
        )
        print("Which do you want to use?")
        print("  (o) Old value '{0}'".format(old_value))
        print("  (n) New value '{0}'".format(new_value))
        while True:
            answer = raw_input("Choose 'o' or 'n' then press enter: ").lower()
            if answer not in ("o", "n"):
                print("Invalid choice `{0}`".format(answer))
            else:
                break
        decisions[key] = {"o": old_value, "n": new_value}[answer]
        print("")
    return decisions[key]


if __name__ == "__main__":
    main()
