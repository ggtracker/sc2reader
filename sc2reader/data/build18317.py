from __future__ import absolute_import

from sc2reader.data.base import *
from sc2reader.data.utils import *

class Data_18317(BaseData):

    class DataObject(DataObject):
        abilities = {
            0x0: 'Right click',
            0x0: 'Right click in fog',
        }

    class Moveable(DataObject):
        abilities = {
            0x0: 'Stop',
            0x0: 'Hold position',
            0x0: 'Move to',
            0x0: 'Patrol',
            0x0: 'Follow',
        }

    class Attacker(DataObject):
        abilities = {
            0x0: 'Stop',   #Attackers can also stop
            0x0: 'Hold position',
            0x0: 'Attack move',
            0x0: 'Attack object',
        }

    class Supporter(DataObject):
        abilities = {
            0x0: 'Scan move', # attack move for units without attack
            0x0: 'Scan target', # attack move for units without attack
        }

    class Building(DataObject):
        abilities = {
            0x0: 'Cancel',
        }

    class TerranBuilding(Building):
        abilities = {
            0x0: 'Halt build',
        }

    class Research(Building):
        abilities = {
            0x0: 'Cancel', # Generic ESC cancel
            0x0: 'Cancel unit', # Cancel + build id
        }

    class Production(Building):
        abilities = {
            0x0: 'Set rally point',
            0x0: 'Set rally target',
            0x0: 'Cancel', # Generic ESC cancel
            0x0: 'Cancel unit', # Cancel + build id
        }

    class Worker(Moveable, Attacker):
        pass

    class SCV(Worker):
        abilities = {
            0x0: 'Gather resources',
            0x0: 'Return cargo',
            0x0: 'Toggle Auto-Repair',
            0x0: 'Repair',
            0x0: 'Halt',
            0x0: 'Command Center',
            0x0: 'Supply Depot',
            0x0: 'Barracks',
            0x0: 'Engineering Bay',
            0x0: 'Missile Turret',
            0x0: 'Bunker',
            0x0: 'Refinery',
            0x0: 'Sensor Tower',
            0x0: 'Ghost Academy',
            0x0: 'Factory',
            0x0: 'Starport',
            0x0: 'Armory',
            0x0: 'Fusion Core',
        }

    class MULE(Worker):
        abilities = {
            0x0: 'Toggle Auto-Repair',
            0x0: 'Repair',
            0x0: 'Return Cargo',
            0x0: 'Gather',
        }

    class Marine(Moveable, Attacker):
        abilities = {
            0x0: 'Use Stimpack (mixed)',
        }

    class Marauder(Moveable, Attacker):
        abilities = {
            0x0: 'Use Stimpack (mixed)',
            0x0: 'Use Stimpack',
        }

    @Cloaks(0x0, 0x0)
    @Channels('Tactical Nuclear Strike',start=0x0,cancel=0x0)
    class Ghost(Moveable, Attacker):
        abilities = {
            0x0: 'Hold fire',
            0x0: 'Weapons free',
            0x0: 'EMP Round',
            0x0: 'Sniper Round',
        }

    @Mode('Sieged',('Siege Mode', 0x0, None),('Unsiege', 0x0, None))
    class SiegeTank(Moveable, Attacker):
        pass

    @Channels('250mm Strike Cannons',0x0,None)
    class Thor(Moveable, Attacker):
        pass

    #This mode change cannot be cancelled
    @Mode('Assault',('Assult Mode', 0x0, None),('Fighter Mode', 0x0, None))
    class Viking(Moveable, Attacker):
        pass

    @Transports(0x0, 0x0, 0x0, 0x0)
    class Medivac(Moveable, Supporter):
        abilities = {
            0x0: 'Toggle Auto-Heal',
            0x0: 'Heal',
        }

    class Raven(Moveable, Supporter):
        abilities = {
            0x0: 'Auto Turret',
            0x0: 'Point Defense Drone',
            0x0: 'Seeker Missile',
        }

    @Cloaks(0x0, 0x0)
    class Banshee(Moveable, Attacker):
        pass

    class Battlecruiser(Moveable, Attacker):
        abilities = {
            0x0: 'Yamato Cannon',
        }

    class TerranMain(TerranBuilding):
        abilities = {
            0x0: 'Set rally point',
            0x0: 'Set rally target',
            0x0: 'Train SCV',
        }

    @Lifts(0x0, 0x0)
    @Transports(0x0, 0x0, 0x0, 0x0)
    class CommandCenter(TerranMain, Production):
        pass

    @Lifts(0x0, 0x0)
    @UpgradeFrom(CommandCenter, 0x0, 0x0)
    class OrbitalCommand(TerranMain, Production):
        abilities = {
            0x0: 'MULE (Target)',
            0x0: 'MULE (Location)',
            0x0: 'Extra Supplies',
            0x0: 'Scanner Sweep',
        }

    @UpgradeFrom(CommandCenter, 0x0, 0x0)
    class PlanetaryFortress(TerranMain, Production):
        abilties = {
            0x0: 'Cancel (PF ONLY)', #????
        }

    @Lowers(0x0, 0x0)
    class SupplyDepot(TerranBuilding):
        pass

    class EngineeringBay(TerranBuilding, Research):
        abilities = {
            0x0: 'Hi-Sec Auto Tracking',
            0x0: 'Building Armor',
            0x0: 'Infantry Weapons Level 1',
            0x0: 'Infantry Weapons Level 2',
            0x0: 'Infantry Weapons Level 3',
            0x0: 'Neosteel Frame',
            0x0: 'Infantry Armor Level 1',
            0x0: 'Infantry Armor Level 2',
            0x0: 'Infantry Armor Level 3',
        }

    class GhostAcademy(TerranBuilding, Research):
        abilities = {
            0x0: 'Arm silo with Nuke',
            0x0: 'Personal Cloaking',
            0x0: 'Moebius Reactor',
        }

    @Transports(0x0, 0x0, 0x0, 0x0)
    class Bunker(TerranBuilding):
        abilities = {
            0x0: 'Salvage',
            0x0: 'Stimpack', #Can bunkers really stimpack?
            # I don't think these 2 are right....?
            #0x0: 'Attack',
            #0x0: 'Stop'
        }

    class Armory(TerranBuilding, Research):
        abilities = {
            0x0: 'Vehicle Plating Level 1',
            0x0: 'Vehicle Plating Level 2',
            0x0: 'Vehicle Plating Level 3',
            0x0: 'Vehicle Weapons Level 1',
            0x0: 'Vehicle Weapons Level 2',
            0x0: 'Vehicle Weapons Level 3',
            0x0: 'Ship Plating Level 1',
            0x0: 'Ship Plating Level 2',
            0x0: 'Ship Plating Level 3',
            0x0: 'Ship Weapons Level 1',
            0x0: 'Ship Weapons Level 2',
            0x0: 'Ship Weapons Level 3',
        }

    @Lifts(0x0, 0x0)
    @AddOn('Techlab', start=0x0, move=0x0, cancel=0x0)
    @AddOn('Reactor', start=0x0, move=0x0, cancel=0x0)
    class Barracks(TerranBuilding, Production):
        abilities = {
            0x0: 'Marine',
            0x0: 'Reaper',
            0x0: 'Ghost',
            0x0: 'Marauder',
        }

        class Techlab(Research):
            abilities = {
                0x0: 'Nitro Packs',
                0x0: 'Stimpack',
                0x0: 'Combat Shields',
                0x0: 'Concussive Shells',
                0x0: 'Cancel Research',
                0x0: 'Cancel specific Research',
            }

        class Reactor(TerranBuilding):
            pass

        @AddOn('Techlab', start=0x0, move=0x0, cancel=0x0)
        @AddOn('Reactor', start=0x0, move=0x0, cancel=0x0)
        class Flying(TerranBuilding, Moveable):
            pass

    @Lifts(0x0,0x0)
    @AddOn('Techlab', start=0x0, move=0x0, cancel=0x0)
    @AddOn('Reactor', start=0x0, move=0x0, cancel=0x0)
    class Factory(TerranBuilding, Production):
        abilities = {
            0x0: 'Siege Tank',
            0x0: 'Thor',
            0x0: 'Hellion'
        }

        class Techlab(Research):
            abilities = {
                0x0: 'Siege Tech',
                0x0: 'Infernal Pre-igniter',
                0x0: '250mm Strike Cannons',
                0x0: 'Cancel Research',
                0x0: 'Cancel specific Research',
            }

        class Reactor(TerranBuilding):

            pass

        @AddOn('Techlab', start=0x0, move=None, cancel=None)
        @AddOn('Reactor', start=0x0, move=None, cancel=None)
        class Flying(TerranBuilding, Moveable):
            pass

    @Lifts(0x0, 0x0)
    @AddOn('Techlab', start=0x0, move=0x0, cancel=0x0)
    @AddOn('Reactor', start=0x0, move=0x0, cancel=0x0)
    class Starport(TerranBuilding, Production):
        abilities = {
            0x0: 'Medivac',
            0x0: 'Banshee',
            0x0: 'Raven',
            0x0: 'Battlecruiser',
            0x0: 'Viking',
        }

        class Techlab(Research):
            abilities = {
                0x0: 'Cloaking Field',
                0x0: 'Caduceus Reactor',
                0x0: 'Corvid Rector',
                0x0: 'Seeker Missile',
                0x0: 'Durable Materials',
                0x0: 'Cancel Research',
                0x0: 'Cancel specific Research',
            }

        class Reactor(TerranBuilding):
            pass

        @AddOn('TechLab', start=0x0, move=0x0, cancel=0x0)
        @AddOn('Reactor', start=0x0, move=0x0, cancel=0x0)
        class Flying(TerranBuilding, Moveable):
            pass

    ###########################
    ## Protoss Units
    ###########################

    class Probe(Worker):
        abilities = {
            0x0: 'Return cargo',
            0x0: 'Nexus',
            0x0: 'Pylon',
            0x0: 'Gateway',
            0x0: 'Forge',
            0x0: 'Fleet Beacon',
            0x0: 'Twilight Council',
            0x0: 'Photon Cannon',
            0x0: 'Assimilator',
            0x0: 'Stargate',
            0x0: 'Templar Archives',
            0x0: 'Dark Shrine',
            0x0: 'Robotics Bay',
            0x0: 'Robotics Facility',
            0x0: 'Cybernetics Core',
        }

    class Stalker(Moveable, Attacker):
        abilities = {
            0x0: 'Blink',
        }

    class Sentry(Moveable, Attacker):
        abilities = {
            0x0: 'Hallucinate Archon',
            0x0: 'Hallucinate Colossus',
            0x0: 'Hallucinate High Templar',
            0x0: 'Hallucinate Immortal',
            0x0: 'Hallucinate Phoenix',
            0x0: 'Hallucinate Probe',
            0x0: 'Hallucinate Stalker',
            0x0: 'Hallucinate Void Ray',
            0x0: 'Hallucinate Warp Prism',
            0x0: 'Hallucinate Zealot',
            0x0: 'Guardian Shield',
            0x0: 'Force Field',
        }

    class HighTemplar(Moveable, Supporter):
        abilities = {
            0x0: 'Psionic Storm',
            0x0: 'Feedback',
        }

    class DarkTemplar(Moveable, Attacker):
        pass

    @MergeFrom([HighTemplar, DarkTemplar], 0x0, 0x0)
    class Archon(Moveable, Attacker):
        pass

    #Phasing mode changes cannot be cancelled
    @Mode('Phasing', ('Phase Mode', 0x0, None), ('Transport Mode', 0x0, None))
    @Transports(0x0, 0x0, 0x0, 0x0)
    class WarpPrism(Moveable, Supporter):
        pass

    @Channels('Graviton Beam', 0x0, 0x0)
    class Pheonix(Moveable, Attacker):
        pass

    class Carrier(Moveable, Attacker):
        abilities = {
            0x0: 'Build Intercepter',
        }

    class Mothership(Moveable, Attacker):
        abilities = {
            0x0: 'Vortex',
            0x0: 'Mass Recall',
        }

    class Nexus(Production):
        abilities = {
            0x0: 'Probe',
            0x0: 'Mothership',
            0x0: 'Chrono Boost',
            0x0: 'Set rally point',
            0x0: 'Set rally target',
        }

    @Mode('WarpGate', ('Tranform to Warpgate',0x031500, None), ('Transform to Gateway', 0x031600, None))
    class Gateway(Production):
        abilities = {
            0x0: 'Train Zealot',
            0x0: 'Train Stalker',
            0x0: 'Train High Templar',
            0x0: 'Train Dark Templar',
            0x0: 'Train Sentry',
        }

        class WarpGate(Building):
            abilities = {
                0x0: 'Warp in Zealot',
                0x0: 'Warp in Stalker',
                0x0: 'Warp in High Templar',
                0x0: 'Warp in Dark Templar',
                0x0: 'Warp in Sentry',
            }

    class Forge(Research):
        abilities = {
            0x0: 'Ground Weapons Level 1',
            0x0: 'Ground Weapons Level 2',
            0x0: 'Ground Weapons Level 3',
            0x0: 'Ground Armor Level 1',
            0x0: 'Ground Armor Level 2',
            0x0: 'Ground Armor Level 3',
            0x0: 'Shield Level 1',
            0x0: 'Shield Level 2',
            0x0: 'Shield Level 3',
        }

    class CyberneticsCore(Research):
        abilities = {
            0x0: 'Air Weapons Level 1',
            0x0: 'Air Weapons Level 2',
            0x0: 'Air Weapons Level 3',
            0x0: 'Air Armor Level 1',
            0x0: 'Air Armor Level 2',
            0x0: 'Air Armor Level 3',
            0x0: 'Warp Gate',
            0x0: 'Hallucination',
        }

    class RoboticsFacility(Production):
        abilities = {
            0x0: 'Warp Prism',
            0x0: 'Observer',
            0x0: 'Colossus',
            0x0: 'Immortal',
        }

    class Stargate(Production):
        abilities = {
            0x0: 'Phoenix',
            0x0: 'Carrier',
            0x0: 'Void Ray',
        }

    class TwilightCouncil(Research):
        abilities = {
            0x0: 'Charge',
            0x0: 'Blink',
        }

    class FleetBeacon(Research):
        abilities = {
            0x0: 'Graviton Catapult'
        }

    class TemplarArchive(Research):
        abilities = {
            0x0: 'Khaydarin Amulet',
            0x0: 'Psionic Storm',
        }

    class RoboticsBay(Research):
        abilities = {
            0x0: 'Gravitic Booster',
            0x0: 'Gravitic Drive',
            0x0: 'Extended Thermal Lance',
        }

    #####################
    ## Zerg
    #####################

    class Larva(DataObject):
        abilities = {
            0x0: 'Drone',
            0x0: 'Zergling',
            0x0: 'Overlord',
            0x0: 'Hydralisk',
            0x0: 'Mutalisk',
            0x0: 'Ultralisk',
            0x0: 'Roach',
            0x0: 'Infestor',
            0x0: 'Corruptor',
        }

    class Egg(Supporter):
        abilities = {
            0x0: 'Cancel',
        }

    @Burrows(0x0, 0x0)
    class Drone(Worker):
        abilities = {
            0x0: 'Return cargo',
            0x12a40: 'Gather resources',
            0x0: 'Burrow',
            0x0: 'Hatchery',
            0x0: 'Spawning Pool',
            0x0: 'Evolution Chamber',
            0x0: 'Hydralisk Den',
            0x0: 'Spire',
            0x0: 'Ultralisk Cavern',
            0x0: 'Extractor',
            0x0: 'Infestation Pit',
            0x0: 'Nydus Network',
            0x0: 'Baneling Nest',
            0x0: 'Roach Warren',
            0x0: 'Spine Crawler',
            0x0: 'Spore Crawler',
        }

    @Burrows(0x0, 0x0)
    class Queen(Moveable, Attacker):
        abilities = {
            0x0: 'Creep Tumor',
            0x0: 'Larva',
            0x0: 'Transfuse',
        }

    @Burrows(0x0, 0x0)
    class Zergling(Moveable, Attacker):
        pass

    @Burrows(0x0, 0x0)
    @MorphedFrom(Zergling, 0x0, 0x0)
    class Baneling(Moveable, Attacker):
        abilities = {
            0x0: 'Explode',
            0x0: 'Attack Structure',
            0x21c00: 'Enable Building Attack',
            0x0: 'Disable Building Attack',
        }

    @Burrows(0x0, 0x0)
    class Roach(Moveable, Attacker):
        pass

    @Burrows(0x0, 0x0)
    class Hydralisk(Moveable, Attacker):
        pass

    @Burrows(0x0, 0x0)
    @Channels('Neural Parasite', 0x0, 0x0)
    class Infestor(Moveable, Supporter):
        abilities = {
            0x0: 'Fungal Growth',
            0x0: 'Infested Terran',
        }

        class Burrowed(Moveable, Supporter):
            abilities = {
                0x0: 'Infested Terran',
            }

    @Burrows(0x0, 0x0)
    class Ultralisk(Moveable, Attacker):
        pass

    @Burrows(0x0, 0x0)
    class InfestedTerran(Moveable, Attacker):
        pass

    class Corruptor(Moveable, Attacker):
        abilities = {
            0x0: 'Corruption',
        }

    @MorphedFrom(Corruptor, 0x0, 0x0)
    class Broodlord(Moveable, Attacker):
        pass

    @Transports(0x0, 0x0, 0x0, 0x0)
    class Overlord(Moveable, Supporter):
        abilities = {
            0x0: 'Generate Creep',
            0x0: 'Stop generating Creep',
            0x0: 'Unload all at',
        }

    @MorphedFrom(Overlord, 0x0, 0x0)
    class Overseer(Zerg, Moveable, Supporter):
        abilities = {
            0x0: 'Changeling',
            0x0: 'Contaminate',
        }

    @Transports(0x0, 0x0, 0x0, 0x0)
    class NydusWorm(Building):
        pass

    @Uproots(0x0, 0x0, 0x0)
    class SpineCrawler(Building, Attacker):
        pass

    @Uproots(0x0, 0x0, 0x0)
    class SporeCrawler(Building, Attacker):
        pass

    class ZergMain(Production, Research):
        abilities = {
            0x0: 'Set worker rally point',
            0x0: 'Set worker rally target',
            0x0: 'Set unit rally point',
            0x0: 'Set unit rally target',
            0x0: 'Queen',
            0x0: 'Evolve Burrow',
            0x0: 'Evolve Pneumatized Carapace',
            0x0: 'Evolve Ventral Sacs',
        }

    class Hatchery(ZergMain):
        pass

    @UpgradeFrom(Hatchery,0x0, 0x0)
    class Lair(ZergMain):
        pass

    @UpgradeFrom(Lair, 0x0, 0x0)
    class Hive(ZergMain):
        pass

    class SpawningPool(Research):
        abilities = {
            0x0: 'Evolve Adrenal Glands',
            0x0: 'Evolve Metabolic Boost',
        }

    class EvolutionChamber(Research):
        abilities = {
            0x0: 'Evolve Melee Attacks Level 1',
            0x0: 'Evolve Melee Attacks Level 2',
            0x0: 'Evolve Melee Attacks Level 3',
            0x0: 'Evolve Ground Carapace Level 1',
            0x0: 'Evolve Ground Carapace Level 2',
            0x0: 'Evolve Ground Carapace Level 3',
            0x0: 'Evolve Missile Attacks Level 1',
            0x0: 'Evolve Missile Attacks Level 2',
            0x0: 'Evolve Missile Attacks Level 3',
        }

    class RoachWarren(Research):
        abilities = {
            0x0: 'Evolve Glial Reconstitution',
            0x0: 'Evolve Tunneling Claws',
        }

    class BanelingNest(Research):
        abilities = {
            0x0: 'Evolve Centrifugal Hooks',
        }

    @Channels('Creep Tumor', 0x0, 0x0)
    class CreepTumorBurrowed(Building):
        pass

    class HydraliskDen(Research):
        abilities = {
            0x0: 'Evolve Grooved Spines',
        }

    class InfestationPit(Research):
        abilities = {
            0x0: 'Evolve Pathogen Glands',
            0x0: 'Evolve Neural Parasite',
        }

    @Transports(0x0, 0x0, 0x0, 0x0)
    class NydusNetwork(Building):
        abilities = {
            0x0: 'Spawn Nydus Worm',
        }

    class Spire(Research):
        abilities = {
            0x0: 'Evolve Flyer Attacks Level 1',
            0x0: 'Evolve Flyer Attacks Level 2',
            0x0: 'Evolve Flyer Attacks Level 3',
            0x0: 'Evolve Flyer Carapace Level 1',
            0x0: 'Evolve Flyer Carapace Level 2',
            0x0: 'Evolve Flyer Carapace Level 3',
        }

    @UpgradeFrom(Spire, 0x0, 0x0)
    class GreaterSpire(Spire):
        pass

    class UltraliskCavern(Research):
        abilities = {
            0x0: 'Chitinous Plating',
        }
