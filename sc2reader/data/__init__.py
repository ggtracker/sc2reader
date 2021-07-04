# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import json
import pkgutil

try:
    from collections import OrderedDict
except ImportError as e:
    from ordereddict import OrderedDict

from sc2reader.log_utils import loggable

try:
    cmp  # Python 2
except NameError:
    cmp = lambda a, b: (a > b) - (a < b)  # noqa Python 3

ABIL_LOOKUP = dict()
for entry in (
    pkgutil.get_data("sc2reader.data", "ability_lookup.csv").decode("utf8").split("\n")
):
    if not entry:
        continue
    str_id, abilities = entry.split(",", 1)
    ABIL_LOOKUP[str_id] = abilities.split(",")

UNIT_LOOKUP = dict()
for entry in (
    pkgutil.get_data("sc2reader.data", "unit_lookup.csv").decode("utf8").split("\n")
):
    if not entry:
        continue
    str_id, title = entry.strip().split(",")
    UNIT_LOOKUP[str_id] = title

unit_data = pkgutil.get_data("sc2reader.data", "unit_info.json").decode("utf8")
unit_lookup = json.loads(unit_data)

command_data = pkgutil.get_data("sc2reader.data", "train_commands.json").decode("utf8")
train_commands = json.loads(command_data)


class Unit(object):
    """Represents an in-game unit."""

    def __init__(self, unit_id):
        #: A reference to the player that currently owns this unit. Only available for 2.0.8+ replays.
        self.owner = None

        #: The frame the unit was started at. Only available for 2.0.8+ replays.
        #: Specifically, it is the frame the :class:`~sc2reader.events.tracker.UnitInitEvent` is received. For units
        #: that are born and not initiated this will be the same as :attr:`finished_at`.
        self.started_at = None

        #: The frame the unit was finished at. Only available for 2.0.8+ replays.
        #: Specifically, it is the frame that the :class:`~sc2reader.events.tracker.UnitDoneEvent` is received. For units
        #: that are born and not initiated this will be the frame that the :class:`~sc2reader.events.tracker.UnitBornEvent`
        #: is received.
        self.finished_at = None

        #: The frame the unit died at. Only available for 2.0.8+ replays.
        #: Specifically, it is the frame that the :class:`~sc2reader.events.tracker.UnitDiedEvent` is received.
        self.died_at = None

        #: Deprecated, see :attr:`self.killing_player`
        self.killed_by = None

        #: A reference to the player that killed this unit. Only available for 2.0.8+ replays.
        #: This value is not set if the killer is unknown or not relevant (morphed into a
        #: different unit or used to create a building, etc)
        self.killing_player = None

        #: A reference to the unit that killed this unit. Only available for 2.1+ replays.
        #: This value is not set if the killer is unknown or not relevant (morphed into a
        #: different unit or used to create a building, etc). If the killing unit dies before
        #: the killed unit dies, a bug may cause the killing unit to be None. This can occur
        #: due because of projectile speeds.
        self.killing_unit = None

        #: A list of units that this unit has killed. Only available for 2.1+ replays.
        #: The unit only gets credit for the kills that it gets the final blow on.
        self.killed_units = list()

        #: The unique in-game id for this unit. The id can sometimes be zero because
        #: TargetUnitCommandEvents will create a new unit with id zero when a unit
        #: behind the fog of war is targeted.
        self.id = unit_id

        #: A reference to the unit type this unit is current in.
        #: e.g. SeigeTank is a different type than SeigeTankSeiged
        self._type_class = None

        #: A history of all the unit types this unit has had stored
        #: in order by frame the type was acquired.
        self.type_history = OrderedDict()

        #: Is this unit type a hallucinated one?
        self.hallucinated = False

        self.flags = 0

    def apply_flags(self, flags):
        self.flags = flags
        self.hallucinated = flags & 2 == 2

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
                    return unit_type is None
        else:
            if isinstance(unit_type, int):
                if self._type_class:
                    return unit_type in [
                        utype.id for utype in self.type_history.values()
                    ]
                else:
                    return unit_type == 0
            elif isinstance(unit_type, Unit):
                return unit_type in self.type_history.values()
            else:
                if self._type_class:
                    return unit_type in [
                        utype.str_id for utype in self.type_history.values()
                    ]
                else:
                    return unit_type is None

    @property
    def name(self):
        """The name of the unit type currently active. None if no type is assigned"""
        return self._type_class.name if self._type_class else None

    @property
    def title(self):
        return self._type_class.title if self._type_class else None

    @property
    def type(self):
        """The internal type id of the current unit type of this unit. None if no type is assigned"""
        return self._type_class.id if self._type_class else None

    @property
    def race(self):
        """The race of this unit. One of Terran, Protoss, Zerg, Neutral, or None"""
        return self._type_class.race if self._type_class else None

    @property
    def minerals(self):
        """The mineral cost of the unit. None if no type is assigned"""
        return self._type_class.minerals if self._type_class else None

    @property
    def vespene(self):
        """The vespene cost of the unit. None if no type is assigned"""
        return self._type_class.vespene if self._type_class else None

    @property
    def supply(self):
        """The supply used by this unit. Negative for supply providers. None if no type is assigned"""
        return self._type_class.supply if self._type_class else None

    @property
    def is_worker(self):
        """Boolean flagging units as worker units. SCV, MULE, Drone, Probe"""
        return self._type_class.is_worker if self._type_class else False

    @property
    def is_building(self):
        """Boolean flagging units as buildings."""
        return self._type_class.is_building if self._type_class else False

    @property
    def is_army(self):
        """Boolean flagging units as army units."""
        return self._type_class.is_army if self._type_class else False

    def __str__(self):
        return "{0} [{1:X}]".format(self.name, self.id)

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def __lt__(self, other):
        return self.id < other.id

    def __le__(self, other):
        return self.id <= other.id

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    def __gt__(self, other):
        return self.id > other.id

    def __ge__(self, other):
        return self.id >= other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)


class UnitType(object):
    """Represents an in game unit type"""

    def __init__(
        self,
        type_id,
        str_id=None,
        name=None,
        title=None,
        race=None,
        minerals=0,
        vespene=0,
        supply=0,
        is_building=False,
        is_worker=False,
        is_army=False,
    ):
        #: The internal integer id representing this unit type
        self.id = type_id

        #: The internal string id representing this unit type
        self.str_id = str_id

        #: The name of this unit type
        self.name = name

        #: The printable title of this unit type; has spaces and possibly punctuation
        self.title = title

        #: The race this unit type belongs to
        self.race = race

        #: The mineral cost of this unit type
        self.minerals = minerals

        #: The vespene cost of this unit type
        self.vespene = vespene

        #: The supply cost of this unit type
        self.supply = supply

        #: Boolean flagging this unit type as a building
        self.is_building = is_building

        #: Boolean flagging this unit type as a worker
        self.is_worker = is_worker

        #: Boolean flagging this unit type as an army unit
        self.is_army = is_army


class Ability(object):
    """Represents an in-game ability"""

    def __init__(
        self, id, name=None, title=None, is_build=False, build_time=0, build_unit=None
    ):
        #: The internal integer id representing this ability.
        self.id = id

        #: The name of this ability
        self.name = name

        #: The printable title of this ability; has spaces and possibly punctuation.
        self.title = title

        #: Boolean flagging this ability as creating a new unit.
        self.is_build = is_build

        #: The number of seconds required to build this unit. 0 if not ``is_build``.
        self.build_time = build_time

        #: A reference to the :class:`UnitType` type built by this ability. Default to None.
        self.build_unit = build_unit


@loggable
class Build(object):
    """
    :param build_id: The build number identifying this dataset.

    The datapack for a particular group of builds. Maps internal integer ids
    to :class:`Unit` and :class:`Ability` types. Also contains builder methods
    for creating new units and changing their types.

    All build data is valid for standard games only. For arcade maps mileage
    may vary.
    """

    def __init__(self, build_id):
        #: The integer id of the build
        self.id = build_id

        #: A dictionary mapping integer ids to available unit types.
        self.units = dict()

        #: A dictionary mapping integer ids to available abilities.
        self.abilities = dict()

    def create_unit(self, unit_id, unit_type, frame):
        """
        :param unit_id: The unique id of this unit.
        :param unit_type: The unit type to assign to the new unit

        Creates a new unit and assigns it to the specified type.
        """
        unit = Unit(unit_id)
        self.change_type(unit, unit_type, frame)
        return unit

    def change_type(self, unit, new_type, frame):
        """
        :param unit: The changing types.
        :param unit_type: The unit type to assign to this unit

        Assigns the given type to a unit.
        """
        if new_type in self.units:
            unit_type = self.units[new_type]
            unit.set_type(unit_type, frame)
        else:
            self.logger.error(
                "Unable to change type of {0} to {1} [frame {2}]; unit type not found in build {3}".format(
                    unit, new_type, frame, self.id
                )
            )

    def add_ability(
        self,
        ability_id,
        name,
        title=None,
        is_build=False,
        build_time=None,
        build_unit=None,
    ):
        ability = Ability(
            ability_id,
            name=name,
            title=title or name,
            is_build=is_build,
            build_time=build_time,
            build_unit=build_unit,
        )
        setattr(self, name, ability)
        self.abilities[ability_id] = ability

    def add_unit_type(
        self,
        type_id,
        str_id,
        name,
        title=None,
        race="Neutral",
        minerals=0,
        vespene=0,
        supply=0,
        is_building=False,
        is_worker=False,
        is_army=False,
    ):
        unit = UnitType(
            type_id,
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
        )
        setattr(self, name, unit)
        self.units[type_id] = unit
        self.units[str_id] = unit


def load_build(expansion, version):
    build = Build(version)

    unit_file = "{0}/{1}_units.csv".format(expansion, version)
    for entry in (
        pkgutil.get_data("sc2reader.data", unit_file).decode("utf8").split("\n")
    ):
        if not entry:
            continue
        int_id, str_id = entry.strip().split(",")
        unit_type = int(int_id, 10)
        title = UNIT_LOOKUP[str_id]

        values = dict(type_id=unit_type, str_id=str_id, name=title)
        for race in ("Protoss", "Terran", "Zerg"):
            if title.lower() in unit_lookup[race]:
                values.update(unit_lookup[race][title.lower()])
                values["race"] = race
                break

        build.add_unit_type(**values)

    abil_file = "{0}/{1}_abilities.csv".format(expansion, version)
    build.add_ability(ability_id=0, name="RightClick", title="Right Click")
    for entry in (
        pkgutil.get_data("sc2reader.data", abil_file).decode("utf8").split("\n")
    ):
        if not entry:
            continue
        int_id_base, str_id = entry.strip().split(",")
        int_id_base = int(int_id_base, 10) << 5

        abils = ABIL_LOOKUP[str_id]
        real_abils = [(i, abil) for i, abil in enumerate(abils) if abil.strip() != ""]

        if len(real_abils) == 0:
            real_abils = [(0, str_id)]

        for index, ability_name in real_abils:
            unit_name, build_time = train_commands.get(ability_name, ("", 0))
            if (
                "Hallucinated" in unit_name
            ):  # Not really sure how to handle hallucinations
                unit_name = unit_name[12:]

            build.add_ability(
                ability_id=int_id_base | index,
                name=ability_name,
                is_build=bool(unit_name),
                build_unit=getattr(build, unit_name, None),
                build_time=build_time,
            )

    return build


# Load the WoL Data
wol_builds = dict()
for version in ("16117", "17326", "18092", "19458", "22612", "24944"):
    wol_builds[version] = load_build("WoL", version)

# Load HotS Data
hots_builds = dict()
for version in ("base", "23925", "24247", "24764"):
    hots_builds[version] = load_build("HotS", version)
hots_builds["38215"] = load_build("LotV", "base")
hots_builds["38215"].id = "38215"

# Load LotV Data
lotv_builds = dict()
for version in (
    "base",
    "44401",
    "47185",
    "48258",
    "53644",
    "54724",
    "59587",
    "70154",
    "76114",
    "77379",
    "80949",
):
    lotv_builds[version] = load_build("LotV", version)

datapacks = builds = {"WoL": wol_builds, "HotS": hots_builds, "LotV": lotv_builds}
