from __future__ import absolute_import

import pkgutil

class Build(object):
    def __init__(self, build_id, units, abilities):
        self.id=build_id
        self.units = units
        self.abilities = abilities

from collections import namedtuple
UnitRow = namedtuple('UnitRow',['id','type','title'])
AbilRow = namedtuple('AbilRow',['id','type','title'])

from os import path
BASE_PATH = path.dirname(path.abspath(__file__))


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
    'carrier':dict(cost=[350,250,6],is_army=True),
    'mothership':dict(cost=[400,400,6],is_army=True),
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
    # TODO: tech labs and reactors and flyings!

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
    'corruptor':dict(cost=[150,100,2],is_army=True),
    'broodlord':dict(cost=[300,250,4],is_army=True),
    'broodling':dict(cost=[0,0,0],is_army=True),
    'infestor':dict(cost=[100,150,2],is_army=True),
    'infestedterran':dict(cost=[0,0,0],is_army=True),
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
    'RavenBuildPointDefenseDrone': ('PointDefenseDrone',0),
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
    'RavenBuildAutoTurret': ('AutoTurret',0),
    'TrainSCV': ('SCV',17),
    'TrainMarine': ('Marine',25),
    'TrainReaper': ('Reaper',45),
    'TrainGhost': ('Ghost',40),
    'TrainMarauder': ('Marauder',30),
    'TrainSiegeTank': ('SiegeTank',45),
    'TrainThor': ('Thor',60),
    'TrainHellion': ('Hellion',30),
    'TrainMedivac': ('Medivac',42),
    'TrainBanshee': ('Banshee',60),
    'TrainRaven': ('Raven',60),
    'TrainBattlecruiser': ('Battlecruiser',90),
    'TrainViking': ('Viking',42),
    'MorphToPlanetaryFortress': ('PlanetaryFortress',50),
    'MorphToOrbitalCommand': ('OrbitalCommand',35),

    'TrainMothership': ('Mothership',160),
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
    'MergeArchon': ('Archon',12),
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
    'TrainDrone': ('Drone',17),
    'TrainZergling': ('Zergling',24),
    'TrainOverlord': ('Overlord',25),
    'TrainHydralisk': ('Hydralisk',33),
    'TrainMutalisk': ('Mutalisk',33),
    'TrainUltralisk': ('Ultralisk',55),
    'TrainRoach': ('Roach',27),
    'TrainInfestor': ('Infestor',50),
    'TrainCorruptor': ('Corruptor',40),
    'MorphToBroodLord': ('BroodLord',34),
    'MorphToOverseer': ('Overseer',17),
    'TrainQueen': ('Queen',50),
    'QueenBuildCreepTumor': ('CreepTumor',15),
    'BuildNydusCanal': ('NydusCanal',20),
    'OverseerSpawnChangeling': ('Changeling',0),
    'InfestorSpawnInfestedTerran': ('InfestorTerran',5),
}

class Unit(object):
    name = 'Unknown Unit'

    def __init__(self, unit_id):
        self.id = unit_id

    def __str__(self):
        return "{} [{:X}]".format(self.name, self.id)

    def __repr__(self):
        return str(self)

class Ability(object):
    pass


def create_build(build):
    units = dict()
    units_file = "{0}_{1}.csv".format(build,"units")
    units_data = pkgutil.get_data('sc2reader.data',units_file).split('\n')[:-1]
    for row in [UnitRow(*line.strip().split('|')[1:]) for line in units_data]:
        unit_id = int(row.id, 10) << 8 | 1
        values = dict(cost=[0,0,0], race='Neutral',is_army=False, is_building=False, is_worker=False)
        race, minerals, vespene, supply = "Neutral", 0, 0, 0
        for race in ('Protoss','Terran','Zerg'):
            if row.type.lower() in unit_lookup[race]:
                values.update(unit_lookup[race][row.type.lower()])
                values['race']=race
                break

        units[unit_id] = type(row.title,(Unit,), dict(
            type=unit_id,
            name=row.title,
            title=row.title,
            race=values['race'],
            minerals=values['cost'][0],
            vespene=values['cost'][1],
            supply=values['cost'][2],
            is_building=values['is_building'],
            is_worker=values['is_worker'],
            is_army=values['is_army'],
        ))

        if row.title.lower() in ('probe','zealot','stalker','immortal','phoenix','hightemplar','warpprism','archon','colossus','voidray'):
            units[unit_id+1] = type("Hallucinated"+row.title,(Unit,), dict(
                type=unit_id+1,
                name="Hallucinated"+row.title,
                title="Hallucinated"+row.title,
                race='Protoss',
                minerals=0,
                vespene=0,
                supply=0,
                is_building=False,
                is_army=True,
                is_worker=False,
            ))


    abils_file = "{0}_{1}.csv".format(build,"abilities")
    abils_data = pkgutil.get_data('sc2reader.data',abils_file).split('\n')[:-1]
    abilities = {0:type('RightClick',(Ability,), dict(type=0, name='RightClick', title='Right Click', is_build=False, build_time=None, build_unit=None))}
    for row in [line.strip().split('|') for line in abils_data]:
        base = int(row[1],10) << 5
        if base == 0: continue

        # Temporary Hack here.
        if base == 0xe80:
            real_abils = [(0xe80,"QueueCancel0"), (0xe81,"QueueCancel1")]
        else:
            real_abils = [(base|i,t) for i,t in enumerate(row[3:]) if t.strip()!='']

        for abil_id, title in real_abils:
            abilities[abil_id] = type(title,(Ability,), dict(
                type=abil_id,
                name=title,
                title=title,
                is_build=False,
                build_time=None,
                build_unit=None
            ))


        # Some abilities have missing entries..
        if len(real_abils) == 0:
            abilities[base] = type(row[2],(Ability,), dict(
                type=base,
                name=row[2],
                title=row[2],
                is_build=False,
                build_time=None,
                build_unit=None
            ))

        if int(row[1],10) == 249 and build==22612:
            pass
            #print row
            #print abilities[0x1f20], abilities[0x1f21], abilities[0x1f22], abilities[0x1f23]

    data = Build(build, units, abilities)
    for unit in units.values():
        setattr(data, unit.name, unit)
    for ability in abilities.values():
        if ability.name in train_commands:
            unit_name, build_time = train_commands[ability.name]
            ability.is_build = True
            ability.build_time = build_time
            ability.build_unit = getattr(data,unit_name)

        setattr(data, ability.name, ability)

    return data

# His build numbers don't map at ALL to the first effective
# build number so do the correct range mapping down here.
build16117 = create_build(16939)
build17326 = create_build(17811)
build18092 = create_build(18701)
build19458 = create_build(21029)
build22612 = create_build(22612)
