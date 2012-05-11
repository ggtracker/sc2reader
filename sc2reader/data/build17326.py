from __future__ import absolute_import

from sc2reader.data.base import *
from sc2reader.data.utils import *

#Hell, this might even cover 1.3.2 as well. Definitely not 1.3.3 though.
class Data_17326(BaseData):

    class DataObject(DataObject):
        abilities = {
            0x3700: 'Right click',
            0x5700: 'Right click in fog',
        }

    class Moveable(DataObject):
        abilities = {
            0x002400: 'Stop',
            0x002403: 'Stop',
            0x002602: 'Hold position',
            0x002610: 'Move to',
            0x002611: 'Patrol',
            0x002620: 'Follow',
        }

    class Attacker(DataObject):
        abilities = {
            0x002400: 'Stop',   #Attackers can also stop
            0x002602: 'Hold position',
            0x002a10: 'Attack move',
            0x002a20: 'Attack object',
        }

    class Supporter(DataObject):
        abilities = {
            0x002613: 'Scan move', # attack move for units without attack
            0x002623: 'Scan target', # attack move for units without attack
        }

    class Building(DataObject):
        abilities = {
            0x013000: 'Cancel',
        }

    class TerranBuilding(Building):
        abilities = {
            0x013001: 'Halt build',
        }

    class Research(Building):
        abilities = {
            0x012c00: 'Cancel', # Generic ESC cancel
            0x012c31: 'Cancel unit', # Cancel + build id
        }

    class Production(Building):
        abilities = {
            0x011710: 'Set rally point',
            0x011720: 'Set rally target',
            0x012c00: 'Cancel', # Generic ESC cancel
            0x012c31: 'Cancel unit', # Cancel + build id
        }

    class Worker(Moveable, Attacker):
        pass

    class SCV(Worker):
        abilities = {
            0x012820: 'Gather resources',
            0x012801: 'Return cargo',
            0x013100: 'Toggle Auto-Repair',
            0x013120: 'Repair',
            0x01f206: 'Halt',
            0x013210: 'Command Center',
            0x013211: 'Supply Depot',
            0x013213: 'Barracks',
            0x013214: 'Engineering Bay',
            0x013215: 'Missile Turret',
            0x013216: 'Bunker',
            0x013222: 'Refinery',
            0x017210: 'Sensor Tower',
            0x017211: 'Ghost Academy',
            0x017212: 'Factory',
            0x017213: 'Starport',
            0x017215: 'Armory',
            0x017217: 'Fusion Core',
        }

    class MULE(Worker):
        abilities = {
            0x003900: 'Toggle Auto-Repair',
            0x003920: 'Repair',
            0x0: 'Return Cargo',
            0x0: 'Gather',
        }

    class Marine(Moveable, Attacker):
        abilities = {
            0x013400: 'Use Stimpack (mixed)',
        }

    class Marauder(Moveable, Attacker):
        abilities = {
            0x013400: 'Use Stimpack (mixed)',
            0x012100: 'Use Stimpack',
        }

    @Cloaks(0x013500, 0x013501)
    @Channels('Tactical Nuclear Strike',start=0x031f10,cancel=0x031f01)
    class Ghost(Moveable, Attacker):
        abilities = {
            0x003200: 'Hold fire',
            0x003300: 'Weapons free',
            0x032210: 'EMP Round',
            0x013620: 'Sniper Round',
        }

    @Mode('Sieged',('Siege Mode',0x013800,None),('Unsiege',0x013900,None))
    class SiegeTank(Moveable, Attacker):
        pass

    @Channels('250mm Strike Cannons',0x012320,None)
    class Thor(Moveable, Attacker):
        pass

    @Mode('Assault',('Assult Mode',0x013e00,None),('Fighter Mode',0x013f00,None))
    class Viking(Moveable, Attacker):
        pass

    @Transports(0x013b12, 0x013b22, 0x013b33, 0x013b20)
    class Medivac(Moveable, Supporter):
        abilities = {
            0x013700: 'Toggle Auto-Heal',
            0x020803: 'Heal',
        }

    class Raven(Moveable, Supporter):
        abilities = {
            0x033b10: 'Auto Turret',
            0x003e10: 'Point Defense Drone',
            0x010a20: 'Seeker Missile',
        }

    @Cloaks(0x013a00, 0x013a01)
    class Banshee(Moveable, Attacker):
        pass

    class Battlecruiser(Moveable, Attacker):
        abilities = {
            0x013d20: 'Yamato Cannon',
        }

    class TerranMain(TerranBuilding):
        abilities = {
            0x011910: 'Set rally point',
            0x011920: 'Set rally target',
            0x020c00: 'Train SCV',
        }

    @Lifts(0x020200, 0x020310)
    @Transports(0x020101, None, 0x020133, 0x020104)
    class CommandCenter(TerranMain, Production):
        pass

    @Lifts(0x031700, 0x031810)
    @UpgradeFrom(CommandCenter, 0x031400, 0x031401)
    class OrbitalCommand(TerranMain, Production):
        abilities = {
            0x010b10: 'MULE (Target)',
            0x010b20: 'MULE (Location)',
            0x012220: 'Extra Supplies',
            0x013c10: 'Scanner Sweep',
        }

    @UpgradeFrom(CommandCenter, 0x030f00, 0x030f01)
    class PlanetaryFortress(TerranMain, Production):
        abilties = {
            0x012e00: 'Cancel (PF ONLY)', #????
        }

    @Lowers(0x020e00, 0x020f00)
    class SupplyDepot(TerranBuilding):
        pass

    class EngineeringBay(TerranBuilding, Research):
        abilities = {
            0x021300: 'Hi-Sec Auto Tracking',
            0x021301: 'Building Armor',
            0x021302: 'Infantry Weapons Level 1',
            0x021303: 'Infantry Weapons Level 2',
            0x021304: 'Infantry Weapons Level 3',
            0x021305: 'Neosteel Frame',
            0x021306: 'Infantry Armor Level 1',
            0x021307: 'Infantry Armor Level 2',
            0x025300: 'Infantry Armor Level 3',
        }

    class GhostAcademy(TerranBuilding, Research):
        abilities = {
            0x021500: 'Arm silo with Nuke',
            0x021900: 'Personal Cloaking',
            0x021901: 'Moebius Reactor',
        }

    class FusionCore(TerranBuilding, Research):
        abilities = {
            0x031c00: 'Research Yamato Cannon', #Good guess???
        }

    @Transports(0x020001, None, 0x020033, 0x20020)
    class Bunker(TerranBuilding):
        abilities = {
            0x032100: 'Salvage',
            0x033000: 'Stimpack', #Can bunkers really stimpack?
            0x032f20: 'Attack',
            # I don't think these 2 are right....?
            #0x032f20: 'Attack',
            #0x033300: 'Stop'
        }

    class Armory(TerranBuilding, Research):
        abilities = {
            0x021a02: 'Vehicle Plating Level 1',
            0x021a03: 'Vehicle Plating Level 2',
            0x021a04: 'Vehicle Plating Level 3',
            0x021a05: 'Vehicle Weapons Level 1',
            0x021a06: 'Vehicle Weapons Level 2',
            0x021a07: 'Vehicle Weapons Level 3',
            0x025a00: 'Ship Plating Level 1',
            0x025a01: 'Ship Plating Level 2',
            0x025a02: 'Ship Plating Level 3',
            0x025a03: 'Ship Weapons Level 1',
            0x025a04: 'Ship Weapons Level 2',
            0x025a05: 'Ship Weapons Level 3',
        }

    @Lifts(0x020500, 0x020d10)
    @AddOn('Techlab', start=0x020400, move=0x020410, cancel=0x02c406)
    @AddOn('Reactor', start=0x020401, move=0x020411, cancel=0x02c406)
    class Barracks(TerranBuilding, Production):
        abilities = {
            0x021000: 'Marine',
            0x021001: 'Reaper',
            0x021002: 'Ghost',
            0x021003: 'Marauder',
        }

        class Techlab(Research):
            abilities = {
                0x021403: 'Nitro Packs',
                0x021600: 'Stimpack',
                0x021601: 'Combat Shields',
                0x021602: 'Concussive Shells',
                0x012f00: 'Cancel Research',
                0x012f31: 'Cancel specific Research',
            }

        class Reactor(TerranBuilding):
            pass

        @AddOn('Techlab', start=0x020410, move=None, cancel=None)
        @AddOn('Reactor', start=0x020411, move=None, cancel=None)
        class Flying(TerranBuilding, Moveable):
            pass

    @Lifts(0x020700,0x020a10)
    @AddOn('Techlab', start=0x020600, move=0x020610, cancel=0x02c606)
    @AddOn('Reactor', start=0x020601, move=0x020611, cancel=0x02c606)
    class Factory(TerranBuilding, Production):
        abilities = {
            0x021101: 'Siege Tank',
            0x021104: 'Thor',
            0x021105: 'Hellion',
            #Shouldn't this be somewhere else?
            #0x020700: 'Set rally point',
        }

        class Techlab(Research):
            abilities = {
                0x021700: 'Siege Tech',
                0x021701: 'Infernal Pre-igniter',
                0x021702: '250mm Strike Cannons',
                0x012f00: 'Cancel Research',
                0x012f31: 'Cancel specific Research',
            }

        class Reactor(TerranBuilding):

            pass

        @AddOn('Techlab', start=0x020610, move=None, cancel=None)
        @AddOn('Reactor', start=0x020611, move=None, cancel=None)
        class Flying(TerranBuilding, Moveable):
            pass

    @Lifts(0x020900, 0x020b10)
    @AddOn('Techlab', start=0x020800, move=0x020810, cancel=0x02c806)
    @AddOn('Reactor', start=0x020801, move=0x020811, cancel=0x02c806)
    class Starport(TerranBuilding, Production):
        abilities = {
            0x021200: 'Medivac',
            0x021201: 'Banshee',
            0x021202: 'Raven',
            0x021203: 'Battlecruiser',
            0x021204: 'Viking',
        }

        class Techlab(Research):
            abilities = {
                0x021800: 'Cloaking Field',
                0x021802: 'Caduceus Reactor',
                0x021803: 'Corvid Rector',
                0x021806: 'Seeker Missile',
                0x021807: 'Durable Materials',
                0x012f00: 'Cancel Research',
                0x012f31: 'Cancel specific Research',
            }

        class Reactor(TerranBuilding):
            pass

        @AddOn('TechLab', start=0x020810, move=None, cancel=None)
        @AddOn('Reactor', start=0x020811, move=None, cancel=None)
        class Flying(TerranBuilding, Moveable):
            pass

    ###########################
    ## Protoss Units
    ###########################

    class Probe(Worker):
        abilities = {
            0x012901: 'Return cargo',
            0x012920: 'Gather Resources',
            0x021b10: 'Nexus',
            0x021b11: 'Pylon',
            0x021b13: 'Gateway',
            0x021b14: 'Forge',
            0x021b15: 'Fleet Beacon',
            0x021b16: 'Twilight Council',
            0x021b17: 'Photon Cannon',
            0x021b22: 'Assimilator',
            0x025b11: 'Stargate',
            0x025b12: 'Templar Archives',
            0x025b13: 'Dark Shrine',
            0x025b14: 'Robotics Bay',
            0x025b15: 'Robotics Facility',
            0x025b16: 'Cybernetics Core',
        }

    class Stalker(Moveable, Attacker):
        abilities = {
            0x030b10: 'Blink',
        }

    class Sentry(Moveable, Attacker):
        abilities = {
            0x003f00: 'Hallucinate Archon',
            0x010000: 'Hallucinate Colossus',
            0x010100: 'Hallucinate High Templar',
            0x010200: 'Hallucinate Immortal',
            0x010300: 'Hallucinate Phoenix',
            0x010400: 'Hallucinate Probe',
            0x010500: 'Hallucinate Stalker',
            0x010600: 'Hallucinate Void Ray',
            0x010700: 'Hallucinate Warp Prism',
            0x010800: 'Hallucinate Zealot',
            0x003800: 'Guardian Shield',
            0x031910: 'Force Field',
        }

    class HighTemplar(Moveable, Supporter):
        abilities = {
            0x022110: 'Psionic Storm',
            0x003c20: 'Feedback',
        }

    class DarkTemplar(Moveable, Attacker):
        pass

    @MergeFrom([HighTemplar, DarkTemplar], 0x033c00, None)
    class Archon(Moveable, Attacker):
        pass

    @Mode('Phasing', ('Phase Mode', 0x031a00, None), ('Transport Mode', 0x031b00, None))
    @Transports(0x021c12, 0x021c22, 0x021c33, 0x021c20)
    class WarpPrism(Moveable, Supporter):
        pass

    @Channels('Graviton Beam', 0x010c20, 0x010c01)
    class Pheonix(Moveable, Attacker):
        pass

    class Carrier(Moveable, Attacker):
        abilities = {
            0x022400: 'Build Intercepter',
        }

    class Mothership(Moveable, Attacker):
        abilities = {
            0x032310: 'Vortex',
            0x003d10: 'Mass Recall',
        }

    class Nexus(Production):
        abilities = {
            0x022000: 'Probe',
            0x003b00: 'Mothership',
            0x012520: 'Chrono Boost',
            0x011a10: 'Set rally point',
            0x011a20: 'Set rally target',
        }

    @Mode('WarpGate', ('Tranform to Warpgate',0x031500, None), ('Transform to Gateway', 0x031600, None))
    class Gateway(Production):
        abilities = {
            0x021d00: 'Train Zealot',
            0x021d01: 'Train Stalker',
            0x021d03: 'Train High Templar',
            0x021d04: 'Train Dark Templar',
            0x021d05: 'Train Sentry',
        }

        class WarpGate(Building):
            abilities = {
                0x030710: 'Warp in Zealot',
                0x030711: 'Warp in Stalker',
                0x030713: 'Warp in High Templar',
                0x030714: 'Warp in Dark Templar',
                0x030715: 'Warp in Sentry',
            }

    class Forge(Research):
        abilities = {
            0x022500: 'Ground Weapons Level 1',
            0x022501: 'Ground Weapons Level 2',
            0x022502: 'Ground Weapons Level 3',
            0x022503: 'Ground Armor Level 1',
            0x022504: 'Ground Armor Level 2',
            0x022505: 'Ground Armor Level 3',
            0x022506: 'Shield Level 1',
            0x022507: 'Shield Level 2',
            0x026500: 'Shield Level 3',
        }

    class CyberneticsCore(Research):
        abilities = {
            0x031d00: 'Air Weapons Level 1',
            0x031d01: 'Air Weapons Level 2',
            0x031d02: 'Air Weapons Level 3',
            0x031d03: 'Air Armor Level 1',
            0x031d04: 'Air Armor Level 2',
            0x031d05: 'Air Armor Level 3',
            0x031d06: 'Warp Gate',
            0x035d01: 'Hallucination',
        }

    class RoboticsFacility(Production):
        abilities = {
            0x021f00: 'Warp Prism',
            0x021f01: 'Observer',
            0x021f02: 'Colossus',
            0x021f03: 'Immortal',
        }

    class Stargate(Production):
        abilities = {
            0x021e00: 'Phoenix',
            0x021e02: 'Carrier',
            0x021e04: 'Void Ray',
        }

    class TwilightCouncil(Research):
        abilities = {
            0x031e00: 'Charge',
            0x031e01: 'Blink',
        }

    class FleetBeacon(Research):
        abilities = {
            0x003601: 'Graviton Catapult'
        }

    class TemplarArchive(Research):
        abilities = {
            0x022700: 'Khaydarin Amulet',
            0x022704: 'Psionic Storm',
        }

    class RoboticsBay(Research):
        abilities = {
            0x022601: 'Gravitic Booster',
            0x022602: 'Gravitic Drive',
            0x022605: 'Extended Thermal Lance',
        }

    #####################
    ## Zerg
    #####################

    class Larva(DataObject):
        abilities = {
            0x023200: 'Drone',
            0x023201: 'Zergling',
            0x023202: 'Overlord',
            0x023203: 'Hydralisk',
            0x023204: 'Mutalisk',
            0x023206: 'Ultralisk',
            0x027201: 'Roach',
            0x027202: 'Infestor',
            0x027203: 'Corruptor',
        }

    class Egg(Supporter):
        abilities = {
            0x0012b00: 'Cancel',
        }

    @Burrows(0x023600, 0x023700)
    class Drone(Worker):
        abilities = {
            0x022920: 'Gather Resources (Zerg)',
            0x022901: 'Return cargo',
            0x023600: 'Burrow',
            0x022810: 'Hatchery',
            0x022813: 'Spawning Pool',
            0x022814: 'Evolution Chamber',
            0x022815: 'Hydralisk Den',
            0x022816: 'Spire',
            0x022817: 'Ultralisk Cavern',
            0x022822: 'Extractor',
            0x026810: 'Infestation Pit',
            0x026811: 'Nydus Network',
            0x026812: 'Baneling Nest',
            0x026815: 'Roach Warren',
            0x026816: 'Spine Crawler',
            0x026817: 'Spore Crawler',
        }

    @Burrows(0x030800, 0x030900)
    class Queen(Moveable, Attacker):
        abilities = {
            0x033510: 'Creep Tumor',
            0x012020: 'Larva',
            0x032620: 'Transfuse',
        }

    @Burrows(0x023c00, 0x023d00)
    class Zergling(Moveable, Attacker):
        pass

    @MorphedFrom(Zergling, 0x003a00, 0x012b00)
    @Burrows(0x023400, 0x023500)
    class Baneling(Moveable, Attacker):
        abilities = {
            0x003500: 'Explode',
            0x011d00: 'Attack Structure',
            0x0: 'Enable Building Attack',
            0x0: 'Disable Building Attack',
        }

    @Burrows(0x023a00, 0x023b00)
    class Roach(Moveable, Attacker):
        pass

    @Burrows(0x023800, 0x023900)
    class Hydralisk(Moveable, Attacker):
        pass

    @Burrows(0x030c00, 0x030d00)
    @Channels('Neural Parasite', 0x011f20, None)
    class Infestor(Moveable, Supporter):
        abilities = {
            0x003710: 'Fungal Growth',
            0x011e10: 'Infested Terran',
        }

        class Burrowed(Moveable, Supporter):
            abilities = {
                0x011e10: 'Infested Terran',
            }

    @Burrows(0x031200, 0x031300)
    class Ultralisk(Moveable, Attacker):
        pass

    @Burrows(None, None)
    class InfestedTerran(Moveable, Attacker):
        pass

    class Corruptor(Moveable, Attacker):
        abilities = {
            0x003120: 'Corruption',
        }

    @MorphedFrom(Corruptor, 0x023300, 0x023301)
    class Broodlord(Moveable, Attacker):
        pass

    @Transports(0x030412, 0x030422, 0x030433, 0x030404)
    class Overlord(Moveable, Supporter):
        abilities = {
            0x033400: 'Generate Creep',
            0x033401: 'Stop generating Creep',
            0x030401: 'Unload all at',
        }

    @MorphedFrom(Overlord, 0x030e00, 0x030e01)
    class Overseer(Zerg, Moveable, Supporter):
        abilities = {
            0x011000: 'Changeling',
            0x040320: 'Contaminate',
        }

    @Transports(0x030a01, None, 0x030a33, 0x030a20)
    class NydusWorm(Building):
        pass

    @Uproots(0x033600, 0x033810, 0x33901)
    class SpineCrawler(Building, Attacker):
        pass

    @Uproots(0x033700, 0x033910, 0x033901)
    class SporeCrawler(Building, Attacker):
        pass

    class ZergMain(Production, Research):
        abilities = {
            0x011b11: 'Set worker rally point',
            0x011b21: 'Set worker rally target',
            0x011b10: 'Set unit rally point',
            0x011b20: 'Set unit rally target',
            0x032400: 'Queen',
            0x022e03: 'Evolve Burrow',
            0x022e01: 'Evolve Pneumatized Carapace',
            0x022e02: 'Evolve Ventral Sacs',
        }

    class Hatchery(ZergMain):
        pass

    @UpgradeFrom(Hatchery,0x022b00, 0x022b01)
    class Lair(ZergMain):
        pass

    @UpgradeFrom(Lair, 0x022c00, 0x022c01)
    class Hive(ZergMain):
        pass

    class SpawningPool(Research):
        abilities = {
            0x022f00: 'Evolve Adrenal Glands',
            0x022f01: 'Evolve Metabolic Boost',
        }

    class EvolutionChamber(Research):
        abilities = {
            0x022a00: 'Evolve Melee Attacks Level 1',
            0x022a01: 'Evolve Melee Attacks Level 2',
            0x022a02: 'Evolve Melee Attacks Level 3',
            0x022a03: 'Evolve Ground Carapace Level 1',
            0x022a04: 'Evolve Ground Carapace Level 2',
            0x022a05: 'Evolve Ground Carapace Level 3',
            0x022a06: 'Evolve Missile Attacks Level 1',
            0x022a07: 'Evolve Missile Attacks Level 2',
            0x026a00: 'Evolve Missile Attacks Level 3',
        }

    class RoachWarren(Research):
        abilities = {
            0x011c01: 'Evolve Glial Reconstitution',
            0x011c02: 'Evolve Tunneling Claws',
        }

    class BanelingNest(Research):
        abilities = {
            0x031100: 'Evolve Centrifugal Hooks',
        }

    @Channels('Creep Tumor', 0x033a10, 0x3fa06)
    class CreepTumorBurrowed(Building):
        pass

    class HydraliskDen(Research):
        abilities = {
            0x023002: 'Evolve Grooved Spines',
        }

    class InfestationPit(Research):
        abilities = {
            0x031002: 'Evolve Pathogen Glands',
            0x031003: 'Evolve Neural Parasite',
        }

    @Transports(0x030a01, None, 0x030a33, 0x030a20)
    class NydusNetwork(Building):
        abilities = {
            0x033d10: 'Spawn Nydus Worm',
        }

    class Spire(Research):
        abilities = {
            0x023100: 'Evolve Flyer Attacks Level 1',
            0x023101: 'Evolve Flyer Attacks Level 2',
            0x023102: 'Evolve Flyer Attacks Level 3',
            0x023103: 'Evolve Flyer Carapace Level 1',
            0x023104: 'Evolve Flyer Carapace Level 2',
            0x023105: 'Evolve Flyer Carapace Level 3',
        }

    @UpgradeFrom(Spire, 0x022d00, 0x022d01)
    class GreaterSpire(Spire):
        pass

    class UltraliskCavern(Research):
        abilities = {
            0x012602: 'Chitinous Plating',
        }
