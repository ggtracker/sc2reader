import argparse
import collections
import csv
import glob
import os
import xml.etree.ElementTree


def generate_build_data(balance_data_path):
    abilities = {}
    units = {}

    ability_lookup = {}

    for xml_file_path in glob.glob(os.path.join(balance_data_path, "*.xml")):
        tree = xml.etree.ElementTree.parse(xml_file_path)
        root = tree.getroot()

        for ability_element in root.findall("./abilities/ability"):
            ability_name = ability_element.get("id")
            if ability_element.get("index") and ability_name:
                abilities[ability_element.get("index")] = ability_name

                if ability_name not in ability_lookup:
                    ability_lookup[ability_name] = []

                for command_element in ability_element.findall("./command"):
                    command_id = command_element.get("id")
                    command_index_str = command_element.get("index")

                    if command_id and command_index_str:
                        command_index = int(command_index_str)

                        # Pad potential gaps in command indices with empty strings
                        while len(ability_lookup[ability_name]) <= command_index:
                            ability_lookup[ability_name].append("")

                        command_name = command_id if command_id != "Execute" else ability_name
                        ability_lookup[ability_name][command_index] = command_name

        unit_id = root.get("id")

        meta_element = root.find("./meta")

        if unit_id and meta_element is not None and meta_element.get("index"):
            units[meta_element.get("index")] = unit_id

        build_unit_elements = root.findall("./builds/unit")
        if build_unit_elements:
            build_ability_index = build_unit_elements[0].get("ability")

            if unit_id == "SCV":
                build_ability_name = "TerranBuild"
            elif unit_id == "Probe":
                build_ability_name = "ProtossBuild"
            elif unit_id == "Drone":
                build_ability_name = "ZergBuild"
            else:
                build_ability_name = "{}Build".format(unit_id)

            if build_ability_index:
                abilities[build_ability_index] = build_ability_name

            if build_ability_name not in ability_lookup:
                ability_lookup[build_ability_name] = []

            for element in build_unit_elements:
                built_unit_id = element.get("id")
                command_index_str = element.get("index")

                if built_unit_id and command_index_str:
                    command_index = int(command_index_str)

                    # Pad potential gaps in command indices with empty strings
                    while len(ability_lookup[build_ability_name]) <= command_index:
                        ability_lookup[build_ability_name].append("")

                    build_command_name = "Build{}".format(built_unit_id)
                    ability_lookup[build_ability_name][command_index] = build_command_name

        train_unit_elements = root.findall("./trains/unit")
        if train_unit_elements:
            train_ability_index = train_unit_elements[0].get("ability")

            if train_ability_index:
                train_ability_name = "{}Train".format(unit_id)
                abilities[train_ability_index] = train_ability_name

            if train_ability_name not in ability_lookup:
                ability_lookup[train_ability_name] = []

            for element in train_unit_elements:
                    element_ability_index = element.get("ability")
                    trained_unit_name = element.get("id")

                    if trained_unit_name:
                        # Handle cases where a unit can train other units using multiple ability indices.
                        # The Nexus is currently the only known example.
                        if element_ability_index != train_ability_index:
                            train_ability_index = element_ability_index

                            train_ability_name = "{}Train{}".format(unit_id, trained_unit_name)
                            abilities[train_ability_index] = train_ability_name

                            if train_ability_name not in ability_lookup:
                                ability_lookup[train_ability_name] = []

                            command_index_str = element.get("index")

                            if command_index_str:
                                command_index = int(command_index_str)

                                # Pad potential gaps in command indices with empty strings
                                while len(ability_lookup[train_ability_name]) <= command_index:
                                    ability_lookup[train_ability_name].append("")

                                ability_lookup[train_ability_name][command_index] = train_ability_name
                        else:
                            command_index_str = element.get("index")

                            if command_index_str:
                                command_index = int(command_index_str)

                                # Pad potential gaps in command indices with empty strings
                                while len(ability_lookup[train_ability_name]) <= command_index:
                                    ability_lookup[train_ability_name].append("")

                                train_command_name = "Train{}".format(trained_unit_name)
                                ability_lookup[train_ability_name][command_index] = train_command_name

        research_upgrade_elements = root.findall("./researches/upgrade")
        if research_upgrade_elements:
            research_ability_index = research_upgrade_elements[0].get("ability")
            research_ability_name = "{}Research".format(unit_id)

            abilities[research_ability_index] = research_ability_name

            if research_ability_name not in ability_lookup:
                ability_lookup[research_ability_name] = []

            for element in research_upgrade_elements:
                researched_upgrade_id = element.get("id")
                command_index_str = element.get("index")

                if researched_upgrade_id and command_index_str:
                    command_index = int(command_index_str)

                    # Pad potential gaps in command indices with empty strings
                    while len(ability_lookup[research_ability_name]) <= command_index:
                        ability_lookup[research_ability_name].append("")

                    research_command_name = "Research{}".format(researched_upgrade_id)
                    ability_lookup[research_ability_name][command_index] = research_command_name

    sorted_units = collections.OrderedDict(sorted(units.items(), key=lambda x: int(x[0])))
    sorted_abilities = collections.OrderedDict(sorted(abilities.items(), key=lambda x: int(x[0])))

    unit_lookup = [[unit_name, unit_name] for _, unit_name in sorted_units.items()]

    return sorted_units, sorted_abilities, unit_lookup, ability_lookup


def main():
    parser = argparse.ArgumentParser(description='Generate [BUILD_VERSION]_abilities.csv, [BUILD_VERSION]_units.csv,'
                                                 ' ability_lookup.csv and unit_lookup.csv files from exported balance'
                                                 ' data.')
    parser.add_argument('build_version', metavar='BUILD_VERSION', type=int,
                        help='the build version of the balance data export')
    parser.add_argument('balance_data_path', metavar='BALANCE_DATA_PATH', type=str,
                        help='the path to the balance data export')

    args = parser.parse_args()

    units, abilities, unit_lookup, ability_lookup = generate_build_data(args.balance_data_path)

    if not units or not abilities:
        parser.print_help()
        print("\n")

        raise ValueError("No balance data found at provided balance data path.")

    with open('{}_units.csv'.format(args.build_version), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', lineterminator=os.linesep)
        for unit_index, unit_name in units.items():
            csv_writer.writerow([unit_index, unit_name])

    with open('{}_abilities.csv'.format(args.build_version), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', lineterminator=os.linesep)
        for ability_index, ability_name in abilities.items():
            csv_writer.writerow([ability_index, ability_name])

    with open('unit_lookup.csv'.format(args.build_version), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', lineterminator=os.linesep)
        for lookup_entry in unit_lookup:
            csv_writer.writerow(lookup_entry)

    with open('ability_lookup.csv'.format(args.build_version), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', lineterminator=os.linesep)
        for ability_name, commands in ability_lookup.items():
            csv_writer.writerow([ability_name] + commands)


if __name__ == "__main__":
    main()
