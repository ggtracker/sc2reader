# -*- coding: utf-8 -*-
import json

class TrackerEvent(object):
    def __init__(self, frames):
        self.frame = frames

    def __str__(self):
        return json.dumps(self.__dict__)

    def load_context(self, replay):
        pass


class PlayerStatsEvent(TrackerEvent):
    name = 'PlayerStatsEvent'

    def __init__(self, frames, data):
        super(PlayerStatsEvent, self).__init__(frames)

        #: Id of the player the stats are for
        self.pid = data[0]

        #: An ordered list of all the available stats
        self.stats = data[1]

        #: Minerals currently available to the player
        self.minerals_current = self.stats[0]

        #: Vespene currently available to the player
        self.vespene_current = self.stats[1]

        #: The rate the player is collecting minerals
        self.minerals_collection_rate = self.stats[2]

        #: The rate the player is collecting vespene
        self.vespene_collection_rate = self.stats[3]

        #: The number of active workers the player has
        self.workers_active_count = self.stats[4]

        #: The total mineral cost of army units (buildings?) currently being built/queued
        self.minerals_used_in_progress_army = self.stats[5]

        #: The total mineral cost of economy units (buildings?) currently being built/queued
        self.minerals_used_in_progress_economy = self.stats[6]

        #: The total mineral cost of technology research (buildings?) currently being built/queued
        self.minerals_used_in_process_technology = self.stats[7]

        #: The total vespene cost of army units (buildings?) currently being built/queued
        self.vespene_used_in_progress_army = self.stats[8]

        #: The total vespene cost of economy units (buildings?) currently being built/queued.
        self.vespene_used_in_progress_economy = self.stats[9]

        #: The total vespene cost of technology research (buildings?) currently being built/queued.
        self.vespene_used_in_progress_technology = self.stats[10]

        #: The total mineral cost of current army units (buildings?)
        self.minerals_used_current_army = self.stats[11]

        #: The total mineral cost of current economy units (buildings?)
        self.minerals_used_current_economy = self.stats[12]

        #: The total mineral cost of current technology research (buildings?)
        self.minerals_used_current_technology = self.stats[13]

        #: The total vespene cost of current army units (buildings?)
        self.vespene_used_current_army = self.stats[14]

        #: The total vespene cost of current economy units (buildings?)
        self.vespene_used_current_economy = self.stats[15]

        #: The total vespene cost of current technology research (buildings?)
        self.vespene_used_current_technology = self.stats[16]

        #: The total mineral cost of all army units (buildings?) lost
        self.minerals_lost_army = self.stats[17]

        #: The total minerals cost of all economy units (buildings?) lost
        self.minerals_lost_economy = self.stats[18]

        #: The total minerals cost of all technology research (buildings?) lost
        self.minerals_lost_technology = self.stats[19]

        #: The total vespene cost of all army units (buildings?) lost
        self.vespene_lost_army = self.stats[20]

        #: The total vespene cost of all economy units (buildings?) lost
        self.vespene_lost_economy = self.stats[21]

        #: The total vespene cost of all technology research (buildings?) lost
        self.vespene_lost_technology = self.stats[22]

        #: The total mineral value of enemy army units (buildings?) killed
        self.minerals_killed_army = self.stats[23]

        #: The total mineral value of enemy economy units (buildings?) killed
        self.minerals_killed_economy = self.stats[24]

        #: The total mineral value of enemy technology research (buildings?) killed
        self.minerals_killed_technology = self.stats[25]

        #: The total vespene value of enemy army units (buildings?) killed
        self.vespene_killed_army = self.stats[26]

        #: The total vespene value of enemy economy units (buildings?) killed
        self.vespene_killed_economy = self.stats[27]

        #: The total vespene value of enemy technology research (buildings?) killed
        self.vespene_killed_technology = self.stats[28]

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


class UnitBornEvent(TrackerEvent):
    name = 'UnitBornEvent'

    def __init__(self, frames, data):
        super(UnitBornEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit being born
        self.unit_id = self.unit_id_index << 16 | self.unit_id_recycle

        #: The unit type name of the unit being born
        self.unit_type_name = data[2]

        #: The id of the player that controls this unit.
        self.control_pid = data[3]

        #: The id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[4]

        #: The x coordinate of the location
        self.x = data[5]

        #: The y coordinate of the location
        self.y = data[6]

        #: The map location of the unit birth
        self.location = (self.x, self.y)

    def load_context(self, replay):
        if self.control_pid: # 0 means neutral unit
            self.unit_controller = replay.player[self.control_pid]

        if self.upkeep_pid: # 0 means neutral unit
            self.unit_upkeeper = replay.player[self.upkeep_pid]

        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            # Create a new unit, but we don't have a type name map yet!
            self.unit = None


class UnitDiedEvent(TrackerEvent):
    name = 'UnitDiedEvent'

    def __init__(self, frames, data):
        super(UnitDiedEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit being killed
        self.unit_id = self.unit_id_index << 16 | self.unit_id_recycle

        #: The id of the player that killed this unit. None when not available.
        self.killer_pid = data[2]

        #: The x coordinate of the location
        self.x = data[3]

        #: The y coordinate of the location
        self.y = data[4]

        #: The map location the unit was killed at.
        self.location = (self.x, self.y)

    def load_context(self, replay):
        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            # Create a new unit, but we don't have a type name map yet!
            self.unit = None

        if self.killer_pid: # This field isn't always available
            self.killer = replay.player[self.killer_pid]


class UnitOwnerChangeEvent(TrackerEvent):
    name = 'UnitOwnerChangeEvent'

    def __init__(self, frames, data):
        super(UnitOwnerChangeEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit changing ownership
        self.unit_id = self.unit_id_index << 16 | self.unit_id_recycle

        #: The new id of the player that controls this unit.
        self.control_pid = data[2]

        #: The new id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[3]


    def load_context(self, replay):
        if self.control_pid: # 0 means neutral unit
            self.unit_controller = replay.player[self.control_pid]

        if self.upkeep_pid: # 0 means neutral unit
            self.unit_upkeeper = replay.player[self.upkeep_pid]

        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            # Create a new unit, but we don't have a type name map yet!
            self.unit = None


class UnitTypeChangeEvent(TrackerEvent):
    name = 'UnitTypeChangeEvent'

    def __init__(self, frames, data):
        super(UnitTypeChangeEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the unit changing type
        self.unit_id = self.unit_id_index << 16 | self.unit_id_recycle

        #: The the new unit type name
        self.unit_type_name = data[2]

    def load_context(self, replay):
        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            # Create a new unit, but we don't have a type name map yet!
            self.unit = None


class UpgradeCompleteEvent(TrackerEvent):
    name = 'UpgradeCompleteEvent'

    def __init__(self, frames, data):
        super(UpgradeCompleteEvent, self).__init__(frames)

        #: The player that completed the upgrade
        self.pid = data[0]

        #: The name of the upgrade
        self.upgrade_type_name = data[1]

        #: The number of times this upgrade as been researched
        self.count = data[2]


    def load_context(self, replay):
        self.player = replay.player[self.pid]
        # TODO: We don't have upgrade -> ability maps


class UnitInitEvent(TrackerEvent):
    name = 'UnitInitEvent'

    def __init__(self, frames, data):
        super(UnitInitEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the stated unit
        self.unit_id = self.unit_id_index << 16 | self.unit_id_recycle

        #: The the new unit type name
        self.unit_type_name = data[2]

        #: The id of the player that controls this unit.
        self.control_pid = data[3]

        #: The id of the player that pays upkeep for this unit.
        self.upkeep_pid = data[4]

        #: The x coordinate of the location
        self.x = data[5]

        #: The y coordinate of the location
        self.y = data[6]

        #: The map location the unit was started at
        self.location = (self.x, self.y)

    def load_context(self, replay):
        if self.control_pid: # 0 means neutral unit
            self.unit_controller = replay.player[self.control_pid]

        if self.upkeep_pid: # 0 means neutral unit
            self.unit_upkeeper = replay.player[self.upkeep_pid]

        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            # Create a new unit, but we don't have a type name map yet!
            self.unit = None


class UnitDoneEvent(TrackerEvent):
    name = 'UnitDoneEvent'

    def __init__(self, frames, data):
        super(UnitDoneEvent, self).__init__(frames)

        #: The index portion of the unit id
        self.unit_id_index = data[0]

        #: The recycle portion of the unit id
        self.unit_id_recycle = data[1]

        #: The unique id of the finished unit
        self.unit_id = self.unit_id_index << 16 | self.unit_id_recycle

    def load_context(self, replay):
        if self.unit_id in replay.objects:
            self.unit = replay.objects[self.unit_id]
        else:
            # Create a new unit, but we don't have a type name map yet!
            self.unit = None


class UnitPositionsEvent(TrackerEvent):
    name = 'UnitPositionsEvent'

    def __init__(self, frames, data):
        super(UnitPositionsEvent, self).__init__(frames)

        #: ???
        self.first_unit_index = data[0]

        #: ???
        self.items = data[1]

        """ We need to be able to find units without the recycle id, can't do this yet!
        unitTagIndex = event['m_firstUnitIndex']
        for i in xrange(len(event['m_items']) / 3):
            unitTagIndex += event['m_items'][i * 3 + 0]
            x = event['m_items'][i * 3 + 1] * 4
            y = event['m_items'][i * 3 + 2] * 4
            # the unit with unitTagIndex is now at coordinate (x, y)
        """
