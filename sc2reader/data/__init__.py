from __future__ import absolute_import

#from sc2reader.data.utils import DataObject
#from sc2reader.data.build16561 import Data_16561
#from sc2reader.data.build17326 import Data_17326
#from sc2reader.data.build18317 import Data_18317
#from sc2reader.data.build19595 import Data_19595

import os

unit_file_format = '{}_units.csv'
abil_file_format = '{}_abilities.csv'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


ABIL_LOOKUP = dict()
with open(os.path.join(BASE_DIR, 'ability_lookup.csv'), 'r') as data_file:
    for entry in data_file:
        str_id, abilities = entry.split(',',1)
        ABIL_LOOKUP[str_id] = abilities.split(',')

UNIT_LOOKUP = dict()
with open(os.path.join(BASE_DIR, 'unit_lookup.csv'), 'r') as data_file:
    for entry in data_file:
        # TODO: Something..
        pass


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

# There are known to be duplicate ability names now. Hrm
train_commands = {
    'RavenBuildPointDefenseDrone': 'PointDefenseDrone',
    'CalldownMULE': 'MULE',
    'BuildCommandCenter': 'CommandCenter',
    'BuildSupplyDepot': 'SupplyDepot',
    'BuildRefinery': 'Refinery',
    'BuildBarracks': 'Barracks',
    'BuildEngineeringBay': 'EngineeringBay',
    'BuildMissileTurret': 'MissileTurret',
    'BuildBunker': 'Bunker',
    'BuildSensorTower': 'SensorTower',
    'BuildGhostAcademy': 'GhostAcademy',
    'BuildFactory': 'Factory',
    'BuildStarport': 'Starport',
    'BuildArmory': 'Armory',
    'BuildFusionCore': 'FusionCore',
    'RavenBuildAutoTurret': 'AutoTurret',
    'TrainSCV': 'SCV',
    'TrainMarine': 'Marine',
    'TrainReaper': 'Reaper',
    'TrainGhost': 'Ghost',
    'TrainMarauder': 'Marauder',
    'TrainSiegeTank': 'SiegeTank',
    'TrainThor': 'Thor',
    'TrainHellion': 'Hellion',
    'TrainMedivac': 'Medivac',
    'TrainBanshee': 'Banshee',
    'TrainRaven': 'Raven',
    'TrainBattlecruiser': 'Battlecruiser',
    'TrainViking': 'VikingFighter',
    'MorphToPlanetaryFortress': 'PlanetaryFortress',
    'MorphToOrbitalCommand': 'OrbitalCommand',

    'TrainMothership': 'Mothership',
    'BuildNexus': 'Nexus',
    'BuildPylon': 'Pylon',
    'BuildAssimilator': 'Assimilator',
    'BuildGateway': 'Gateway',
    'BuildForge': 'Forge',
    'BuildFleetBeacon': 'FleetBeacon',
    'BuildTwilightCouncil': 'TwilightCouncil',
    'BuildPhotonCannon': 'PhotonCannon',
    'BuildStargate': 'Stargate',
    'BuildTemplarArchive': 'TemplarArchive',
    'BuildDarkShrine': 'DarkShrine',
    'BuildRoboticsBay': 'RoboticsBay',
    'BuildRoboticsFacility': 'RoboticsFacility',
    'BuildCyberneticsCore': 'CyberneticsCore',
    'TrainZealot': 'Zealot',
    'TrainStalker': 'Stalker',
    'TrainHighTemplar': 'HighTemplar',
    'TrainDarkTemplar': 'DarkTemplar',
    'TrainSentry': 'Sentry',
    'TrainPhoenix': 'Phoenix',
    'TrainCarrier': 'Carrier',
    'TrainVoidRay': 'VoidRay',
    'TrainWarpPrism': 'WarpPrism',
    'TrainObserver': 'Observer',
    'TrainColossus': 'Colossus',
    'TrainImmortal': 'Immortal',
    'TrainProbe': 'Probe',
    'ArmInterceptor': 'Interceptor',
    'WarpInZealot': 'Zealot',
    'WarpInStalker': 'Stalker',
    'WarpInHighTemplar': 'HighTemplar',
    'WarpInDarkTemplar': 'DarkTemplar',
    'WarpInSentry': 'Sentry',
    'MorphToWarpGate': 'WarpGate',
    'MergeArchon': 'Archon',
    'SentryHallucinationArchon': 'HallucinatedArchon',
    'SentryHallucinationColossus': 'HallucinatedColossus',
    'SentryHallucinationHighTemplar': 'HallucinatedHighTemplar',
    'SentryHallucinationImmortal': 'HallucinatedImmortal',
    'SentryHallucinationPhoenix': 'HallucinatedPhoenix',
    'SentryHallucinationProbe': 'HallucinatedProbe',
    'SentryHallucinationStalker': 'HallucinatedStalker',
    'SentryHallucinationVoidRay': 'HallucinatedVoidRay',
    'SentryHallucinationWarpPrism': 'HallucinatedWarpPrism',
    'SentryHallucinationZealot': 'HallucinatedZealot',
    #'MorphToGateway': 'Gateway' #not safe for now, double counting

    'MorphToBaneling': 'Baneling',
    'BuildHatchery': 'Hatchery',
    'BuildExtractor': 'Extractor',
    'BuildSpawningPool': 'SpawningPool',
    'BuildEvolutionChamber': 'EvolutionChamber',
    'BuildHydraliskDen': 'HydraliskDen',
    'BuildSpire': 'Spire',
    'BuildUltraliskCavern': 'UltraliskCavern',
    'BuildInfestationPit': 'InfestationPit',
    'BuildNydusNetwork': 'NydusNetwork',
    'BuildBanelingNest': 'BanelingNest',
    'BuildRoachWarren': 'RoachWarren',
    'BuildSpineCrawler': 'SpineCrawler',
    'BuildSporeCrawler': 'SporeCrawler',
    'MorphToLair': 'Lair',
    'MorphToHive': 'Hive',
    'MorphToGreaterSpire': 'GreaterSpire',
    'TrainDrone': 'Drone',
    'TrainZergling': 'Zergling',
    'TrainOverlord': 'Overlord',
    'TrainHydralisk': 'Hydralisk',
    'TrainMutalisk': 'Mutalisk',
    'TrainUltralisk': 'Ultralisk',
    'TrainRoach': 'Roach',
    'TrainInfestor': 'Infestor',
    'TrainCorruptor': 'Corruptor',
    'MorphToBroodLord': 'BroodLord',
    'MorphToOverseer': 'Overseer',
    'TrainQueen': 'Queen',
    'QueenBuildCreepTumor': 'CreepTumor',
    'BuildNydusCanal': 'NydusCanal',
    'OverseerSpawnChangeling': 'Changeling',
    'InfestorSpawnInfestedTerran': 'InfestorTerran',
}

class Build(object):
    def __init__(self, build_id, units, abilities):
        self.id=build_id
        self.units = units
        self.abilities = abilities

class Unit(object):
    def __init__(self, unit_id):
        self.id = unit_id

    def __str__(self):
        return "{} [{:X}]".format(self.name, self.id)

    def __repr__(self):
        return str(self)

class Ability(object):
    pass

def load_build(data_dir, version):
    print("Loading build {}".format(version))
    unit_file = os.path.join(data_dir,unit_file_format.format(version))
    abil_file = os.path.join(data_dir,abil_file_format.format(version))

    units = dict()
    with open(unit_file, 'r') as data_file:
        for entry in data_file:
            int_id, str_id = entry.strip().split(',')
            int_id = int(int_id)
            race, minerals, vespene, supply = "Neutral", 0, 0, 0
            for race in ('Protoss','Terran','Zerg'):
                if str_id.lower() in unit_lookup[race]:
                    minerals, vespene, supply = unit_lookup[race][str_id.lower()]
                    break

            units[int_id] = type(str_id,(Unit,), dict(
                type=int_id,
                name=str_id,
                title=str_id,
                race=race,
                minerals=minerals,
                vespene=vespene,
                supply=supply,
            ))

            if str_id.lower() in ('probe','zealot','stalker','immortal','phoenix','hightemplar','warpprism','archon','colossus','voidray'):
                units[int_id+1] = type("Hallucinated"+str_id,(Unit,), dict(
                    type=int_id+1,
                    name="Hallucinated"+str_id,
                    title="Hallucinated"+str_id,
                    race=race,
                    minerals=0,
                    vespene=0,
                    supply=0,
                ))
            # TODO: Finish this up!


    # TODO: Should RightClick be in the main data files?
    abilities = {0:type('RightClick',(Ability,), dict(type=0, name='RightClick', title='Right Click'))}
    with open(abil_file, 'r') as data_file:
        for entry in data_file:
            int_id_base, str_id = entry.strip().split(',')
            int_id_base = int(int_id_base,10) << 5

            abils = ABIL_LOOKUP[str_id] # The entry must exist
            real_abils = [(int_id_base|i,abil) for i,abil in enumerate(abils) if abil.strip()!='']

            if len(real_abils) == 0:
                # TODO: Should we issue a warning?
                abilities[int_id_base] = type(str_id,(Ability,), dict(
                        type=int_id_base,
                        name=str_id,
                        title=str_id
                    ))

            else:
                for index, ability in real_abils:
                    int_id = int_id_base | index
                    abilities[int_id] = type(ability,(Ability,), dict(
                            type=int_id,
                            name=ability,
                            title=ability
                        ))

    data = Build(version, units, abilities)
    for unit in units.values():
        setattr(data, unit.name, unit)
    for ability in abilities.values():
        if ability.name in train_commands:
            ability.is_build = True
            ability.build_unit = getattr(data,train_commands[ability.name])
        setattr(data, ability.name, ability)

    return data




# Load the WoL Data
wol_builds = dict()
data_dir = os.path.join(BASE_DIR, 'WoL')
for version in ('16117','17326','18092','19458','22612'):
    wol_builds[version] = load_build(data_dir, version)
    
# Load HotS Data
hots_builds = dict()
data_dir = os.path.join(BASE_DIR, 'HotS')
for version in ('base',):
    hots_builds[version] = load_build(data_dir, version)

builds = {'WoL':wol_builds,'HotS':hots_builds}

from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint
pprint(builds['HotS'])
# class Build(object):
#     def __init__(self, build_id, units, abilities):
#         self.id=build_id
#         self.units = units
#         self.abilities = abilities

# from collections import namedtuple
# UnitRow = namedtuple('UnitRow',['id','type','title'])
# AbilRow = namedtuple('AbilRow',['id','type','title'])

# from os import path
# BASE_PATH = path.dirname(path.abspath(__file__))


# unit_lookup = {'Protoss':{
#     'probe':dict(cost=[50,0,1],is_worker=True),
#     'zealot':dict(cost=[100,0,2],is_army=True),
#     'sentry':dict(cost=[50,100,2],is_army=True),
#     'stalker':dict(cost=[125,50,2],is_army=True),
#     'hightemplar':dict(cost=[50,150,2],is_army=True),
#     'darktemplar':dict(cost=[125,125,2],is_army=True),
#     'immortal':dict(cost=[250,100,4],is_army=True),
#     'colossus':dict(cost=[300,200,6],is_army=True),
#     'archon':dict(cost=[175,275,4],is_army=True), # Can't know the cost, split the difference.
#     'observer':dict(cost=[25,75,1],is_army=True),
#     'warpprism':dict(cost=[200,0,2],is_army=True),
#     'phoenix':dict(cost=[150,100,2],is_army=True),
#     'voidray':dict(cost=[250,150,2],is_army=True),
#     'carrier':dict(cost=[350,250,6],is_army=True),
#     'mothership':dict(cost=[400,400,6],is_army=True),
#     #'interceptor':[25,0,0], # This is technically a army unit

#     'photoncannon':dict(cost=[150,0,0],is_building=True),
#     'nexus':dict(cost=[400,0,0],is_building=True),
#     'pylon':dict(cost=[100,0,0],is_building=True),
#     'assimilator':dict(cost=[75,0,0],is_building=True),
#     'gateway':dict(cost=[150,0,0],is_building=True),
#     'warpgate':dict(cost=[150,0,0],is_building=True),
#     'forge':dict(cost=[150,0,0],is_building=True),
#     'cyberneticscore':dict(cost=[150,0,0],is_building=True),
#     'robiticsfacility':dict(cost=[200,100,0],is_building=True),
#     'roboticsbay':dict(cost=[200,200,0],is_building=True),
#     'twilightcouncil':dict(cost=[150,100,0],is_building=True),
#     'darkshrine':dict(cost=[100,250,0],is_building=True),
#     'templararchives':dict(cost=[150,200,0],is_building=True),
#     'stargate':dict(cost=[150,150,0],is_building=True),
#     'fleetbeacon':dict(cost=[300,200,0],is_building=True),


# },'Terran':{
#     'scv':dict(cost=[50,0,1],is_worker=True),
#     'marine':dict(cost=[50,0,1],is_army=True),
#     'marauder':dict(cost=[100,25,2],is_army=True),
#     'reaper':dict(cost=[50,50,2],is_army=True),
#     'ghost':dict(cost=[200,100,2],is_army=True),
#     'hellion':dict(cost=[100,0,2],is_army=True),
#     'siegetank':dict(cost=[150,125,2],is_army=True),
#     'thor':dict(cost=[300,200,6],is_army=True),
#     'viking':dict(cost=[150,75,2],is_army=True),
#     'medivac':dict(cost=[100,100,2],is_army=True),
#     'banshee':dict(cost=[150,100,3],is_army=True),
#     'raven':dict(cost=[100,200,2],is_army=True),
#     'battlecruiser':dict(cost=[400,300,6],is_army=True),
#     'planetaryfortress':dict(cost=[150,150,0],is_building=True),
#     'missileturret':dict(cost=[100,0,0],is_building=True),

#     'commandcenter':dict(cost=[400,0,0],is_building=True),
#     'orbitalcommand':dict(cost=[550,0,0],is_building=True),
#     'supplydepot':dict(cost=[100,0,0],is_building=True),
#     'refinery':dict(cost=[100,0,0],is_building=True),
#     'barracks':dict(cost=[150,0,0],is_building=True),
#     'bunker':dict(cost=[100,0,0],is_building=True),
#     'engineeringbay':dict(cost=[125,0,0],is_building=True),
#     'sensortower':dict(cost=[125,100,0],is_building=True),
#     'ghostacademy':dict(cost=[150,50,0],is_building=True),
#     'factory':dict(cost=[150,100,0],is_building=True),
#     'starport':dict(cost=[150,100,0],is_building=True),
#     'fusioncore':dict(cost=[150,150,0],is_building=True),
#     'armory':dict(cost=[150,100,0],is_building=True),
#     # TODO: tech labs and reactors and flyings!

# },'Zerg':{
#     # Cumulative costs, including drone costs
#     'drone':dict(cost=[50,0,1],is_worker=True),
#     'zergling':dict(cost=[25,0,.5],is_army=True),
#     'queen':dict(cost=[150,0,2],is_army=True),
#     'baneling':dict(cost=[50,25,.5],is_army=True),
#     'roach':dict(cost=[75,25,2],is_army=True),
#     'overlord':dict(cost=[100,0,0],is_army=True),
#     'overseer':dict(cost=[150,50,0],is_army=True),
#     'hydralisk':dict(cost=[100,50,2],is_army=True),
#     'mutalisk':dict(cost=[100,100,2],is_army=True),
#     'corruptor':dict(cost=[150,100,2],is_army=True),
#     'broodlord':dict(cost=[300,250,4],is_army=True),
#     'broodling':dict(cost=[0,0,0],is_army=True),
#     'infestor':dict(cost=[100,150,2],is_army=True),
#     'infestedterran':dict(cost=[0,0,0],is_army=True),
#     'ultralisk':dict(cost=[300,200,6],is_army=True),
#     'spinecrawler':dict(cost=[150,0,0],is_building=True),
#     'sporecrawler':dict(cost=[125,0,0],is_building=True),
#     'nydusworm':dict(cost=[100,100,0],is_building=True),

#     'hatchery':dict(cost=[350,0,0],is_building=True),
#     'lair':dict(cost=[500,100,0],is_building=True),
#     'hive':dict(cost=[750,250,0],is_building=True),
#     'spawningpool':dict(cost=[250,0,0],is_building=True),
#     'banelingnest':dict(cost=[150,50,0],is_building=True),
#     'roachwarren':dict(cost=[200,0,0],is_building=True),
#     'evolutionchamber':dict(cost=[125,0,0],is_building=True),
#     'extractor':dict(cost=[75,0,0],is_building=True),
#     'nydusnetwork':dict(cost=[200,200,0],is_building=True),
#     'hydraliskden':dict(cost=[150,100,0],is_building=True),
#     'infestationpit':dict(cost=[150,100,0],is_building=True),
#     'spire':dict(cost=[250,200,0],is_building=True),
#     'greaterspire':dict(cost=[350,350,0],is_building=True),
#     'creeptumor':dict(cost=[0,0,0],is_building=True),
#     'ultraliskcavern':dict(cost=[200,200,0],is_building=True),
# }}

# # There are known to be duplicate ability names now. Hrm
# train_commands = {
#     'RavenBuildPointDefenseDrone': ('PointDefenseDrone',0),
#     'CalldownMULE': ('MULE',0),
#     'BuildCommandCenter': ('CommandCenter',100),
#     'BuildSupplyDepot': ('SupplyDepot',30),
#     'BuildRefinery': ('Refinery',30),
#     'BuildBarracks': ('Barracks',65),
#     'BuildEngineeringBay': ('EngineeringBay',35),
#     'BuildMissileTurret': ('MissileTurret',25),
#     'BuildBunker': ('Bunker',40),
#     'BuildSensorTower': ('SensorTower',25),
#     'BuildGhostAcademy': ('GhostAcademy',40),
#     'BuildFactory': ('Factory',60),
#     'BuildStarport': ('Starport',50),
#     'BuildArmory': ('Armory',65),
#     'BuildFusionCore': ('FusionCore',65),
#     'RavenBuildAutoTurret': ('AutoTurret',0),
#     'TrainSCV': ('SCV',17),
#     'TrainMarine': ('Marine',25),
#     'TrainReaper': ('Reaper',45),
#     'TrainGhost': ('Ghost',40),
#     'TrainMarauder': ('Marauder',30),
#     'TrainSiegeTank': ('SiegeTank',45),
#     'TrainThor': ('Thor',60),
#     'TrainHellion': ('Hellion',30),
#     'TrainMedivac': ('Medivac',42),
#     'TrainBanshee': ('Banshee',60),
#     'TrainRaven': ('Raven',60),
#     'TrainBattlecruiser': ('Battlecruiser',90),
#     'TrainViking': ('VikingFighter',42),
#     'MorphToPlanetaryFortress': ('PlanetaryFortress',50),
#     'MorphToOrbitalCommand': ('OrbitalCommand',35),

#     'TrainMothership': ('Mothership',160),
#     'BuildNexus': ('Nexus',100),
#     'BuildPylon': ('Pylon',25),
#     'BuildAssimilator': ('Assimilator',30),
#     'BuildGateway': ('Gateway',65),
#     'BuildForge': ('Forge',45),
#     'BuildFleetBeacon': ('FleetBeacon',60),
#     'BuildTwilightCouncil': ('TwilightCouncil',50),
#     'BuildPhotonCannon': ('PhotonCannon',40),
#     'BuildStargate': ('Stargate',60),
#     'BuildTemplarArchive': ('TemplarArchive',50),
#     'BuildDarkShrine': ('DarkShrine',100),
#     'BuildRoboticsBay': ('RoboticsBay',65),
#     'BuildRoboticsFacility': ('RoboticsFacility',65),
#     'BuildCyberneticsCore': ('CyberneticsCore',50),
#     'TrainZealot': ('Zealot',38),
#     'TrainStalker': ('Stalker',42),
#     'TrainHighTemplar': ('HighTemplar',55),
#     'TrainDarkTemplar': ('DarkTemplar',55),
#     'TrainSentry': ('Sentry',37),
#     'TrainPhoenix': ('Phoenix',35),
#     'TrainCarrier': ('Carrier',120),
#     'TrainVoidRay': ('VoidRay',60),
#     'TrainWarpPrism': ('WarpPrism',50),
#     'TrainObserver': ('Observer',30),
#     'TrainColossus': ('Colossus',75),
#     'TrainImmortal': ('Immortal',55),
#     'TrainProbe': ('Probe',17),
#     'ArmInterceptor': ('Interceptor',8),
#     'WarpInZealot': ('Zealot',28),
#     'WarpInStalker': ('Stalker',21.3),
#     'WarpInHighTemplar': ('HighTemplar',30),
#     'WarpInDarkTemplar': ('DarkTemplar',30),
#     'WarpInSentry': ('Sentry',21.3),
#     'MorphToWarpGate': ('WarpGate',10),
#     'MergeArchon': ('Archon',12),
#     'SentryHallucinationArchon': ('HallucinatedArchon',0),
#     'SentryHallucinationColossus': ('HallucinatedColossus',0),
#     'SentryHallucinationHighTemplar': ('HallucinatedHighTemplar',0),
#     'SentryHallucinationImmortal': ('HallucinatedImmortal',0),
#     'SentryHallucinationPhoenix': ('HallucinatedPhoenix',0),
#     'SentryHallucinationProbe': ('HallucinatedProbe',0),
#     'SentryHallucinationStalker': ('HallucinatedStalker',0),
#     'SentryHallucinationVoidRay': ('HallucinatedVoidRay',0),
#     'SentryHallucinationWarpPrism': ('HallucinatedWarpPrism',0),
#     'SentryHallucinationZealot': ('HallucinatedZealot',0),
#     #'MorphToGateway': 'Gateway' #not safe for now, double counting

#     'MorphToBaneling': ('Baneling',20),
#     'BuildHatchery': ('Hatchery',100),
#     'BuildExtractor': ('Extractor',30),
#     'BuildSpawningPool': ('SpawningPool',65),
#     'BuildEvolutionChamber': ('EvolutionChamber',35),
#     'BuildHydraliskDen': ('HydraliskDen',40),
#     'BuildSpire': ('Spire',100),
#     'BuildUltraliskCavern': ('UltraliskCavern',65),
#     'BuildInfestationPit': ('InfestationPit',50),
#     'BuildNydusNetwork': ('NydusNetwork',50),
#     'BuildBanelingNest': ('BanelingNest',60),
#     'BuildRoachWarren': ('RoachWarren',55),
#     'BuildSpineCrawler': ('SpineCrawler',50),
#     'BuildSporeCrawler': ('SporeCrawler',30),
#     'MorphToLair': ('Lair',80),
#     'MorphToHive': ('Hive',100),
#     'MorphToGreaterSpire': ('GreaterSpire',100),
#     'TrainDrone': ('Drone',17),
#     'TrainZergling': ('Zergling',24),
#     'TrainOverlord': ('Overlord',25),
#     'TrainHydralisk': ('Hydralisk',33),
#     'TrainMutalisk': ('Mutalisk',33),
#     'TrainUltralisk': ('Ultralisk',55),
#     'TrainRoach': ('Roach',27),
#     'TrainInfestor': ('Infestor',50),
#     'TrainCorruptor': ('Corruptor',40),
#     'MorphToBroodLord': ('BroodLord',34),
#     'MorphToOverseer': ('Overseer',17),
#     'TrainQueen': ('Queen',50),
#     'QueenBuildCreepTumor': ('CreepTumor',15),
#     'BuildNydusCanal': ('NydusCanal',20),
#     'OverseerSpawnChangeling': ('Changeling',0),
#     'InfestorSpawnInfestedTerran': ('InfestorTerran',5),
# }

# class Unit(object):
#     name = 'Unknown Unit'

#     def __init__(self, unit_id):
#         self.id = unit_id

#     def __str__(self):
#         return "{} [{:X}]".format(self.name, self.id)

#     def __repr__(self):
#         return str(self)

# class Ability(object):
#     pass

# def create_build(build):
#     units_file = path.join(BASE_PATH, "{}_{}.csv".format(build,"units"))
#     abils_file = path.join(BASE_PATH, "{}_{}.csv".format(build,"abilities"))
#     with open(units_file, 'r') as data_file:
#         units = dict()
#         for row in [UnitRow(*line.strip().split('|')[1:]) for line in data_file]:
#             unit_id = int(row.id, 10) << 8 | 1
#             values = dict(cost=[0,0,0], race='Neutral',is_army=False, is_building=False, is_worker=False)
#             race, minerals, vespene, supply = "Neutral", 0, 0, 0
#             for race in ('Protoss','Terran','Zerg'):
#                 if row.type.lower() in unit_lookup[race]:
#                     values.update(unit_lookup[race][row.type.lower()])
#                     values['race']=race
#                     break

#             units[unit_id] = type(row.title,(Unit,), dict(
#                 type=unit_id,
#                 name=row.title,
#                 title=row.title,
#                 race=values['race'],
#                 minerals=values['cost'][0],
#                 vespene=values['cost'][1],
#                 supply=values['cost'][2],
#                 is_building=values['is_building'],
#                 is_worker=values['is_worker'],
#                 is_army=values['is_army'],
#             ))

#             if row.title.lower() in ('probe','zealot','stalker','immortal','phoenix','hightemplar','warpprism','archon','colossus','voidray'):
#                 units[unit_id+1] = type("Hallucinated"+row.title,(Unit,), dict(
#                     type=unit_id+1,
#                     name="Hallucinated"+row.title,
#                     title="Hallucinated"+row.title,
#                     race='Protoss',
#                     minerals=0,
#                     vespene=0,
#                     supply=0,
#                     is_building=False,
#                     is_army=True,
#                     is_worker=False,
#                 ))


#     with open(abils_file, 'r') as data_file:
#         abilities = {0:type('RightClick',(Ability,), dict(type=0, name='RightClick', title='Right Click', is_build=False, build_time=None, build_unit=None))}
#         for row in [line.strip().split('|') for line in data_file]:
#             base = int(row[1],10) << 5
#             if base == 0: continue

#             # Temporary Hack here.
#             if base == 0xe80:
#                 real_abils = [(0xe80,"QueueCancel0"), (0xe81,"QueueCancel1")]
#             else:
#                 real_abils = [(base|i,t) for i,t in enumerate(row[3:]) if t.strip()!='']

#             for abil_id, title in real_abils:
#                 abilities[abil_id] = type(title,(Ability,), dict(
#                     type=abil_id,
#                     name=title,
#                     title=title,
#                     is_build=False,
#                     build_time=None,
#                     build_unit=None
#                 ))


#             # Some abilities have missing entries..
#             if len(real_abils) == 0:
#                 abilities[base] = type(row[2],(Ability,), dict(
#                     type=base,
#                     name=row[2],
#                     title=row[2],
#                     is_build=False,
#                     build_time=None,
#                     build_unit=None
#                 ))

#             if int(row[1],10) == 249 and build==22612:
#                 pass
#                 #print row
#                 #print abilities[0x1f20], abilities[0x1f21], abilities[0x1f22], abilities[0x1f23]

#     data = Build(build, units, abilities)
#     for unit in units.values():
#         setattr(data, unit.name, unit)
#     for ability in abilities.values():
#         if ability.name in train_commands:
#             unit_name, build_time = train_commands[ability.name]
#             ability.is_build = True
#             ability.build_time = build_time
#             ability.build_unit = getattr(data,unit_name)

#         setattr(data, ability.name, ability)

#     return data

# # His build numbers don't map at ALL to the first effective
# # build number so do the correct range mapping down here.
# build16117 = create_build(16939)
# build17326 = create_build(17811)
# build18092 = create_build(18701)
# build19458 = create_build(21029)
# build22612 = create_build(22612)
