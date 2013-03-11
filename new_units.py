# Shows new data entries from the requested build files:
#
# Usage: python new_data.py sc2reader/data/HotS/24764_units.csv sc2reader/data/HotS/24764_abilites.csv
#
# The output from this can be used to update the unit_lookup.csv and ability_lookup.csv files. Maybe the
# script can be fixed to append these lines automatically...
#
import pkgutil
import sys

UNIT_LOOKUP = dict()
for entry in pkgutil.get_data('sc2reader.data', 'unit_lookup.csv').split('\n'):
    if not entry: continue
    str_id, title = entry.strip().split(',')
    UNIT_LOOKUP[str_id] = title

with open(sys.argv[1],'r') as new_units:
	for line in new_units:
		new_unit_name = line.strip().split(',')[1]
		if new_unit_name not in UNIT_LOOKUP:
			print "{0},{1}".format(new_unit_name,new_unit_name)

print
print

ABIL_LOOKUP = dict()
for entry in pkgutil.get_data('sc2reader.data', 'ability_lookup.csv').split('\n'):
    if not entry: continue
    str_id, abilities = entry.split(',',1)
    ABIL_LOOKUP[str_id] = abilities.split(',')

with open(sys.argv[2], 'r') as new_abilities:
	for line in new_abilities:
		new_ability_name = line.strip().split(',')[1]
		if new_ability_name not in ABIL_LOOKUP:
			print "{0},{1}".format(new_ability_name,new_ability_name)
