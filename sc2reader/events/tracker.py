# -*- coding: utf-8 -*-
import json
import functools

from sc2reader.utils import Length

clamp = functools.partial(max, 0)

class TrackerEvent(object):
    def __init__(self, frames):
        #: The frame of the game this event was applied
        self.frame = frames

    def load_context(self, replay):
        pass

    def _str_prefix(self):
        return "{0}\t ".format(Length(seconds=int(self.frame/16)))

    def __str__(self):
        return self._str_prefix() + self.name

class PlayerStatsEvent(TrackerEvent):
    """
        Sometimes values in these fields can be negative.
        Clamp them to 0 until this is fixed.

        An additional stats event is sent the frame that a player leaves.
        That player still gets normal stats events for the rest of the game though.
    """
    name = 'PlayerStatsEvent'

    def __init__(self, frames, data):
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
        self.minerals_used_in_progress = self.minerals_used_in_progress_army + self.minerals_used_in_progress_economy + self.minerals_used_in_progress_technology

        #: The total vespene cost of army units (buildings?) currently being built/queued
        self.vespene_used_in_progress_army = clamp(self.stats[8])

        #: The total vespene cost of economy units (buildings?) currently being built/queued.
        self.vespene_used_in_progress_economy = clamp(self.stats[9])

        #: The total vespene cost of technology research (buildings?) currently being built/queued.
        self.vespene_used_in_progress_technology = clamp(self.stats[10])

        #: The total vespene cost of all things in progress
        self.vespene_used_in_progress = self.vespene_used_in_progress_army + self.vespene_used_in_progress_economy + self.vespene_used_in_progress_technology

        #: The total cost of all things in progress
        self.resources_used_in_progress = self.minerals_used_in_progress + self.vespene_used_in_progress

        #: The total mineral cost of current army units (buildings?)
        self.minerals_used_current_army = clamp(self.stats[11])

        #: The total mineral cost of current economy units (buildings?)
        self.minerals_used_current_economy = clamp(self.stats[12])

        #: The total mineral cost of current technology research (buildings?)
        self.minerals_used_current_technology = clamp(self.stats[13])

        #: The total mineral cost of all current things
        self.minerals_used_current = self.minerals_used_current_army + self.minerals_used_current_economy + self.minerals_used_current_technology

        #: The total vespene cost of current army units (buildings?)
        self.vespene_used_current_army = clamp(self.stats[14])

        #: The total vespene cost of current economy units (buildings?)
        self.vespene_used_current_economy = clamp(self.stats[15])

        #: The total vespene cost of current technology research (buildings?)
        self.vespene_used_current_technology = clamp(self.stats[16])

        #: The total vepsene cost of all current things
        self.vespene_used_current = self.vespene_used_current_army + self.vespene_used_current_economy + self.vespene_used_current_technology

        #: The total cost of all things current
        self.resources_used_current = self.minerals_used_current + self.vespene_used_current

        #: The total mineral cost of all army units (buildings?) lost
        self.minerals_lost_army = clamp(self.stats[17])

        #: The total mineral cost of all economy units (buildings?) lost
        self.minerals_lost_economy = clamp(self.stats[18])

        #: The total mineral cost of all technology research (buildings?) lost
        self.minerals_lost_technology = clamp(self.stats[19])

        #: The total mineral cost of all lost things
        self.minerals_lost = self.minerals_lost_army + self.minerals_lost_economy + self.minerals_lost_technology

        #: The total vespene cost of all army units (buildings?) lost
        self.vespene_lost_army = clamp(self.stats[20])

        #: The total vespene cost of all economy units (buildings?) lost
        self.vespene_lost_economy = clamp(self.stats[21])

        #: The total vespene cost of all technology research (buildings?) lost
        self.vespene_lost_technology = clamp(self.stats[22])

        #: The total vepsene cost of all lost things
        self.vespene_lost = self.vespene_lost_army + self.vespene_lost_economy + self.vespene_lost_technology

        #: The total resource cost of all lost things
        self.resources_lost = self.minerals_lost + self.vespene_lost

        #: The total mineral value of enemy army units (buildings?) killed
        self.minerals_killed_army = clamp(self.stats[23])

        #: The total mineral value of enemy economy units (buildings?) killed
        self.minerals_killed_economy = clamp(self.stats[24])

        #: The total mineral value of enemy technology research (buildings?) killed
        self.minerals_killed_technology = clamp(self.stats[25])

        #: The total mineral value of all killed things
        self.minerals_killed = self.minerals_killed_army + self.minerals_killed_economy + self.minerals_killed_technology

        #: The total vespene value of enemy army units (buildings?) killed
        self.vespene_killed_army = clamp(self.stats[26])

        #: The total vespene value of enemy economy units (buildings?) killed
        self.vespene_killed_economy = clamp(self.stats[27])

        #: The total vespene value of enemy technology research (buildings?) killed
        self.vespene_killed_technology = clamp(self.stats[28])

        #: The total vespene cost of all killed things
        self.vespene_killed = self.vespene_killed_army + self.vespene_killed_economy + self.vespene_killed_technology

        #: The total resource cost of all killed things
        self.resources_killed = self.minerals_killed + self.vespene_killed

        #: The food supply currently used
        self.food_used = self.stats[29]

        #: The food supply currently available
        self.food_made = self.stats[30]

        #: The total mineral value of all active forces
        self.minerals_used_active_forces = self.stats[31]

        #: The total vespene value of all active forces
        self.vespene_used_active_forces = self.stats[32]

    def load_context(self, replay):
        self.player = replay.player[self.pid]

    def __str__(self):
        return self._str_prefix()+"{0: >15} - Stats Update".format(self.player)

class UnitBornEvent(TrackerEvent):
    name = 'UnitBornEvent'

    def __init__(self, frames, data):
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
        self.unit_type_name = data[2]

        #: The id of the player that controls this unit.
        self.control_pid = data[3]

        #: The id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[4]

        #: The player object that pays upkeep for this one. 0 means neutral unit
        self.unit_upkeeper = None

        #: The player object that controls this unit. 0 means neutral unit
        self.unit_controller = None

        #: The x coordinate of the location
        self.x = data[5] * 4

        #: The y coordinate of the location
        self.y = data[6] * 4

        #: The map location of the unit birth
        self.location = (self.x, self.y)

    def load_context(self, replay):
        if self.control_pid in replay.player:
            self.unit_controller = replay.player[self.control_pid]
        elif self.control_pid != 0:
            pass#print "Unknown controller pid", self.control_pid

        if self.upkeep_pid in replay.player:
            self.unit_upkeeper = replay.player[self.upkeep_pid]
        elif self.upkeep_pid != 0:
            pass#print "Unknown upkeep pid", self.upkeep_pid

        if self.unit_id in replay.objects:
            # This can happen because game events are done first
            self.unit = replay.objects[self.unit_id]
        else:
            # TODO: How to tell if something is hallucination?
            self.unit = replay.datapack.create_unit(self.unit_id, self.unit_type_name, 0, self.frame)
            replay.objects[self.unit_id] = self.unit

        replay.active_units[self.unit_id_index] = self.unit
        self.unit.location = self.location
        self.unit.started_at = self.frame
        self.unit.finished_at = self.frame

        if self.unit_upkeeper:
            self.unit.owner = self.unit_upkeeper
            self.unit.owner.units.append(self.unit)

    def __str__(self):
        return self._str_prefix()+"{0: >15} - Unit born {1}".format(self.unit_upkeeper,self.unit)

class UnitDiedEvent(TrackerEvent):
    name = 'UnitDiedEvent'

    def __init__(self, frames, data):
        super(UnitDiedEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit being killed
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that died
        self.unit = None

        #: The id of the player that killed this unit. None when not available.
        self.killer_pid = data[2]

        #: The player object of the that killed the unit. Not always available.
        self.killer = None

        #: The x coordinate of the location
        self.x = data[3] * 4

        #: The y coordinate of the location
        self.y = data[4] * 4

        #: The map location the unit was killed at.
        self.location = (self.x, self.y)

    def load_context(self, replay):
        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
            self.unit.died_at = self.frame
            self.unit.location = self.location
            if self.unit_id_index in replay.active_units:
                del replay.active_units[self.unit_id_index]
            else:
                pass#print "Unable to delete unit, not index not active", self.unit_id_index
        else:
            pass#print "Unit died before it was born!"

        if self.killer_pid in replay.player:
            self.killer = replay.player[self.killer_pid]
            if self.unit:
                self.unit.killed_by = self.killer
                self.killer.killed_units.append(self.unit)
        elif self.killer_pid:
            pass#print "Unknown killer pid", self.killer_pid

    def __str__(self):
        return self._str_prefix()+"{0: >15} - Unit died {1}.".format(self.unit.owner, self.unit)


class UnitOwnerChangeEvent(TrackerEvent):
    name = 'UnitOwnerChangeEvent'

    def __init__(self, frames, data):
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

    def load_context(self, replay):
        if self.control_pid in replay.player:
            self.unit_controller = replay.player[self.control_pid]
        elif self.control_pid != 0:
            pass#print "Unknown controller pid", self.control_pid

        if self.upkeep_pid in replay.player:
            self.unit_upkeeper = replay.player[self.upkeep_pid]
        elif self.upkeep_pid != 0:
            pass#print "Unknown upkeep pid", self.upkeep_pid

        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            print "Unit owner changed before it was born!"

        if self.unit_upkeeper:
            if self.unit.owner:
                self.unit.owner.units.remove(self.unit)
            self.unit.owner = self.unit_upkeeper
            self.unit_upkeeper.units.append(self.unit)

    def __str__(self):
        return self._str_prefix()+"{0: >15} took {1}".format(self.unit_upkeeper, self.unit)


class UnitTypeChangeEvent(TrackerEvent):
    name = 'UnitTypeChangeEvent'

    def __init__(self, frames, data):
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
        self.unit_type_name = data[2]

    def load_context(self, replay):
        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
            replay.datapack.change_type(self.unit, self.unit_type_name, self.frame)
        else:
            print "Unit type changed before it was born!"

    def __str__(self):
        return self._str_prefix()+"{0: >15} - Unit {0} type changed to {1}".format(self.unit.owner, self.unit, self.unit_type_name)


class UpgradeCompleteEvent(TrackerEvent):
    name = 'UpgradeCompleteEvent'

    def __init__(self, frames, data):
        super(UpgradeCompleteEvent, self).__init__(frames)

        #: The player that completed the upgrade
        self.pid = data[0]

        #: The Player object that completed the upgrade
        self.player = None

        #: The name of the upgrade
        self.upgrade_type_name = data[1]

        #: The number of times this upgrade as been researched
        self.count = data[2]


    def load_context(self, replay):
        if self.pid in replay.player:
            self.player = replay.player[self.pid]
        else:
            pass#print "Unknown upgrade pid", self.pid
        # TODO: We don't have upgrade -> ability maps
        # TODO: we can probably do the same thing we did for units

    def __str__(self):
        return self._str_prefix()+"{0: >15} - {1}upgrade completed".format(self.player, self.upgrade_type_name)

class UnitInitEvent(TrackerEvent):
    name = 'UnitInitEvent'

    def __init__(self, frames, data):
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
        self.unit_type_name = data[2]

        #: The id of the player that controls this unit.
        self.control_pid = data[3]

        #: The id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[4]

        #: The player object that pays upkeep for this one. 0 means neutral unit
        self.unit_upkeeper = None

        #: The player object that controls this unit. 0 means neutral unit
        self.unit_controller = None

        #: The x coordinate of the location
        self.x = data[5] * 4

        #: The y coordinate of the location
        self.y = data[6] * 4

        #: The map location the unit was started at
        self.location = (self.x, self.y)

    def load_context(self, replay):
        if self.control_pid in replay.player:
            self.unit_controller = replay.player[self.control_pid]
        elif self.control_pid != 0:
            pass#print "Unknown controller pid", self.control_pid

        if self.upkeep_pid in replay.player:
            self.unit_upkeeper = replay.player[self.upkeep_pid]
        elif self.upkeep_pid != 0:
            pass#print "Unknown upkeep pid", self.upkeep_pid

        if self.unit_id in replay.objects:
            # This can happen because game events are done first
            self.unit = replay.objects[self.unit_id]
            if not self.unit.is_type(self.unit_type_name):
                print "CONFLICT {} <-_-> {}".format(self.unit._type_class.str_id, self.unit_type_name)
        else:
            # TODO: How to tell if something is hallucination?
            self.unit = replay.datapack.create_unit(self.unit_id, self.unit_type_name, 0, self.frame)
            replay.objects[self.unit_id] = self.unit

        replay.active_units[self.unit_id_index] = self.unit
        self.unit.location = self.location
        self.unit.started_at = self.frame
        # self.unit.finished_at = self.frame

        if self.unit_upkeeper:
            self.unit.owner = self.unit_upkeeper
            self.unit.owner.units.append(self.unit)

    def __str__(self):
        return self._str_prefix()+"{0: >15} - Unit inititated {1}".format(self.unit_upkeeper, self.unit)


class UnitDoneEvent(TrackerEvent):
    name = 'UnitDoneEvent'

    def __init__(self, frames, data):
        super(UnitDoneEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the finished unit
        self.unit_id = self.unit_id_index << 18 | self.unit_id_recycle

        #: The unit object that was finished
        self.unit = None

    def load_context(self, replay):
        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
            self.unit.finished_at = self.frame
        else:
            print "Unit done before it was started!"

    def __str__(self):
        return self._str_prefix()+"{0: >15} - Unit {1} done".format(self.unit.owner, self.unit)

class UnitPositionsEvent(TrackerEvent):
    name = 'UnitPositionsEvent'

    def __init__(self, frames, data):
        super(UnitPositionsEvent, self).__init__(frames)

        #: The starting unit index point.
        self.first_unit_index = data[0]

        #: An ordered list of unit/point data interpreted as below.
        self.items = data[1]

        #: A dict mapping of units that had their position updated to their positions
        self.units = dict()

        #: A list of (unit_index, (x,y)) derived from the first_unit_index and items
        self.positions = list()

        unit_index = self.first_unit_index
        for i in range(0, len(self.items), 3):
            unit_index += self.items[i]
            x = self.items[i+1]*4
            y = self.items[i+2]*4
            self.positions.append((unit_index, (x,y)))

    def load_context(self, replay):
        for unit_index, (x,y) in self.positions:
            if unit_index in replay.active_units:
                unit = replay.active_units[unit_index]
                unit.location = (x,y)
                self.units[unit] = unit.location
            else:
                print "Unit moved that doesn't exist!"

    def __str__(self):
        return self._str_prefix()+"Unit positions update"
