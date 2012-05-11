from __future__ import absolute_import

from sc2reader.data.base import *
from sc2reader.data.utils import *

class Data_19595(BaseData):

    class DataObject(DataObject):
        abilities = {
            0x3601: 'Right click',
            0x5601: 'Right click in fog',
        }

    class Moveable(DataObject):
        abilities = {
            0x2400: 'Stop',
            0x2403: 'Stop',
            0x2602: 'Hold position',
            0x2620: 'Move to',
            0x26a0: 'Move to',
            0x2640: 'Move to',
            0x2621: 'Patrol',
            0x26a1: 'Patrol',
            0x0: 'Follow',
        }

    class Attacker(DataObject):
        abilities = {
            0x2400: 'Stop',   #Attackers can also stop
            0x2602: 'Hold position',
            0x2a20: 'Attack object',
            0x2a40: 'Attack object',
            0x2aa0: 'Attack move',
        }

    class Supporter(DataObject):
        abilities = {
            0x2623: 'Scan move', # attack move for units without attack
            0x26a3: 'Scan move', # attack move for units without attack
            0x2643: 'Scan target', # attack move for units without attack
        }

    class Building(DataObject):
        abilities = {
            0x6c00: 'Cancel',
            0x6c61: 'Cancel',
            0x6d00: 'Cancel',
            0x6d61: 'Cancel',
            0x6e00: 'Cancel',
            0x7000: 'Cancel',
            0x7100: 'Cancel',
        }

    class TerranBuilding(Building):
        abilities = {
            0x7101: 'Halt build',
        }

    class Research(Building):
        abilities = {
            0x0: 'Cancel', # Generic ESC cancel
            0x0: 'Cancel unit', # Cancel + build id
        }

    class Production(Building):
        abilities = {
            0x5820: 'Set rally point',
            0x5840: 'Set rally point',
            0x0: 'Set rally target',
            0x6d00: 'Cancel', # Generic ESC cancel
            0x0: 'Cancel unit', # Cancel + build id
        }

    class Worker(Moveable, Attacker):
        pass

    class SCV(Worker):
        abilities = {
            0x6940: 'Gather resources',
            0x6901: 'Return cargo',
            0x7200: 'Toggle Auto-Repair',
            0x7240: 'Repair',
            0xf30e: 'Halt',
            0x7320: 'Command Center',
            0x7321: 'Supply Depot',
            0x7323: 'Barracks',
            0x7324: 'Engineering Bay',
            0x7325: 'Missile Turret',
            0x7326: 'Bunker',
            0x7342: 'Refinery',
            0x7328: 'Sensor Tower',
            0x7329: 'Ghost Academy',
            0x732a: 'Factory',
            0x732b: 'Starport',
            0x732d: 'Armory',
            0x732f: 'Fusion Core',

            0x73a0: 'Command Center',
            0x73a1: 'Supply Depot',
            0x73a3: 'Barracks',
            0x73a4: 'Engineering Bay',
            0x73a5: 'Missile Turret',
            0x73a6: 'Bunker',
            0x73a2: 'Refinery',
            0x73a8: 'Sensor Tower',
            0x73a9: 'Ghost Academy',
            0x73aa: 'Factory',
            0x73ab: 'Starport',
            0x73ad: 'Armory',
            0x73af: 'Fusion Core',
        }

    class MULE(Worker):
        abilities = {
            0x3a00: 'Toggle Auto-Repair',
            0x3a40: 'Repair',
            0x4a01: 'Return Cargo',
            0x4a40: 'Gather',
        }

    class Marine(Moveable, Attacker):
        abilities = {
            0x7500: 'Use Stimpack (mixed)',
        }

    class Marauder(Moveable, Attacker):
        abilities = {
            0x7500: 'Use Stimpack (mixed)',
            0x6200: 'Use Stimpack',
        }

    @Cloaks(0x7600, 0x7601)
    @Channels('Tactical Nuclear Strike',start=0x16020,cancel=0x16001)
    class Ghost(Moveable, Attacker):
        abilities = {
            0x3300: 'Hold fire',
            0x3400: 'Weapons free',
            0x16320: 'EMP Round',
            0x7740: 'Sniper Round',

            0x163a0: 'EMP Round',
        }

    @Mode('Sieged',('Siege Mode', 0x7900, None),('Unsiege', 0x7a00, None))
    class SiegeTank(Moveable, Attacker):
        pass

    @Channels('250mm Strike Cannons', 0x6440, 0x6401)
    class Thor(Moveable, Attacker):
        pass

    #This mode change cannot be cancelled
    @Mode('Assault',('Assult Mode', 0x7f00, None),('Fighter Mode', 0x8000, None))
    @Mode('Assault',('Assult Mode', 0x0, None),('Fighter Mode', 0x10000, None))
    class Viking(Moveable, Attacker):
        pass

    @Transports(0x7c22, None, 0x7c63, 0x7c40)
    @Transports(0x0, None, 0x0, 0x7c42)
    @Transports(0x7ca2, None, 0x0, 0x0)
    class Medivac(Moveable, Supporter):
        abilities = {
            0x7800: 'Toggle Auto-Heal',
            0x7840: 'Heal',
        }

    class Raven(Moveable, Supporter):
        abilities = {
            0x17c20: 'Auto Turret',
            0x3f20: 'Point Defense Drone',
            0x4b40: 'Seeker Missile',

            0x17ca0: 'Auto Turret',
            0x3fa0: 'Point Defense Drone',
        }

    @Cloaks(0x7b00, 0x7b01)
    class Banshee(Moveable, Attacker):
        pass

    class Battlecruiser(Moveable, Attacker):
        abilities = {
            0x7e40: 'Yamato Cannon',
        }

    class TerranMain(TerranBuilding):
        abilities = {
            0x5a20: 'Set rally point',
            0x5a40: 'Set rally target',
            0x10d00: 'Train SCV',
        }

    @Lifts(0x10300, 0x10420)
    @Lifts(0x0, 0x104a0)
    @Transports(0x10201, None, 0x10263, 0x10204)
    class CommandCenter(TerranMain, Production):
        pass

    @Lifts(0x15800, 0x15920)
    @Lifts(0x0, 0x159a0)
    @UpgradeFrom(CommandCenter, 0x15500, 0x15501)
    class OrbitalCommand(TerranMain, Production):
        abilities = {
            0x4c40: 'MULE (Target)',
            0x4c20: 'MULE (Location)',
            0x6340: 'Extra Supplies',
            0x7d20: 'Scanner Sweep',

            0x4ca0: 'MULE (Location)',
            0x7da0: 'Scanner Sweep',
        }

    @UpgradeFrom(CommandCenter, 0x15000, 0x15001)
    class PlanetaryFortress(TerranMain, Production):
        abilties = {
            0x6f61: 'Cancel (PF ONLY)',
            0x6f00: 'Cancel (PF ONLY)',
        }

    @Lowers(0x10f00, 0x11000)
    class SupplyDepot(TerranBuilding):
        pass

    class EngineeringBay(TerranBuilding, Research):
        abilities = {
            0x11400: 'Hi-Sec Auto Tracking',
            0x11401: 'Building Armor',
            0x11402: 'Infantry Weapons Level 1',
            0x11403: 'Infantry Weapons Level 2',
            0x11404: 'Infantry Weapons Level 3',
            0x11405: 'Neosteel Frame',
            0x11406: 'Infantry Armor Level 1',
            0x11407: 'Infantry Armor Level 2',
            0x11408: 'Infantry Armor Level 3',
        }

    class GhostAcademy(TerranBuilding, Research):
        abilities = {
            0x11600: 'Arm silo with Nuke',
            0x11a00: 'Personal Cloaking',
            0x11a01: 'Moebius Reactor',
        }

    @Transports(0x10101, None, 0x10163, 0x10140)
    class Bunker(TerranBuilding):
        abilities = {
            0x3100: 'Salvage',
            0x16200: 'Salvage',
            0x17100: 'Stimpack',
            0x17040: 'Attack',
            0x17400: 'Stop'
        }

    class Armory(TerranBuilding, Research):
        abilities = {
            0x11b02: 'Vehicle Plating Level 1',
            0x11b03: 'Vehicle Plating Level 2',
            0x11b04: 'Vehicle Plating Level 3',
            0x11b05: 'Vehicle Weapons Level 1',
            0x11b06: 'Vehicle Weapons Level 2',
            0x11b07: 'Vehicle Weapons Level 3',
            0x11b08: 'Ship Plating Level 1',
            0x11b09: 'Ship Plating Level 2',
            0x11b0a: 'Ship Plating Level 3',
            0x11b0b: 'Ship Weapons Level 1',
            0x11b0c: 'Ship Weapons Level 2',
            0x11b0d: 'Ship Weapons Level 3',
        }

    class FusionCore(TerranBuilding, Research):
        abilities = {
            0x15d00: 'Weapon Refit',
            0x15d01: 'Behemoth Reactor',
        }

    @Lifts(0x10600, 0x10e20)
    @Lifts(0x0, 0x10ea0)
    @AddOn('Techlab', start=0x10500, move=0x0, cancel=0x1850e)
    @AddOn('Techlab', start=0x10520, move=0x0, cancel=0x1850e)
    @AddOn('Techlab', start=0x105a0, move=0x0, cancel=0x1850e)
    @AddOn('Reactor', start=0x10501, move=0x0, cancel=0x1850e)
    @AddOn('Reactor', start=0x10521, move=0x0, cancel=0x1850e)
    @AddOn('Reactor', start=0x105a1, move=0x0, cancel=0x1850e)
    class Barracks(TerranBuilding, Production):
        abilities = {
            0x11100: 'Marine',
            0x11101: 'Reaper',
            0x11102: 'Ghost',
            0x11103: 'Marauder',
        }

        class Techlab(Research):
            abilities = {
                0x11503: 'Nitro Packs',
                0x11700: 'Stimpack',
                0x11701: 'Combat Shields',
                0x11702: 'Concussive Shells',
                0x0: 'Cancel Research',
                0x7061: 'Cancel Specific Research',
            }

        class Reactor(TerranBuilding):
            pass

        @AddOn('Techlab', start=0x10500, move=0x0, cancel=0x1850e)
        @AddOn('Techlab', start=0x10520, move=0x0, cancel=0x1850e)
        @AddOn('Techlab', start=0x105a0, move=0x0, cancel=0x1850e)
        @AddOn('Reactor', start=0x10501, move=0x0, cancel=0x1850e)
        @AddOn('Reactor', start=0x10521, move=0x0, cancel=0x1850e)
        @AddOn('Reactor', start=0x105a1, move=0x0, cancel=0x1850e)
        class Flying(TerranBuilding, Moveable):
            pass

    @Lifts(0x10800,0x10b20)
    @Lifts(0x0,0x10ba0)
    @AddOn('Techlab', start=0x10700, move=0x0, cancel=0x1870e)
    @AddOn('Techlab', start=0x10720, move=0x0, cancel=0x1870e)
    @AddOn('Techlab', start=0x107a0, move=0x0, cancel=0x1870e)
    @AddOn('Reactor', start=0x10701, move=0x0, cancel=0x1870e)
    @AddOn('Reactor', start=0x10721, move=0x0, cancel=0x1870e)
    @AddOn('Reactor', start=0x107a1, move=0x0, cancel=0x1870e)
    class Factory(TerranBuilding, Production):
        abilities = {
            0x11201: 'Siege Tank',
            0x11204: 'Thor',
            0x11205: 'Hellion'
        }

        class Techlab(Research):
            abilities = {
                0x11800: 'Siege Tech',
                0x11801: 'Infernal Pre-igniter',
                0x11802: '250mm Strike Cannons',
                0x0: 'Cancel Research',
                0x7061: 'Cancel Specific Research',
            }

        class Reactor(TerranBuilding):

            pass

        @AddOn('Techlab', start=0x10700, move=0x0, cancel=0x1870e)
        @AddOn('Techlab', start=0x10720, move=0x0, cancel=0x1870e)
        @AddOn('Techlab', start=0x107a0, move=0x0, cancel=0x1870e)
        @AddOn('Reactor', start=0x10701, move=0x0, cancel=0x1870e)
        @AddOn('Reactor', start=0x10721, move=0x0, cancel=0x1870e)
        @AddOn('Reactor', start=0x107a1, move=0x0, cancel=0x1870e)
        class Flying(TerranBuilding, Moveable):
            pass

    @Lifts(0x10a00, 0x10c20)
    @Lifts(0x0, 0x10ca0)
    @AddOn('Techlab', start=0x10900, move=0x0, cancel=0x1890e)
    @AddOn('Techlab', start=0x10920, move=0x0, cancel=0x1890e)
    @AddOn('Techlab', start=0x109a0, move=0x0, cancel=0x1890e)
    @AddOn('Reactor', start=0x10901, move=0x0, cancel=0x1890e)
    @AddOn('Reactor', start=0x10921, move=0x0, cancel=0x1890e)
    @AddOn('Reactor', start=0x109a1, move=0x0, cancel=0x1890e)
    class Starport(TerranBuilding, Production):
        abilities = {
            0x11300: 'Medivac',
            0x11301: 'Banshee',
            0x11302: 'Raven',
            0x11303: 'Battlecruiser',
            0x11304: 'Viking',
        }

        class Techlab(Research):
            abilities = {
                0x11900: 'Cloaking Field',
                0x11902: 'Caduceus Reactor',
                0x11903: 'Corvid Rector',
                0x11906: 'Seeker Missile',
                0x11907: 'Durable Materials',
                0x0: 'Cancel Research',
                0x7061: 'Cancel Specific Research',
            }

        class Reactor(TerranBuilding):
            pass

        @AddOn('Techlab', start=0x10900, move=0x0, cancel=0x1890e)
        @AddOn('Techlab', start=0x10920, move=0x0, cancel=0x1890e)
        @AddOn('Techlab', start=0x109a0, move=0x0, cancel=0x1890e)
        @AddOn('Reactor', start=0x10901, move=0x0, cancel=0x1890e)
        @AddOn('Reactor', start=0x10921, move=0x0, cancel=0x1890e)
        @AddOn('Reactor', start=0x109a1, move=0x0, cancel=0x1890e)
        class Flying(TerranBuilding, Moveable):
            pass

    ###########################
    ## Protoss Units
    ###########################

    class Probe(Worker):
        abilities = {
            0x6a01: 'Return cargo',
            0x6a40: 'Gather resources',
            0x11c20: 'Nexus',
            0x11ca0: 'Nexus',
            0x11c21: 'Pylon',
            0x11ca1: 'Pylon',
            0x11c23: 'Gateway',
            0x11ca3: 'Gateway',
            0x11c24: 'Forge',
            0x11ca4: 'Forge',
            0x11c25: 'Fleet Beacon',
            0x11ca5: 'Fleet Beacon',
            0x11c26: 'Twilight Council',
            0x11ca6: 'Twilight Council',
            0x11c27: 'Photon Cannon',
            0x11ca7: 'Photon Cannon',
            0x11c42: 'Assimilator',
            0x11c29: 'Stargate',
            0x11ca9: 'Stargate',
            0x11c2a: 'Templar Archives',
            0x11caa: 'Templar Archives',
            0x11c2b: 'Dark Shrine',
            0x11cab: 'Dark Shrine',
            0x11c2c: 'Robotics Bay',
            0x11cac: 'Robotics Bay',
            0x11c2d: 'Robotics Facility',
            0x11cad: 'Robotics Facility',
            0x11c2e: 'Cybernetics Core',
            0x11cae: 'Cybernetics Core',
        }

    class Stalker(Moveable, Attacker):
        abilities = {
            0x14c20: 'Blink',
            0x14ca0: 'Blink',
        }

    class Sentry(Moveable, Attacker):
        abilities = {
            0x4000: 'Hallucinate Archon',
            0x4100: 'Hallucinate Colossus',
            0x4200: 'Hallucinate High Templar',
            0x4300: 'Hallucinate Immortal',
            0x4400: 'Hallucinate Phoenix',
            0x4500: 'Hallucinate Probe',
            0x4600: 'Hallucinate Stalker',
            0x4700: 'Hallucinate Void Ray',
            0x4800: 'Hallucinate Warp Prism',
            0x4900: 'Hallucinate Zealot',
            0x3900: 'Guardian Shield',
            0x15a20: 'Force Field',

            0x15aa0: 'Force Field',
        }

    class HighTemplar(Moveable, Supporter):
        abilities = {
            0x12220: 'Psionic Storm',
            0x122a0: 'Psionic Storm',
            0x3d40: 'Feedback',
        }

    class DarkTemplar(Moveable, Attacker):
        pass

    @MergeFrom([HighTemplar, DarkTemplar], 0x17d00, 0x0)
    class Archon(Moveable, Attacker):
        pass

    #Phasing mode changes cannot be cancelled
    @Mode('Phasing', ('Phase Mode', 0x15b00, None), ('Transport Mode', 0x15c00, None))
    @Transports(0x11d42, None, 0x11d63, 0x11d40)
    @Transports(0x11d22, None, 0x0, 0x0)
    @Transports(0x11da2, None, 0x0, 0x0)
    class WarpPrism(Moveable, Supporter):
        pass

    @Channels('Graviton Beam', 0x4d40, 0x4d01)
    class Pheonix(Moveable, Attacker):
        pass

    class Carrier(Moveable, Attacker):
        abilities = {
            0x12500: 'Build Intercepter',
        }

    class Mothership(Moveable, Attacker):
        abilities = {
            0x16420: 'Vortex',
            0x3e20: 'Mass Recall',
        }

    class Nexus(Production):
        abilities = {
            0x12100: 'Probe',
            0x3c00: 'Mothership',
            0x6640: 'Chrono Boost',
            0x5b40: 'Set rally point',
            0x5b20: 'Set rally target',
        }

    @Mode('WarpGate', ('Tranform to Warpgate',0x15600, None), ('Transform to Gateway', 0x15700, None))
    class Gateway(Production):
        abilities = {
            0x11e00: 'Train Zealot',
            0x11e01: 'Train Stalker',
            0x11e03: 'Train High Templar',
            0x11e04: 'Train Dark Templar',
            0x11e05: 'Train Sentry',
        }

        class WarpGate(Building):
            abilities = {
                0x14820: 'Warp in Zealot',
                0x14821: 'Warp in Stalker',
                0x14823: 'Warp in High Templar',
                0x14824: 'Warp in Dark Templar',
                0x14825: 'Warp in Sentry',

                0x148a0: 'Warp in Zealot',
                0x148a1: 'Warp in Stalker',
                0x148a3: 'Warp in High Templar',
                0x148a4: 'Warp in Dark Templar',
                0x148a5: 'Warp in Sentry',
            }

    class Forge(Research):
        abilities = {
            0x12600: 'Ground Weapons Level 1',
            0x12601: 'Ground Weapons Level 2',
            0x12602: 'Ground Weapons Level 3',
            0x12603: 'Ground Armor Level 1',
            0x12604: 'Ground Armor Level 2',
            0x12605: 'Ground Armor Level 3',
            0x12606: 'Shield Level 1',
            0x12607: 'Shield Level 2',
            0x12608: 'Shield Level 3',
        }

    class CyberneticsCore(Research):
        abilities = {
            0x15e00: 'Air Weapons Level 1',
            0x15e01: 'Air Weapons Level 2',
            0x15e02: 'Air Weapons Level 3',
            0x15e03: 'Air Armor Level 1',
            0x15e04: 'Air Armor Level 2',
            0x15e05: 'Air Armor Level 3',
            0x15e06: 'Warp Gate',
            0x15e07: 'Hallucination',
            0x15e09: 'Hallucination',
        }

    class RoboticsFacility(Production):
        abilities = {
            0x12000: 'Warp Prism',
            0x12001: 'Observer',
            0x12002: 'Colossus',
            0x12003: 'Immortal',
        }

    class Stargate(Production):
        abilities = {
            0x11f00: 'Phoenix',
            0x11f02: 'Carrier',
            0x11f04: 'Void Ray',
        }

    class TwilightCouncil(Research):
        abilities = {
            0x15f00: 'Charge',
            0x15f01: 'Blink',
        }

    class FleetBeacon(Research):
        abilities = {
            0x3701: 'Graviton Catapult',
            0x3702: 'Anion Crystals'
        }

    class TemplarArchive(Research):
        abilities = {
            0x0: 'Khaydarin Amulet',
            0x12804: 'Psionic Storm',
        }

    class RoboticsBay(Research):
        abilities = {
            0x12701: 'Gravitic Booster',
            0x12702: 'Gravitic Drive',
            0x12705: 'Extended Thermal Lance',
        }

    #####################
    ## Zerg
    #####################

    class Larva(DataObject):
        abilities = {
            0x13300: 'Drone',
            0x13301: 'Zergling',
            0x13302: 'Overlord',
            0x13303: 'Hydralisk',
            0x13304: 'Mutalisk',
            0x13306: 'Ultralisk',
            0x13309: 'Roach',
            0x1330a: 'Infestor',
            0x1330b: 'Corruptor',
        }

    class Egg(Supporter):
        abilities = {
            0x0: 'Cancel',
        }

    @Burrows(0x13700, 0x13800)
    class Drone(Worker):
        abilities = {
            0x12a01: 'Return cargo',
            0x12a40: 'Gather resources',
            0x0: 'Burrow',
            0x12920: 'Hatchery',
            0x12923: 'Spawning Pool',
            0x12924: 'Evolution Chamber',
            0x12925: 'Hydralisk Den',
            0x12926: 'Spire',
            0x12927: 'Ultralisk Cavern',
            0x12942: 'Extractor',
            0x12928: 'Infestation Pit',
            0x12929: 'Nydus Network',
            0x1292a: 'Baneling Nest',
            0x1292d: 'Roach Warren',
            0x1292e: 'Spine Crawler',
            0x1292f: 'Spore Crawler',

            0x129a0: 'Hatchery',
            0x129a3: 'Spawning Pool',
            0x129a4: 'Evolution Chamber',
            0x129a5: 'Hydralisk Den',
            0x129a6: 'Spire',
            0x129a7: 'Ultralisk Cavern',
            0x129a2: 'Extractor',
            0x129a8: 'Infestation Pit',
            0x129a9: 'Nydus Network',
            0x129aa: 'Baneling Nest',
            0x129ad: 'Roach Warren',
            0x129ae: 'Spine Crawler',
            0x129af: 'Spore Crawler',
        }

    @Burrows(0x14900, 0x14a00)
    class Queen(Moveable, Attacker):
        abilities = {
            0x17620: 'Creep Tumor',
            0x176a0: 'Creep Tumor',
            0x6140: 'Larva',
            0x16740: 'Transfuse',
        }

    @Burrows(0x13d00, 0x13e00)
    class Zergling(Moveable, Attacker):
        pass

    @Burrows(0x13500, 0x13600)
    @MorphedFrom(Zergling, 0x3b00, 0x0)
    class Baneling(Moveable, Attacker):
        abilities = {
            0x3600: 'Explode',
            0x5e40: 'Attack Structure',
            0x21c00: 'Enable Building Attack',
            0x0: 'Disable Building Attack',
        }

    @Burrows(0x13b00, 0x13c00)
    class Roach(Moveable, Attacker):
        pass

    @Burrows(0x13900, 0x13a00)
    class Hydralisk(Moveable, Attacker):
        pass

    @Burrows(0x14d00, 0x14e00)
    @Channels('Neural Parasite', 0x6040, 0x6001)
    class Infestor(Moveable, Supporter):
        abilities = {
            0x3820: 'Fungal Growth',
            0x38a0: 'Fungal Growth',

            0x5f20: 'Infested Terran',
            0x5fa0: 'Infested Terran',
        }

        class Burrowed(Moveable, Supporter):
            abilities = {
                0x5f20: 'Infested Terran',
                0x5fa0: 'Infested Terran',
            }

    @Burrows(0x15300, 0x15400)
    class Ultralisk(Moveable, Attacker):
        pass

    @Burrows(0x13f00, 0x14000)
    class InfestedTerran(Moveable, Attacker):
        pass

    class Corruptor(Moveable, Attacker):
        abilities = {
            0x3200: 'Corruption',
            0x3240: 'Corruption',
        }

    @MorphedFrom(Corruptor, 0x13400, 0x13401)
    class Broodlord(Moveable, Attacker):
        pass

    #@Transports(0x14501, None, 0x14563, 0x14504)
    @Transports(0x14501, None, 0x00, 0x00)
    class Overlord(Moveable, Supporter):
        abilities = {
            0x17500: 'Generate Creep',
            0x17501: 'Stop generating Creep',
            0x14522: 'Unload all at',
        }

    @MorphedFrom(Overlord, 0x14f00, 0x14f01)
    class Overseer(Zerg, Moveable, Supporter):
        abilities = {
            0x5100: 'Changeling',
            0x20440: 'Contaminate',
        }

    @Transports(0x0, 0x0, 0x0, 0x0)
    class NydusWorm(Building):
        pass

    @Uproots(0x17700, 0x17920, 0x17901)
    @Uproots(0x0, 0x179a0, 0x0)
    class SpineCrawler(Building, Attacker):
        pass

    @Uproots(0x17800, 0x17a20, 0x0)
    @Uproots(0x0, 0x17aa0, 0x0)
    class SporeCrawler(Building, Attacker):
        pass

    class ZergMain(Production, Research):
        abilities = {
            0x5c21: 'Set worker rally point',
            0x5c41: 'Set worker rally target',
            0x5c20: 'Set unit rally point',
            0x5c40: 'Set unit rally target',
            0x16500: 'Queen',
            0x12f03: 'Evolve Burrow',
            0x12f01: 'Evolve Pneumatized Carapace',
            0x12f02: 'Evolve Ventral Sacs',
        }

    class Hatchery(ZergMain):
        pass

    @UpgradeFrom(Hatchery,0x12c00, 0x12c01)
    class Lair(ZergMain):
        pass

    @UpgradeFrom(Lair, 0x12d00, 0x12d01)
    class Hive(ZergMain):
        pass

    class SpawningPool(Research):
        abilities = {
            0x13000: 'Evolve Adrenal Glands',
            0x13001: 'Evolve Metabolic Boost',
        }

    class EvolutionChamber(Research):
        abilities = {
            0x12b00: 'Evolve Melee Attacks Level 1',
            0x12b01: 'Evolve Melee Attacks Level 2',
            0x12b02: 'Evolve Melee Attacks Level 3',
            0x12b03: 'Evolve Ground Carapace Level 1',
            0x12b04: 'Evolve Ground Carapace Level 2',
            0x12b05: 'Evolve Ground Carapace Level 3',
            0x12b06: 'Evolve Missile Attacks Level 1',
            0x12b07: 'Evolve Missile Attacks Level 2',
            0x12b08: 'Evolve Missile Attacks Level 3',
        }

    class RoachWarren(Research):
        abilities = {
            0x5d01: 'Evolve Glial Reconstitution',
            0x5d02: 'Evolve Tunneling Claws',
        }

    class BanelingNest(Research):
        abilities = {
            0x15200: 'Evolve Centrifugal Hooks',
        }

    @Channels('Creep Tumor', 0x17b20, 0x0)
    @Channels('Creep Tumor', 0x17ba0, 0x0)
    class CreepTumorBurrowed(Building):
        pass

    class HydraliskDen(Research):
        abilities = {
            0x13102: 'Evolve Grooved Spines',
        }

    class InfestationPit(Research):
        abilities = {
            0x15102: 'Evolve Pathogen Glands',
            0x15103: 'Evolve Neural Parasite',
        }

    @Transports(0x14b01, None, 0x14b63, 0x14b40)
    class NydusNetwork(Building):
        abilities = {
            0x17e20: 'Spawn Nydus Worm',
        }

    class Spire(Research):
        abilities = {
            0x13200: 'Evolve Flyer Attacks Level 1',
            0x13201: 'Evolve Flyer Attacks Level 2',
            0x13202: 'Evolve Flyer Attacks Level 3',
            0x13203: 'Evolve Flyer Carapace Level 1',
            0x13204: 'Evolve Flyer Carapace Level 2',
            0x13205: 'Evolve Flyer Carapace Level 3',
        }

    @UpgradeFrom(Spire, 0x12e00, 0x12e01)
    class GreaterSpire(Spire):
        pass

    class UltraliskCavern(Research):
        abilities = {
            0x6702: 'Chitinous Plating',
        }
