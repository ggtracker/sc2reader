Supporting a new StarCraft II build version with updated balance data
=====================================================================

Sometimes when a new version comes out, such as (3.4.0) 44401, Blizzard will update the ids used to identify units and abilities.

See dsjoerg's commits on Jul 13, 2016 for context on what needs to be modified to support these changes: https://github.com/ggtracker/sc2reader/commits/upstream

Here are some detailed steps on how to add support for these new ids.

1. Install and open the StarCraft II Editor, then navigate to `File` -> `Export Balance Data...` and select the expansion level for the balance data you wish to add, then select the directory which you wish to export the balance data to.
2. Find out the build version this balance data correlates to. One method of doing this is to navigate to the s2protocol repo (https://github.com/Blizzard/s2protocol) and looking at the version of the latest protocol.
At the time of writing, the latest build version is 53644.
3. Execute `sc2reader/generate_build_data.py`, passing the expansion level selected in step 1, the build version determined in step 2, the directory the balance data was exported to in step 1, and the sc2reader project root directory as parameters.
e.g. `python3 sc2reader/generate_build_data.py LotV 53644 balance_data/ sc2reader/`
This will generate the necessary data files to support the new build version (namely, `53644_abilities.csv`, `53644_units.csv`, and updated versions of `ability_lookup.csv` and `unit_lookup.csv`).
4. Finally, modify `sc2reader/data/__init__.py` and `sc2reader/resources.py` to register support for the new build version.
