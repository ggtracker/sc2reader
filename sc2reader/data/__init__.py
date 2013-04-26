from __future__ import absolute_import

import json
import pkgutil
from collections import OrderedDict
from sc2reader.log_utils import loggable

ABIL_LOOKUP = dict()
for entry in pkgutil.get_data('sc2reader.data', 'ability_lookup.csv').split('\n'):
    if not entry: continue
    str_id, abilities = entry.split(',',1)
    ABIL_LOOKUP[str_id] = abilities.split(',')

UNIT_LOOKUP = dict()
for entry in pkgutil.get_data('sc2reader.data', 'unit_lookup.csv').split('\n'):
    if not entry: continue
    str_id, title = entry.strip().split(',')
    UNIT_LOOKUP[str_id] = title

unit_data = pkgutil.get_data('sc2reader.data', 'unit_info.json')
unit_lookup = json.loads(unit_data)

command_data = pkgutil.get_data('sc2reader.data', 'train_commands.json')
train_commands = json.loads(command_data)

class Unit(object):

    def __init__(self, unit_id, flags):
        #: A reference to the player that owns this unit
        self.owner = None

        #: The frame the unit was started at
        self.started_at = None

        #: The frame the unit was finished at
        self.finished_at = None

        #: The frame the unit died at
        self.died_at = None

        #: A reference to the player that killed this unit. Not always available.
        self.killed_by = None

        self.id = unit_id
        self.flags = flags
        self._type_class = None
        self.type_history = OrderedDict()
        self.hallucinated = (flags & 2 == 2)

    def set_type(self, unit_type, frame):
        self._type_class = unit_type
        self.type_history[frame] = unit_type

    def is_type(self, unit_type, strict=True):
        if strict:
            if isinstance(unit_type, int):
                if self._type_class:
                    return unit_type == self._type_class.id
                else:
                    return unit_type == 0
            elif isinstance(unit_type, Unit):
                return self._type_class == unit_type
            else:
                if self._type_class:
                    return unit_type == self._type_class.str_id
                else:
                    return unit_type == None
        else:
            if isinstance(unit_type, int):
                if self._type_class:
                    return unit_type in [utype.id for utype in self.type_history.values()]
                else:
                    return unit_type == 0
            elif isinstance(unit_type, Unit):
                return unit_type in self.type_history.values()
            else:
                if self._type_class:
                    return unit_type in [utype.str_id for utype in self.type_history.values()]
                else:
                    return unit_type == None

    @property
    def name(self):
        return self._type_class.name if self._type_class else None

    @property
    def title(self):
        return self._type_class.title if self._type_class else None

    @property
    def type(self):
        """ For backwards compatibility this returns the int id instead of the actual class """
        return self._type_class.id if self._type_class else None

    @property
    def race(self):
        return self._type_class.race if self._type_class else None

    @property
    def minerals(self):
        return self._type_class.minerals if self._type_class else None

    @property
    def vespene(self):
        return self._type_class.vespene if self._type_class else None

    @property
    def supply(self):
        return self._type_class.supply if self._type_class else None

    @property
    def is_worker(self):
        return self._type_class.is_worker if self._type_class else False

    @property
    def is_building(self):
        return self._type_class.is_building if self._type_class else False

    @property
    def is_army(self):
        return self._type_class.is_army if self._type_class else False

    def __str__(self):
        return "{0} [{1:X}]".format(self.name, self.id)

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)


class Ability(object):
    pass

@loggable
class Build(object):
    def __init__(self, build_id):
        self.id=build_id
        self.units = dict()
        self.abilities = dict()

    def create_unit(self, unit_id, unit_type, unit_flags, frame):
        unit = Unit(unit_id, unit_flags)
        self.change_type(unit, unit_type, frame)
        return unit

    def change_type(self, unit, new_type, frame):
        if new_type in self.units:
            unit_type = self.units[new_type]
            unit.set_type(unit_type, frame)
        else:
            self.logger.error("Unable to change type of {0} to {1} [frame {2}]; unit type not found in build {3}".format(unit,new_type,frame,self.id))

    def add_ability(self, ability_id, name, title=None, is_build=False, build_time=None, build_unit=None):
        ability = type(name,(Ability,), dict(
            id=ability_id,
            name=name,
            title=title or name,
            is_build=is_build,
            build_time=build_time,
            build_unit=build_unit
        ))
        setattr(self, name, ability)
        self.abilities[ability_id] = ability

    def add_unit_type(self, type_id, str_id, name, title=None, race='Neutral', minerals=0, vespene=0, supply=0, is_building=False, is_worker=False, is_army=False):
        unit = type(name,(Unit,), dict(
            id=type_id,
            str_id=str_id,
            name=name,
            title=title or name,
            race=race,
            minerals=minerals,
            vespene=vespene,
            supply=supply,
            is_building=is_building,
            is_worker=is_worker,
            is_army=is_army,
        ))
        setattr(self, name, unit)
        self.units[type_id] = unit
        self.units[str_id] = unit

def load_build(expansion, version):
    build = Build(version)

    unit_file = '{0}/{1}_units.csv'.format(expansion,version)
    for entry in pkgutil.get_data('sc2reader.data', unit_file).split('\n'):
        if not entry: continue
        int_id, str_id = entry.strip().split(',')
        unit_type = int(int_id,10)
        title = UNIT_LOOKUP[str_id]

        values = dict(type_id=unit_type, str_id=str_id, name=title)
        for race in ('Protoss','Terran','Zerg'):
            if title.lower() in unit_lookup[race]:
                values.update(unit_lookup[race][title.lower()])
                values['race']=race
                break

        build.add_unit_type(**values)

    abil_file = '{0}/{1}_abilities.csv'.format(expansion,version)
    build.add_ability(ability_id=0, name='RightClick', title='Right Click')
    for entry in pkgutil.get_data('sc2reader.data', abil_file).split('\n'):
        if not entry: continue
        int_id_base, str_id = entry.strip().split(',')
        int_id_base = int(int_id_base,10) << 5

        abils = ABIL_LOOKUP[str_id]
        real_abils = [(i,abil) for i,abil in enumerate(abils) if abil.strip()!='']

        if len(real_abils)==0:
            real_abils = [(0, str_id)]

        for index, ability_name in real_abils:
            unit_name, build_time = train_commands.get(ability_name, ('', 0))
            if 'Hallucinated' in unit_name: # Not really sure how to handle hallucinations
                unit_name = unit_name[12:]

            build.add_ability(
                ability_id=int_id_base | index,
                name=ability_name,
                is_build=bool(unit_name),
                build_unit=getattr(build, unit_name, None),
                build_time=build_time
            )

    return build

# Load the WoL Data
wol_builds = dict()
for version in ('16117','17326','18092','19458','22612','24944'):
    wol_builds[version] = load_build('WoL', version)

# Load HotS Data
hots_builds = dict()
for version in ('base','23925','24247','24764'):
    hots_builds[version] = load_build('HotS', version)

builds = {'WoL':wol_builds,'HotS':hots_builds}

