import argparse
import collections
import csv
import glob
import os
import xml.etree.ElementTree


def generate_abilities(balance_data_path):
    abilities = {}

    for xml_file_path in glob.glob(os.path.join(balance_data_path, "*.xml")):
        tree = xml.etree.ElementTree.parse(xml_file_path)
        root = tree.getroot()

        for ability_element in root.findall("./abilities/ability"):
            if ability_element.get("index") and ability_element.get("id"):
                abilities[ability_element.get("index")] = ability_element.get("id")

        unit_name = root.get("id")

        build_unit_element = root.find("./builds/unit")
        if build_unit_element:
            build_ability_index = build_unit_element.get("ability")

            if unit_name == "SCV":
                build_ability_name = "TerranBuild"
            elif unit_name == "Probe":
                build_ability_name = "ProtossBuild"
            elif unit_name == "Drone":
                build_ability_name = "ZergBuild"
            else:
                build_ability_name = "{}Build".format(unit_name)

            if build_ability_index:
                abilities[build_ability_index] = build_ability_name

        train_unit_elements = root.findall("./trains/unit")
        if train_unit_elements:
            train_ability_index = train_unit_elements[0].get("ability")

            if train_ability_index:
                abilities[train_ability_index] = "{}Train".format(unit_name)

                # Handle cases where a unit can train other units using multiple ability indices.
                # The Nexus is currently the only known example.
                for element in train_unit_elements[1:]:
                    element_ability_index = element.get("ability")
                    trained_unit_name = element.get("id")

                    if element_ability_index != train_ability_index and trained_unit_name:
                        train_ability_index = element_ability_index

                        abilities[train_ability_index] = "{}Train{}".format(unit_name, trained_unit_name)

        research_upgrade_element = root.find("./researches/upgrade")
        if research_upgrade_element:
            research_ability_index = research_upgrade_element.get("ability")
            research_ability_name = "{}Research".format(unit_name)

            abilities[research_ability_index] = research_ability_name

    return collections.OrderedDict(sorted(abilities.items(), key=lambda x: int(x[0])))


def main():
    parser = argparse.ArgumentParser(description='Generate a [BUILD]_abilities.csv file from exported balance data.')
    parser.add_argument('build_version', metavar='BUILD_VERSION', type=int,
                        help='the build version of the balance data export')
    parser.add_argument('balance_data_path', metavar='BALANCE_DATA_PATH', type=str,
                        help='the path to the balance data export')

    args = parser.parse_args()

    abilities = generate_abilities(args.balance_data_path)

    if not abilities:
        raise ValueError("No balance data found at provided balance data path.")

    with open('{}_abilities.csv'.format(args.build_version), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        for ability_index, ability_name in abilities.items():
            csv_writer.writerow([ability_index, ability_name])


if __name__ == "__main__":
    main()
