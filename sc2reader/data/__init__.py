from __future__ import absolute_import

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

unit_file_format = '{}_units.csv'
abil_file_format = '{}_abilities.csv'

ABIL_LOOKUP = dict()
with open(os.path.join(BASE_DIR, 'ability_lookup.csv'), 'r') as data_file:
    for entry in data_file:
        str_id, abilities = entry.split(',',1)
        ABIL_LOOKUP[str_id] = abilities.split(',')

UNIT_LOOKUP = dict()
with open(os.path.join(BASE_DIR, 'unit_lookup.csv'), 'r') as data_file:
    for entry in data_file:
        str_id, title = entry.strip().split(',')
        UNIT_LOOKUP[str_id] = title


# TODO: Costs need to be version stats. Not here
unit_lookup = {'Protoss':{
    'probe':dict(cost=[50,0,1],is_worker=True),
    'zealot':dict(cost=[100,0,2],is_army=True),
    'sentry':dict(cost=[50,100,2],is_army=True),
    'stalker':dict(cost=[125,50,2],is_army=True),
    'hightemplar':dict(cost=[50,150,2],is_army=True),
    'darktemplar':dict(cost=[125,125,2],is_army=True),
    'immortal':dict(cost=[250,100,4],is_army=True),
    'colossus':dict(cost=[300,200,6],is_army=True),
    'archon':dict(cost=[175,275,4],is_army=True), # Can't know the cost, split the difference.
    'observer':dict(cost=[25,75,1],is_army=True),
    'warpprism':dict(cost=[200,0,2],is_army=True),
    'phoenix':dict(cost=[150,100,2],is_army=True),
    'voidray':dict(cost=[250,150,2],is_army=True),
    'tempest':dict(cost=[300,200,4],is_army=True),
    'oracle':dict(cost=[150,150,3],is_army=True),
    'carrier':dict(cost=[350,250,6],is_army=True),
    'mothership':dict(cost=[400,400,6],is_army=True),
    'mothershipcore':dict(cost=[100,100,2],is_army=True),
    #'interceptor':[25,0,0], # This is technically a army unit

    'photoncannon':dict(cost=[150,0,0],is_building=True),
    'nexus':dict(cost=[400,0,0],is_building=True),
    'pylon':dict(cost=[100,0,0],is_building=True),
    'assimilator':dict(cost=[75,0,0],is_building=True),
    'gateway':dict(cost=[150,0,0],is_building=True),
    'warpgate':dict(cost=[150,0,0],is_building=True),
    'forge':dict(cost=[150,0,0],is_building=True),
    'cyberneticscore':dict(cost=[150,0,0],is_building=True),
    'robiticsfacility':dict(cost=[200,100,0],is_building=True),
    'roboticsbay':dict(cost=[200,200,0],is_building=True),
    'twilightcouncil':dict(cost=[150,100,0],is_building=True),
    'darkshrine':dict(cost=[100,250,0],is_building=True),
    'templararchives':dict(cost=[150,200,0],is_building=True),
    'stargate':dict(cost=[150,150,0],is_building=True),
    'fleetbeacon':dict(cost=[300,200,0],is_building=True),


},'Terran':{
    'scv':dict(cost=[50,0,1],is_worker=True),
    'marine':dict(cost=[50,0,1],is_army=True),
    'marauder':dict(cost=[100,25,2],is_army=True),
    'reaper':dict(cost=[50,50,2],is_army=True),
    'ghost':dict(cost=[200,100,2],is_army=True),
    'hellion':dict(cost=[100,0,2],is_army=True),
    'battlehellion':dict(cost=[100,0,2],is_army=True),
    'warhound':dict(cost=[150,75,2],is_army=True),
    'widowmine':dict(cost=[75,25,2],is_army=True),
    'siegetank':dict(cost=[150,125,2],is_army=True),
    'thor':dict(cost=[300,200,6],is_army=True),
    'viking':dict(cost=[150,75,2],is_army=True),
    'medivac':dict(cost=[100,100,2],is_army=True),
    'banshee':dict(cost=[150,100,3],is_army=True),
    'raven':dict(cost=[100,200,2],is_army=True),
    'battlecruiser':dict(cost=[400,300,6],is_army=True),
    'planetaryfortress':dict(cost=[150,150,0],is_building=True),
    'missileturret':dict(cost=[100,0,0],is_building=True),

    'commandcenter':dict(cost=[400,0,0],is_building=True),
    'orbitalcommand':dict(cost=[550,0,0],is_building=True),
    'supplydepot':dict(cost=[100,0,0],is_building=True),
    'refinery':dict(cost=[100,0,0],is_building=True),
    'barracks':dict(cost=[150,0,0],is_building=True),
    'bunker':dict(cost=[100,0,0],is_building=True),
    'engineeringbay':dict(cost=[125,0,0],is_building=True),
    'sensortower':dict(cost=[125,100,0],is_building=True),
    'ghostacademy':dict(cost=[150,50,0],is_building=True),
    'factory':dict(cost=[150,100,0],is_building=True),
    'starport':dict(cost=[150,100,0],is_building=True),
    'fusioncore':dict(cost=[150,150,0],is_building=True),
    'armory':dict(cost=[150,100,0],is_building=True),
    # TODO: tech labs and reactors and flyings?

},'Zerg':{
    # Cumulative costs, including drone costs
    'drone':dict(cost=[50,0,1],is_worker=True),
    'zergling':dict(cost=[25,0,.5],is_army=True),
    'queen':dict(cost=[150,0,2],is_army=True),
    'baneling':dict(cost=[50,25,.5],is_army=True),
    'roach':dict(cost=[75,25,2],is_army=True),
    'overlord':dict(cost=[100,0,0],is_army=True),
    'overseer':dict(cost=[150,50,0],is_army=True),
    'hydralisk':dict(cost=[100,50,2],is_army=True),
    'mutalisk':dict(cost=[100,100,2],is_army=True),
    'viper':dict(cost=[100,200,3],is_army=True),
    'corruptor':dict(cost=[150,100,2],is_army=True),
    'broodlord':dict(cost=[300,250,4],is_army=True),
    'broodling':dict(cost=[0,0,0],is_army=True),
    'infestor':dict(cost=[100,150,2],is_army=True),
    'infestedterran':dict(cost=[0,0,0],is_army=True),
    'swarmhost':dict(cost=[200,100,3],is_army=True),
    'locust':dict(cost=[0,0,0],is_army=True),
    'ultralisk':dict(cost=[300,200,6],is_army=True),
    'spinecrawler':dict(cost=[150,0,0],is_building=True),
    'sporecrawler':dict(cost=[125,0,0],is_building=True),
    'nydusworm':dict(cost=[100,100,0],is_building=True),

    'hatchery':dict(cost=[350,0,0],is_building=True),
    'lair':dict(cost=[500,100,0],is_building=True),
    'hive':dict(cost=[750,250,0],is_building=True),
    'spawningpool':dict(cost=[250,0,0],is_building=True),
    'banelingnest':dict(cost=[150,50,0],is_building=True),
    'roachwarren':dict(cost=[200,0,0],is_building=True),
    'evolutionchamber':dict(cost=[125,0,0],is_building=True),
    'extractor':dict(cost=[75,0,0],is_building=True),
    'nydusnetwork':dict(cost=[200,200,0],is_building=True),
    'hydraliskden':dict(cost=[150,100,0],is_building=True),
    'infestationpit':dict(cost=[150,100,0],is_building=True),
    'spire':dict(cost=[250,200,0],is_building=True),
    'greaterspire':dict(cost=[350,350,0],is_building=True),
    'creeptumor':dict(cost=[0,0,0],is_building=True),
    'ultraliskcavern':dict(cost=[200,200,0],is_building=True),
}}


# There are known to be duplicate ability names now. Hrm
train_commands = {
    'BuildPointDefenseDrone': ('PointDefenseDrone',0),
    'CalldownMULE': ('MULE',0),
    'BuildCommandCenter': ('CommandCenter',100),
    'BuildSupplyDepot': ('SupplyDepot',30),
    'BuildRefinery': ('Refinery',30),
    'BuildBarracks': ('Barracks',65),
    'BuildEngineeringBay': ('EngineeringBay',35),
    'BuildMissileTurret': ('MissileTurret',25),
    'BuildBunker': ('Bunker',40),
    'BuildSensorTower': ('SensorTower',25),
    'BuildGhostAcademy': ('GhostAcademy',40),
    'BuildFactory': ('Factory',60),
    'BuildStarport': ('Starport',50),
    'BuildArmory': ('Armory',65),
    'BuildFusionCore': ('FusionCore',65),
    'BuildAutoTurret': ('AutoTurret',0),
    'TrainSCV': ('SCV',17),
    'TrainMarine': ('Marine',25),
    'TrainReaper': ('Reaper',45),
    'TrainGhost': ('Ghost',40),
    'TrainMarauder': ('Marauder',30),
    'BuildSiegeTank': ('SiegeTank',45),
    'BuildThor': ('Thor',60),
    'BuildwarHound': ('WarHound',45),
    'BuildWidowMine': ('WidowMine',40),
    'BuildHellion': ('Hellion',30),
    'BuildBattleHellion': ('BattleHellion',30),
    'TrainMedivac': ('Medivac',42),
    'TrainBanshee': ('Banshee',60),
    'TrainRaven': ('Raven',60),
    'TrainBattlecruiser': ('Battlecruiser',90),
    'TrainViking': ('VikingFighter',42),
    'UpgradeToPlanetaryFortress': ('PlanetaryFortress',50),
    'UpgradeToOrbitalCommand': ('OrbitalCommand',35),

    'TrainMothership': ('Mothership',160),
    'TrainMothershipCore': ('MothershipCore',30),
    'BuildNexus': ('Nexus',100),
    'BuildPylon': ('Pylon',25),
    'BuildAssimilator': ('Assimilator',30),
    'BuildGateway': ('Gateway',65),
    'BuildForge': ('Forge',45),
    'BuildFleetBeacon': ('FleetBeacon',60),
    'BuildTwilightCouncil': ('TwilightCouncil',50),
    'BuildPhotonCannon': ('PhotonCannon',40),
    'BuildStargate': ('Stargate',60),
    'BuildTemplarArchive': ('TemplarArchive',50),
    'BuildDarkShrine': ('DarkShrine',100),
    'BuildRoboticsBay': ('RoboticsBay',65),
    'BuildRoboticsFacility': ('RoboticsFacility',65),
    'BuildCyberneticsCore': ('CyberneticsCore',50),
    'TrainZealot': ('Zealot',38),
    'TrainStalker': ('Stalker',42),
    'TrainHighTemplar': ('HighTemplar',55),
    'TrainDarkTemplar': ('DarkTemplar',55),
    'TrainSentry': ('Sentry',37),
    'TrainPhoenix': ('Phoenix',35),
    'TrainTempest': ('Tempest',75),
    'TrainOracle': ('Oracle',60),
    'TrainCarrier': ('Carrier',120),
    'TrainVoidRay': ('VoidRay',60),
    'TrainWarpPrism': ('WarpPrism',50),
    'TrainObserver': ('Observer',30),
    'TrainColossus': ('Colossus',75),
    'TrainImmortal': ('Immortal',55),
    'TrainProbe': ('Probe',17),
    'ArmInterceptor': ('Interceptor',8),
    'WarpInZealot': ('Zealot',28),
    'WarpInStalker': ('Stalker',21.3),
    'WarpInHighTemplar': ('HighTemplar',30),
    'WarpInDarkTemplar': ('DarkTemplar',30),
    'WarpInSentry': ('Sentry',21.3),
    'MorphToWarpGate': ('WarpGate',10),
    'ArchonWarpSelection': ('Archon',12),
    'ArchonWarpTarget': ('Archon',12),
    'SentryHallucinationArchon': ('HallucinatedArchon',0),
    'SentryHallucinationColossus': ('HallucinatedColossus',0),
    'SentryHallucinationHighTemplar': ('HallucinatedHighTemplar',0),
    'SentryHallucinationImmortal': ('HallucinatedImmortal',0),
    'SentryHallucinationPhoenix': ('HallucinatedPhoenix',0),
    'SentryHallucinationProbe': ('HallucinatedProbe',0),
    'SentryHallucinationStalker': ('HallucinatedStalker',0),
    'SentryHallucinationVoidRay': ('HallucinatedVoidRay',0),
    'SentryHallucinationWarpPrism': ('HallucinatedWarpPrism',0),
    'SentryHallucinationZealot': ('HallucinatedZealot',0),
    #'MorphToGateway': 'Gateway' #not safe for now, double counting

    'MorphToBaneling': ('Baneling',20),
    'BuildHatchery': ('Hatchery',100),
    'BuildExtractor': ('Extractor',30),
    'BuildSpawningPool': ('SpawningPool',65),
    'BuildEvolutionChamber': ('EvolutionChamber',35),
    'BuildHydraliskDen': ('HydraliskDen',40),
    'BuildSpire': ('Spire',100),
    'BuildUltraliskCavern': ('UltraliskCavern',65),
    'BuildInfestationPit': ('InfestationPit',50),
    'BuildNydusNetwork': ('NydusNetwork',50),
    'BuildBanelingNest': ('BanelingNest',60),
    'BuildRoachWarren': ('RoachWarren',55),
    'BuildSpineCrawler': ('SpineCrawler',50),
    'BuildSporeCrawler': ('SporeCrawler',30),
    'MorphToLair': ('Lair',80),
    'MorphToHive': ('Hive',100),
    'MorphToGreaterSpire': ('GreaterSpire',100),
    'MorphDrone': ('Drone',17),
    'MorphZergling': ('Zergling',24),
    'MorphOverlord': ('Overlord',25),
    'MorphHydralisk': ('Hydralisk',33),
    'MorphMutalisk': ('Mutalisk',33),
    'MorphUltralisk': ('Ultralisk',55),
    'MorphRoach': ('Roach',27),
    'MorphInfestor': ('Infestor',50),
    'MorphSwarmHost': ('SwarmHost',40),
    'MorphViper': ('Viper',40),
    'MorphCorruptor': ('Corruptor',40),
    'MorphToBroodLord': ('BroodLord',34),
    'MorphToOverseer': ('Overseer',17),
    'TrainQueen': ('Queen',50),
    'QueenBuildCreepTumor': ('CreepTumor',15),
    'BuildNydusCanal': ('NydusCanal',20),
    'OverseerSpawnChangeling': ('Changeling',0),
    'InfestorSpawnInfestedTerran': ('InfestorTerran',5),
}

class Build(object):
    def __init__(self, build_id, units, abilities):
        self.id=build_id
        self.units = units
        self.abilities = abilities

class Unit(object):
    name = 'Unknown Unit'
    type = 0

    def __init__(self, unit_id, flags):
        self.id = unit_id
        self.flags = flags
        self.hallucinated = (flags & 2 == 2)
        self._cmp_val = (self.id << 16) | self.type

    def __str__(self):
        return "{} [{:X}]".format(self.name, self.id)

    def __cmp__(self, other):
        if self._cmp_val == other._cmp_val:
            return 0
        elif  self._cmp_val > other._cmp_val:
            return 1
        else:
            return -1

    def __hash__(self):
        return hash(self._cmp_val)

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
            unit_type = int(int_id,10)
            title = UNIT_LOOKUP[str_id]

            values = dict(cost=[0,0,0], race='Neutral',is_army=False, is_building=False, is_worker=False)
            race, minerals, vespene, supply = "Neutral", 0, 0, 0
            for race in ('Protoss','Terran','Zerg'):
                if title.lower() in unit_lookup[race]:
                    values.update(unit_lookup[race][title.lower()])
                    values['race']=race
                    break

            units[unit_type] = type(title,(Unit,), dict(
                type=unit_type,
                name=title,
                title=title,
                race=values['race'],
                minerals=values['cost'][0],
                vespene=values['cost'][1],
                supply=values['cost'][2],
                is_building=values['is_building'],
                is_worker=values['is_worker'],
                is_army=values['is_army'],
            ))

    # TODO: Should RightClick be in the main data files?
    abilities = {0:type('RightClick',(Ability,), dict(type=0, name='RightClick', title='Right Click', is_build=False, build_time=None, build_unit=None))}
    with open(abil_file, 'r') as data_file:
        for entry in data_file:
            int_id_base, str_id = entry.strip().split(',')
            int_id_base = int(int_id_base,10) << 5

            abils = ABIL_LOOKUP[str_id] # The entry must exist
            real_abils = [(int_id_base|i,abil) for i,abil in enumerate(abils) if abil.strip()!='']

            if len(real_abils) == 0:
                # TODO: Should we issue a warning?
                # A: We'd have to fill in all the blanks, probably not worth it
                abilities[int_id_base] = type(str_id,(Ability,), dict(
                        type=int_id_base,
                        name=str_id,
                        title=str_id,
                        is_build=False,
                        build_time=None,
                        build_unit=None
                    ))

            else:
                for index, ability in real_abils:
                    int_id = int_id_base | index
                    abilities[int_id] = type(ability,(Ability,), dict(
                            type=int_id,
                            name=ability,
                            title=ability,
                            is_build=False,
                            build_time=None,
                            build_unit=None
                        ))

    data = Build(version, units, abilities)
    for unit in units.values():
        setattr(data, unit.name, unit)
    for ability in abilities.values():
        if ability.name in train_commands:
            unit_name, build_time = train_commands[ability.name]
            # Side affect of using the same ability lookup for all versions
            # BuildBattleHellion will register for all versions because if FactoryTrain
            # This shouldn't hurt though because the ability can't actually be used
            # and will never be looked up in the ability dictionary.
            if hasattr(data,unit_name):
                ability.is_build = True
                ability.build_time = build_time
                ability.build_unit = getattr(data,unit_name)
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
