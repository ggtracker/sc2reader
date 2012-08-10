from __future__ import absolute_import

#from sc2reader.data.utils import DataObject
#from sc2reader.data.build16561 import Data_16561
#from sc2reader.data.build17326 import Data_17326
#from sc2reader.data.build18317 import Data_18317
#from sc2reader.data.build19595 import Data_19595


from collections import namedtuple
Build = namedtuple('Build',['id','units','abilities'])
UnitRow = namedtuple('UnitRow',['id','type','title'])
AbilRow = namedtuple('AbilRow',['id','type','title'])

from os import path
BASE_PATH = path.dirname(path.abspath(__file__))


unit_lookup = {'Protoss':{
    'probe':[50,0,1],
    'zealot':[100,0,2],
    'sentry':[50,100,2],
    'stalker':[125,50,2],
    'hightemplar':[50,150,2],
    'darktemplar':[125,125,2],
    'immortal':[250,100,4],
    'colossus':[300,200,6],
    'archon':[175,275,4], # Can't know the cost, split the difference.
    'observer':[25,75,1],
    'warpprism':[200,0,2],
    'phoenix':[150,100,2],
    'voidray':[250,150,2],
    'carrier':[350,250,6],
    'mothership':[400,400,6],
    'photoncannon':[150,0,0],
    #'interceptor':[25,0,0], # This is technically a army unit

    'nexus':[400,0,0],
    'pylon':[100,0,0],
    'assimilator':[75,0,0],
    'gateway':[150,0,0],
    'warpgate':[150,0,0],
    'forge':[150,0,0],
    'cyberneticscore':[150,0,0],
    'robiticsfacility':[200,100,0],
    'roboticsbay':[200,200,0],
    'twilightcouncil':[150,100,0],
    'darkshrine':[100,250,0],
    'templararchives':[150,200,0],
    'stargate':[150,150,0],
    'fleetbeacon':[300,200,0],


},'Terran':{
    'scv':[50,0,1],
    'marine':[50,0,1],
    'marauder':[100,25,2],
    'reaper':[50,50,2],
    'ghost':[200,100,2],
    'hellion':[100,0,2],
    'siegetank':[150,125,2],
    'thor':[300,200,6],
    'viking':[150,75,2],
    'medivac':[100,100,2],
    'banshee':[150,100,3],
    'raven':[100,200,2],
    'battlecruiser':[400,300,6],
    'planetaryfortress':[150,150,0],
    'missileturret':[100,0,0],

    'commandcenter':[400,0,0],
    'orbitalcommand':[550,0,0],
    'supplydepot':[100,0,0],
    'refinery':[100,0,0],
    'barracks':[150,0,0],
    'bunker':[100,0,0],
    'engineeringbay':[125,0,0],
    'sensortower':[125,100,0],
    'ghostacademy':[150,50,0],
    'factory':[150,100,0],
    'starport':[150,100,0],
    'fusioncore':[150,150,0],
    'armory':[150,100,0],
    # TODO: tech labs and reactors and flyings!

},'Zerg':{
    # Cumulative costs, including drone costs
    'drone':[50,0,1],
    'zergling':[25,0,.5],
    'queen':[150,0,2],
    'baneling':[50,25,.5],
    'roach':[75,25,2],
    'overlord':[100,0,0],
    'overseer':[150,50,0],
    'hydralisk':[100,50,2],
    'spinecrawler':[150,0,0],
    'sporecrawler':[125,0,0],
    'mutalisk':[100,100,2],
    'corruptor':[150,100,2],
    'broodlord':[300,250,4],
    'broodling':[0,0,0],
    'infestor':[100,150,2],
    'infestedterran':[0,0,0],
    'ultralisk':[300,200,6],
    'nydusworm':[100,100,0],

    'hatchery':[350,0,0],
    'lair':[500,100,0],
    'hive':[750,250,0],
    'spawningpool':[250,0,0],
    'banelingnest':[150,50,0],
    'roachwarren':[200,0,0],
    'evolutionchamber':[125,0,0],
    'extractor':[75,0,0],
    'nydusnetwork':[200,200,0],
    'hydraliskden':[150,100,0],
    'infestationpit':[150,100,0],
    'spire':[250,200,0],
    'greaterspire':[350,350,0],
    'creeptumor':[0,0,0],
    'ultraliskcavern':[200,200,0],
}}

class Unit(object):
	def __init__(self, unit_id):
		self.id = unit_id

class Ability(object):
	pass

def create_build(build):
	units_file = path.join(BASE_PATH, "{}_{}.csv".format(build,"units"))
	abils_file = path.join(BASE_PATH, "{}_{}.csv".format(build,"abilities"))
	with open(units_file, 'r') as data_file:
		units = dict()
		for row in [UnitRow(*line.strip().split(',')) for line in data_file]:
			unit_id = int(row.id, 10) << 8 | 1
			race, minerals, vespene, supply = "Neutral", 0, 0, 0
			for race in ('Protoss','Terran','Zerg'):
				if row.type.lower() in unit_lookup[race]:
					minerals, vespene, supply = unit_lookup[race][row.type.lower()]
					break

			units[unit_id] = type(row.title,(Unit,), dict(
				type=unit_id,
				name=row.title,
				title=row.title,
				race=race,
				minerals=minerals,
				vespene=vespene,
				supply=supply,
			))


	with open(abils_file, 'r') as data_file:
		abilities = {0:type('RightClick',(Ability,), dict(type=0, name='RightClick', title='Right Click'))}
		for row in [line.strip().split(',') for line in data_file]:
			base = int(row[1],10) << 5
			real_abils = [(base|i,t) for i,t in enumerate(row[3:]) if t!='']
			for abil_id, title in real_abils:
				abilities[abil_id] = type(title,(Ability,), dict(
					type=abil_id,
					name=title,
					title=title,
				))

	return  Build(build, units, abilities)

build16117 = create_build(16117)
build17811 = create_build(17811)
build18701 = create_build(18701)
build21029 = create_build(21029)
build22612 = create_build(22612)
