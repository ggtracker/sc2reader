# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import functools

from sc2reader.events.base import Event
from sc2reader.utils import Length

clamp = functools.partial(max, 0)


class TrackerEvent(Event):
    """
    Parent class for all tracker events.
    """

    def __init__(self, frames):
        #: The frame of the game this event was applied
        #: Ignore all but the lowest 32 bits of the frame
        self.frame = frames % 2 ** 32

        #: The second of the game (game time not real time) this event was applied
        self.second = self.frame >> 4

        #: Short cut string for event class name
        self.name = self.__class__.__name__

    def load_context(self, replay):
        pass

    def _str_prefix(self):
        return "{0}\t ".format(Length(seconds=int(self.frame / 16)))

    def __str__(self):
        return self._str_prefix() + self.name


class PlayerSetupEvent(TrackerEvent):
    """Sent during game setup to help us organize players better"""

    def __init__(self, frames, data, build):
        super(PlayerSetupEvent, self).__init__(frames)

        #: The player id of the player we are setting up
        self.pid = data[0]

        #: The type of this player. One of 1=human, 2=cpu, 3=neutral, 4=hostile
        self.type = data[1]

        #: The user id of the player we are setting up. None of not human
        self.uid = data[2]

        #: The slot id of the player we are setting up. None if not playing
        self.sid = data[3]


class PlayerStatsEvent(TrackerEvent):
    """
    Player Stats events are generated for all players that were in the game even if they've since
    left every 10 seconds. An additional set of stats events are generated at the end of the game.

    When a player leaves the game, a single PlayerStatsEvent is generated for that player and no
    one else. That player continues to generate PlayerStatsEvents at 10 second intervals until the
    end of the game.

    In 1v1 games, the above behavior can cause the losing player to have 2 events generated at the
    end of the game. One for leaving and one for the  end of the game.
    """

    def __init__(self, frames, data, build):
        super(PlayerStatsEvent, self).__init__(frames)

        #: Id of the player the stats are for
        self.pid = data[0]

        #: The Player object that these stats apply to
        self.player = None

        #: An ordered list of all the available stats
        self.stats = data[1]

        #: Minerals currently available to the player
        self.minerals_current = clamp(self.stats[0])

        #: Vespene currently available to the player
        self.vespene_current = clamp(self.stats[1])

        #: The rate the player is collecting minerals
        self.minerals_collection_rate = clamp(self.stats[2])

        #: The rate the player is collecting vespene
        self.vespene_collection_rate = clamp(self.stats[3])

        #: The number of active workers the player has
        self.workers_active_count = clamp(self.stats[4])

        #: The total mineral cost of army units (buildings?) currently being built/queued
        self.minerals_used_in_progress_army = clamp(self.stats[5])

        #: The total mineral cost of economy units (buildings?) currently being built/queued
        self.minerals_used_in_progress_economy = clamp(self.stats[6])

        #: The total mineral cost of technology research (buildings?) currently being built/queued
        self.minerals_used_in_progress_technology = clamp(self.stats[7])

        #: The total mineral cost of all things in progress
        self.minerals_used_in_progress = (
            self.minerals_used_in_progress_army
            + self.minerals_used_in_progress_economy
            + self.minerals_used_in_progress_technology
        )

        #: The total vespene cost of army units (buildings?) currently being built/queued
        self.vespene_used_in_progress_army = clamp(self.stats[8])

        #: The total vespene cost of economy units (buildings?) currently being built/queued.
        self.vespene_used_in_progress_economy = clamp(self.stats[9])

        #: The total vespene cost of technology research (buildings?) currently being built/queued.
        self.vespene_used_in_progress_technology = clamp(self.stats[10])

        #: The total vespene cost of all things in progress
        self.vespene_used_in_progress = (
            self.vespene_used_in_progress_army
            + self.vespene_used_in_progress_economy
            + self.vespene_used_in_progress_technology
        )

        #: The total cost of all things in progress
        self.resources_used_in_progress = (
            self.minerals_used_in_progress + self.vespene_used_in_progress
        )

        #: The total mineral cost of current army units (buildings?)
        self.minerals_used_current_army = clamp(self.stats[11])

        #: The total mineral cost of current economy units (buildings?)
        self.minerals_used_current_economy = clamp(self.stats[12])

        #: The total mineral cost of current technology research (buildings?)
        self.minerals_used_current_technology = clamp(self.stats[13])

        #: The total mineral cost of all current things
        self.minerals_used_current = (
            self.minerals_used_current_army
            + self.minerals_used_current_economy
            + self.minerals_used_current_technology
        )

        #: The total vespene cost of current army units (buildings?)
        self.vespene_used_current_army = clamp(self.stats[14])

        #: The total vespene cost of current economy units (buildings?)
        self.vespene_used_current_economy = clamp(self.stats[15])

        #: The total vespene cost of current technology research (buildings?)
        self.vespene_used_current_technology = clamp(self.stats[16])

        #: The total vepsene cost of all current things
        self.vespene_used_current = (
            self.vespene_used_current_army
            + self.vespene_used_current_economy
            + self.vespene_used_current_technology
        )

        #: The total cost of all things current
        self.resources_used_current = (
            self.minerals_used_current + self.vespene_used_current
        )

        #: The total mineral cost of all army units (buildings?) lost
        self.minerals_lost_army = clamp(self.stats[17])

        #: The total mineral cost of all economy units (buildings?) lost
        self.minerals_lost_economy = clamp(self.stats[18])

        #: The total mineral cost of all technology research (buildings?) lost
        self.minerals_lost_technology = clamp(self.stats[19])

        #: The total mineral cost of all lost things
        self.minerals_lost = (
            self.minerals_lost_army
            + self.minerals_lost_economy
            + self.minerals_lost_technology
        )

        #: The total vespene cost of all army units (buildings?) lost
        self.vespene_lost_army = clamp(self.stats[20])

        #: The total vespene cost of all economy units (buildings?) lost
        self.vespene_lost_economy = clamp(self.stats[21])

        #: The total vespene cost of all technology research (buildings?) lost
        self.vespene_lost_technology = clamp(self.stats[22])

        #: The total vepsene cost of all lost things
        self.vespene_lost = (
            self.vespene_lost_army
            + self.vespene_lost_economy
            + self.vespene_lost_technology
        )

        #: The total resource cost of all lost things
        self.resources_lost = self.minerals_lost + self.vespene_lost

        #: The total mineral value of enemy army units (buildings?) killed
        self.minerals_killed_army = clamp(self.stats[23])

        #: The total mineral value of enemy economy units (buildings?) killed
        self.minerals_killed_economy = clamp(self.stats[24])

        #: The total mineral value of enemy technology research (buildings?) killed
        self.minerals_killed_technology = clamp(self.stats[25])

        #: The total mineral value of all killed things
        self.minerals_killed = (
            self.minerals_killed_army
            + self.minerals_killed_economy
            + self.minerals_killed_technology
        )

        #: The total vespene value of enemy army units (buildings?) killed
        self.vespene_killed_army = clamp(self.stats[26])

        #: The total vespene value of enemy economy units (buildings?) killed
        self.vespene_killed_economy = clamp(self.stats[27])

        #: The total vespene value of enemy technology research (buildings?) killed
        self.vespene_killed_technology = clamp(self.stats[28])

        #: The total vespene cost of all killed things
        self.vespene_killed = (
            self.vespene_killed_army
            + self.vespene_killed_economy
            + self.vespene_killed_technology
        )

        #: The total resource cost of all killed things
        self.resources_killed = self.minerals_killed + self.vespene_killed

        #: The food supply currently used
        self.food_used = clamp(self.stats[29]) / 4096.0

        #: The food supply currently available
        self.food_made = clamp(self.stats[30]) / 4096.0

        #: The total mineral value of all active forces
        self.minerals_used_active_forces = clamp(self.stats[31])

        #: The total vespene value of all active forces
        self.vespene_used_active_forces = clamp(self.stats[32])

        #: Minerals of army value lost to friendly fire
        self.ff_minerals_lost_army = clamp(self.stats[33]) if build >= 26490 else None

        #: Minerals of economy value lost to friendly fire
        self.ff_minerals_lost_economy = (
            clamp(self.stats[34]) if build >= 26490 else None
        )

        #: Minerals of technology value lost to friendly fire
        self.ff_minerals_lost_technology = (
            clamp(self.stats[35]) if build >= 26490 else None
        )

        #: Vespene of army value lost to friendly fire
        self.ff_vespene_lost_army = clamp(self.stats[36]) if build >= 26490 else None

        #: Vespene of economy value lost to friendly fire
        self.ff_vespene_lost_economy = clamp(self.stats[37]) if build >= 26490 else None

        #: Vespene of technology value lost to friendly fire
        self.ff_vespene_lost_technology = (
            clamp(self.stats[38]) if build >= 26490 else None
        )

    def __str__(self):
        return self._str_prefix() + "{0: >15} - Stats Update".format(str(self.player))


class UnitBornEvent(TrackerEvent):
    """
    Generated when a unit is created in a finished state in the game. Examples include the Marine,
    Zergling, and Zealot (when trained from a gateway). Units that enter the game unfinished (all
    buildings, warped in units) generate a :class:`UnitInitEvent` instead.

    Unfortunately, units that are born do not have events marking their beginnings like
    :class:`UnitInitEvent` and :class:`UnitDoneEvent` do. The closest thing to it are the
    :class:`~sc2reader.event.game.CommandEvent` game events where the command is a train unit
    command.
    """

    def __init__(self, frames, data, build):
        super(UnitBornEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit being born
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that was born
        self.unit = None

        #: The unit type name of the unit being born
        self.unit_type_name = data[2].decode("utf8")

        #: The id of the player that controls this unit.
        self.control_pid = data[3]

        #: The id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[4]

        #: The player object that pays upkeep for this one. 0 means neutral unit
        self.unit_upkeeper = None

        #: The player object that controls this unit. 0 means neutral unit
        self.unit_controller = None

        #: The x coordinate of the center of the born unit's footprint. Only 4 point resolution
        #: prior to Starcraft Patch 2.1.
        self.x = data[5]

        #: The y coordinate of the center of the born unit's footprint. Only 4 point resolution
        #: prior to Starcraft Patch 2.1.
        self.y = data[6]

        #: The map location of the unit birth
        self.location = (self.x, self.y)

        if build < 27950:
            self.x = self.x * 4
            self.y = self.y * 4
            self.location = (self.x, self.y)

    def __str__(self):
        return self._str_prefix() + "{0: >15} - Unit born {1}".format(
            str(self.unit_upkeeper), self.unit
        )


class UnitDiedEvent(TrackerEvent):
    """
    Generated when a unit dies or is removed from the game for any reason. Reasons include
    morphing, merging, and getting killed.
    """

    def __init__(self, frames, data, build):
        super(UnitDiedEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit being killed
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that died
        self.unit = None

        #: Deprecated, see :attr:`killing_player_id`
        self.killer_pid = data[2]

        #: Deprecated, see :attr:`killing_player`
        self.killer = None

        #: The id of the player that killed this unit. None when not available.
        self.killing_player_id = data[2]

        #: The player object of the that killed the unit. Not always available.
        self.killing_player = None

        #: The x coordinate of the center of the dying unit's footprint. Only 4 point resolution
        #: prior to Starcraft Patch 2.1.
        self.x = data[3]

        #: The y coordinate of the center of the dying unit's footprint. Only 4 point resolution
        #: prior to Starcraft Patch 2.1.
        self.y = data[4]

        #: The map location the unit was killed at.
        self.location = (self.x, self.y)

        #: The index portion of the killing unit's id. Available for build 27950+
        self.killing_unit_index = None

        #: The recycle portion of the killing unit's id. Available for build 27950+
        self.killing_unit_recycle = None

        #: The unique id of the unit doing the killing. Available for build 27950+
        self.killing_unit_id = None

        #: A reference to the :class:`Unit` that killed this :class:`Unit`
        self.killing_unit = None

        if build < 27950:
            self.x = self.x * 4
            self.y = self.y * 4
            self.location = (self.x, self.y)
        else:
            # Starcraft patch 2.1 introduced killer unit indexes
            self.killing_unit_index = data[5]
            self.killing_unit_recycle = data[6]
            if self.killing_unit_index:
                self.killing_unit_id = (
                    self.killing_unit_index << 18 | self.killing_unit_recycle
                )

    def __str__(self):
        return self._str_prefix() + "{0: >15} - Unit died {1}.".format(
            str(self.unit.owner), self.unit
        )


class UnitOwnerChangeEvent(TrackerEvent):
    """
    Generated when either ownership or control of a unit is changed. Neural Parasite is an example
    of an action that would generate this event.
    """

    def __init__(self, frames, data, build):
        super(UnitOwnerChangeEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit changing ownership
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that is affected by this event
        self.unit = None

        #: The new id of the player that controls this unit.
        self.control_pid = data[2]

        #: The new id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[3]

        #: The player object that pays upkeep for this one. 0 means neutral unit
        self.unit_upkeeper = None

        #: The player object that controls this unit. 0 means neutral unit
        self.unit_controller = None

    def __str__(self):
        return self._str_prefix() + "{0: >15} took {1}".format(
            str(self.unit_upkeeper), self.unit
        )


class UnitTypeChangeEvent(TrackerEvent):
    """
    Generated when the unit's type changes. This generally tracks upgrades to buildings (Hatch,
    Lair, Hive) and mode switches (Sieging Tanks, Phasing prisms, Burrowing roaches). There may
    be some other situations where a unit transformation is a type change and not a new unit.
    """

    def __init__(self, frames, data, build):
        super(UnitTypeChangeEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit changing type
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that was changed
        self.unit = None

        #: The the new unit type name
        self.unit_type_name = data[2].decode("utf8")

    def __str__(self):
        return self._str_prefix() + "{0: >15} - Unit {1} type changed to {2}".format(
            str(self.unit.owner), self.unit, self.unit_type_name
        )


class UpgradeCompleteEvent(TrackerEvent):
    """
    Generated when a player completes an upgrade.
    """

    def __init__(self, frames, data, build):
        super(UpgradeCompleteEvent, self).__init__(frames)

        #: The player that completed the upgrade
        self.pid = data[0]

        #: The Player object that completed the upgrade
        self.player = None

        #: The name of the upgrade
        self.upgrade_type_name = data[1].decode("utf8")

        #: The number of times this upgrade as been researched
        self.count = data[2]

    def __str__(self):
        return self._str_prefix() + "{0: >15} - {1} upgrade completed".format(
            str(self.player), self.upgrade_type_name
        )


class UnitInitEvent(TrackerEvent):
    """
    The counter part to :class:`UnitDoneEvent`, generated by the game engine when a unit is
    initiated. This applies only to units which are started in game before they are finished.
    Primary examples being buildings and warp-in units.
    """

    def __init__(self, frames, data, build):
        super(UnitInitEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the stated unit
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that was started (e.g. started to warp in)
        self.unit = None

        #: The the new unit type name
        self.unit_type_name = data[2].decode("utf8")

        #: The id of the player that controls this unit.
        self.control_pid = data[3]

        #: The id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[4]

        #: The player object that pays upkeep for this one. 0 means neutral unit
        self.unit_upkeeper = None

        #: The player object that controls this unit. 0 means neutral unit
        self.unit_controller = None

        #: The x coordinate of the center of the init unit's footprint. Only 4 point resolution
        #: prior to Starcraft Patch 2.1.
        self.x = data[5]

        #: The y coordinate of the center of the init unit's footprint. Only 4 point resolution
        #: prior to Starcraft Patch 2.1.
        self.y = data[6]

        #: The map location the unit was started at
        self.location = (self.x, self.y)

        if build < 27950:
            self.x = self.x * 4
            self.y = self.y * 4
            self.location = (self.x, self.y)

    def __str__(self):
        return self._str_prefix() + "{0: >15} - Unit initiated {1}".format(
            str(self.unit_upkeeper), self.unit
        )


class UnitDoneEvent(TrackerEvent):
    """
    The counter part to the :class:`UnitInitEvent`, generated by the game engine when an initiated
    unit is completed. E.g. warp-in finished, building finished, morph complete.
    """

    def __init__(self, frames, data, build):
        super(UnitDoneEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the finished unit
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that was finished
        self.unit = None

    def __str__(self):
        return self._str_prefix() + "{0: >15} - Unit {1} done".format(
            str(self.unit.owner), self.unit
        )


class UnitPositionsEvent(TrackerEvent):
    """
    Generated every 15 seconds. Marks the positions of the first 255 units that were damaged in
    the last interval. If more than 255 units were damaged, then the first 255 are reported and
    the remaining units are carried into the next interval.
    """

    def __init__(self, frames, data, build):
        super(UnitPositionsEvent, self).__init__(frames)

        #: The starting unit index point.
        self.first_unit_index = data[0]

        #: An ordered list of unit/point data interpreted as below.
        self.items = data[1]

        #: A dict mapping of units that had their position updated to their positions
        self.units = dict()

        #: A list of (unit_index, (x,y)) derived from the first_unit_index and items. Prior to
        #: Starcraft Patch 2.1 the coordinates have 4 point resolution. (15,25) recorded as (12,24).
        #: Location prior to any rounding marks the center of the unit footprint.
        self.positions = list()

        unit_index = self.first_unit_index
        for i in range(0, len(self.items), 3):
            unit_index += self.items[i]
            x = self.items[i + 1]
            y = self.items[i + 2]
            if build < 27950:
                x = x * 4
                y = y * 4
            self.positions.append((unit_index, (x, y)))

    def __str__(self):
        return self._str_prefix() + "Unit positions update"
