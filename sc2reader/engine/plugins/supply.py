# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from collections import defaultdict


class SupplyTracker(object):
    def add_to_units_alive(self, event, replay):
        unit_name = event.unit_type_name
        if unit_name in self.unit_name_to_supply:
            supplyCount = self.unit_name_to_supply[event.unit_type_name][0]
            buildTime = self.unit_name_to_supply[event.unit_type_name][1]
            time_built = event.second - buildTime
            time_built = 0 if time_built < 0 else time_built
            new_unit = (supplyCount, event.unit_id)
            self.units_alive[event.control_pid].append(new_unit)
            total_supply = sum([x[0] for x in self.units_alive[event.control_pid]])
            replay.players[event.control_pid - 1].current_food_used[
                time_built
            ] = total_supply
            print(
                "Second",
                time_built,
                replay.players[event.control_pid - 1],
                "SUPPLY",
                replay.players[event.control_pid - 1].current_food_used[time_built],
            )

        elif unit_name in self.supply_gen_unit:
            ## see if the unit provides supply
            supply_gen_count = self.supply_gen_unit[event.unit_type_name][0]
            build_time = self.supply_gen_unit[event.unit_type_name][1]
            time_complete = event.second + build_time
            supply_gen_unit = (supply_gen_count, event.unit_id)
            self.supply_gen[event.control_pid].append(supply_gen_unit)
            total_supply_gen = sum([x[0] for x in self.supply_gen[event.control_pid]])
            replay.players[event.control_pid - 1].current_food_made[
                time_complete
            ] = total_supply_gen
            print(
                "Second",
                time_complete,
                replay.players[event.control_pid - 1],
                "Built",
                replay.players[event.control_pid - 1].current_food_made[time_complete],
            )
        else:
            print("Unit name {0} does not exist".format(event.unit_type_name))
        return

    def remove_from_units_alive(self, event, replay):
        died_unit_id = event.unit_id
        for player in replay.player:
            dead_unit = filter(lambda x: x[1] == died_unit_id, self.units_alive[player])
            if dead_unit:
                self.units_alive[player].remove(dead_unit[0])
                total_supply = sum([x[0] for x in self.units_alive[player]])

                replay.players[player - 1].current_food_used[
                    event.second
                ] = total_supply
                print(
                    "Second",
                    event.second,
                    "Killed",
                    event.unit.name,
                    "SUPPLY",
                    replay.players[player - 1].current_food_used[event.second],
                )

            dead_supply_gen = filter(
                lambda x: x[1] == died_unit_id, self.supply_gen[player]
            )
            if dead_supply_gen:
                self.supply_gen[player].remove(dead_supply_gen[0])
                total_supply_gen = sum([x[0] for x in self.supply_gen[player]])
                replay.players[player - 1].current_food_made[
                    event.second
                ] = total_supply_gen
                print(
                    "Second",
                    event.second,
                    "Killed",
                    event.unit.name,
                    "SUPPLY",
                    replay.players[player - 1].current_food_made[event.second],
                )

    def handleInitGame(self, event, replay):
        ## This dictionary contains the supply of every unit
        self.unit_name_to_supply = {
            # Zerg
            "Drone": (1, 17),
            "Zergling": (1, 25),
            "Baneling": (0, 20),
            "Queen": (2, 50),
            "Hydralisk": (2, 33),
            "Roach": (2, 27),
            "Infestor": (2, 50),
            "Mutalisk": (2, 33),
            "Corruptor": (2, 40),
            "Utralisk": (6, 55),
            "Broodlord": (2, 34),
            "SwarmHost": (3, 40),
            "Viper": (3, 40),
            # Terran
            "SCV": (1, 17),
            "Marine": (1, 25),
            "Marauder": (2, 30),
            "SiegeTank": (2, 45),
            "Reaper": (1, 45),
            "Ghost": (2, 40),
            "Hellion": (2, 30),
            "Thor": (6, 60),
            "Viking": (2, 42),
            "Medivac": (2, 42),
            "Raven": (2, 60),
            "Banshee": (3, 60),
            "Battlecruiser": (6, 90),
            "Hellbat": (2, 30),
            "WidowMine": (2, 40),
            # Protoss
            "Probe": (1, 17),
            "Zealot": (2, 38),
            "Stalker": (2, 42),
            "Sentry": (2, 42),
            "Observer": (1, 30),
            "Immortal": (4, 55),
            "WarpPrism": (2, 50),
            "Colossus": (6, 75),
            "Phoenix": (2, 35),
            "VoidRay": (4, 60),
            "HighTemplar": (2, 55),
            "DarkTemplar": (2, 55),
            "Archon": (4, 12),
            "Carrier": (6, 120),
            "Mothership": (6, 100),
            "MothershipCore": (2, 30),
            "Oracle": (3, 50),
            "Tempest": (4, 60),
        }

        self.supply_gen_unit = {
            # overlord build time is zero because event for units are made when
            # it is born not when it's created
            "Overlord": (8, 0),
            "Hatchery": (2, 100),
            "SupplyDepot": (8, 30),
            "CommandCenter": (11, 100),
            "Pylon": (8, 25),
            "Nexus": (10, 100),
        }
        ## This list contains a turple of the units supply and unit ID.
        ## the purpose of the list is to know which user owns which unit
        ## so that when a unit dies, that
        self.units_alive = dict()
        ##
        self.supply_gen = dict()
        for player in replay.players:
            self.supply_gen[player.pid] = list()
            self.units_alive[player.pid] = list()
            player.current_food_used = defaultdict(int)
            player.current_food_made = defaultdict(int)
            player.time_supply_capped = int()

    def handleUnitInitEvent(self, event, replay):
        # print ("Init",event.unit_type_name, event.unit_id)
        self.add_to_units_alive(event, replay)

    def handleUnitBornEvent(self, event, replay):
        # print ("Born",event.unit_type_name,event.unit_id)
        self.add_to_units_alive(event, replay)

    def handleUnitDiedEvent(self, event, replay):
        if event.unit.name not in self.unit_name_to_supply:
            return
        self.remove_from_units_alive(event, replay)

    def handleEndGame(self, event, replay):
        for player in replay.players:
            player.current_food_used = sorted(
                player.current_food_used.iteritems(), key=lambda x: x[0]
            )
            player.current_food_made = sorted(
                player.current_food_made.iteritems(), key=lambda x: x[0]
            )
