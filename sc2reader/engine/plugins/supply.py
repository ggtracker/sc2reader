# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from collections import defaultdict

class SupplyTracker(object):
    def add_to_units_alive(self,event,replay):
        try: ## see if the unit takes supply
            supplyCount = self.unit_name_to_supply[event.unit_type_name]
            new_unit = (supplyCount, event.unit_id)
            self.units_alive[event.control_pid].append(new_unit)
            total_supply = sum([x[0] for x in self.units_alive[event.control_pid]])
            replay.players[event.control_pid-1].current_food_used[event.second]= total_supply
            print("SECOND",event.second, "Player",replay.players[event.control_pid-1],"SUPPLY",replay.players[event.control_pid-1].current_food_used[event.second])
        except KeyError:
            try: ## see if the unit provides supply
                supply_gen_count = (self.supply_gen_unit[event.unit_type_name])
                supply_gen_unit = (supply_gen_count,event.unit_id)
                self.supply_gen[event.control_pid].append(supply_gen_unit)
                total_supply_gen = sum([x[0] for x in self.units_alive[event.control_pid]])
                replay.players[event.control_pid-1].current_food_made[event.second]= total_supply_gen
            except KeyError:
                print("Unit name {0} does not exist".format(event.unit_type_name))
            return

    def remove_from_units_alive(self,event,replay):
        died_unit_id = event.unit_id
        for player in replay.player:
            dead_unit = filter(lambda x:x[1]==died_unit_id, self.units_alive[player])
            if dead_unit:
                self.units_alive[player].remove(dead_unit[0])
                total_supply = sum([x[0] for x in self.units_alive[player]])
                replay.players[player-1].current_food_used[event.second] = total_supply
                print("Second", event.second, "Killed", event.unit.name,"SUPPLY",replay.players[player-1].current_food_used[event.second])
            
            dead_supply_gen = filter(lambda x:x[1]==died_unit_id, self.supply_gen[player])
            if dead_supply_gen:
                self.supply_gen[player].remove(dead_supply_gen[0])
                total_supply_gen = sum([x[0] for x in self.supply_gen[player]])
                replay.players[player-1].current_food_made[event.second] = total_supply_gen
                print("Second", event.second, "Killed", event.unit.name,"SUPPLY",replay.players[player-1].current_food_made[event.second])

    def handleInitGame(self, event, replay):
        ## This dictionary contains te supply of every unit
        self.unit_name_to_supply = { "Drone":1,"Zergling":1,"Baneling":1,\
                                     "Queen":2,\
                                     "SCV":1,"Marine":1,"Marauder":2,"SiegeTank":2}
        self.supply_gen_unit = {"Overlord":8, "SupplyDepot":8,"Pylon":8}
        ## This list contains a turple of the units supply and unit ID. 
        self.units_alive = dict()
        self.supply_gen = dict()
        for player in replay.players:
            self.supply_gen[player.pid] = list()
            self.units_alive[player.pid] = list()
            player.current_food_used = defaultdict(int)
            player.current_food_made = defaultdict(int)
            player.time_supply_capped = int()

    def handleUnitInitEvent(self,event,replay):
        print ("Init",event.unit_type_name, event.unit_id)
        self.add_to_units_alive(event,replay)

    def handleUnitBornEvent(self,event,replay):
        print ("Born",event.unit_type_name,event.unit_id)
        self.add_to_units_alive(event,replay)

    def handleUnitDiedEvent(self,event,replay):
        if event.unit.name not in self.unit_name_to_supply:
            return
        self.remove_from_units_alive(event,replay)

    def handleEndGame(self, event, replay):
        pass
