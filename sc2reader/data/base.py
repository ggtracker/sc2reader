from __future__ import absolute_import

from sc2reader.data.utils import MetaData, DataObject

############################
## Unit Classifiers
############################

class Protoss(object):
    pass

class Zerg(object):
    pass

class Terran(object):
    pass

class Main(object):
    pass

class Resource(DataObject):
    pass

class Building(DataObject):
    pass

class MineralField(Resource):
    pass

class RichMineralField(MineralField):
    pass

class VespeneGeyser(Resource):
    pass

class RichVespeneGeyser(VespeneGeyser):
    pass

class Moveable(DataObject):
    pass

class Critter(Moveable):
    pass

class Destructable(DataObject):
    pass

class Attacker(DataObject):
    pass

class Army(Moveable, Attacker):
    pass

class Unit(DataObject):
    pass

class Supporter(DataObject):
    pass

class Research(Building):
    pass

class Production(Building):
    pass

class Worker(Moveable, Attacker):
    pass

###################################
## Terran Specific Classifications

class TerranBuilding(Building):
    pass

class Production(Building):
    pass

class TerranMain(TerranBuilding, Production):
    pass

####################################
## Protoss Specific Classifications

class Hallucination(Protoss, Moveable, Attacker):
    pass


################################
## The Base Data Class
################################
class BaseData(object):
    """This class holds the unit codes and classifications"""

    __metaclass__ = MetaData

    @classmethod
    def type(self, type_code):
        return self.types[type_code]

    @classmethod
    def ability(self, ability_code):
        return self.abilities[ability_code]

    #######################
    ## Terran
    #######################

    class Techlab(TerranBuilding):
        code = 0x1e01

    class Reactor(TerranBuilding):
        code = 0x1f01

    class CommandCenter(TerranMain):
        code = 0x2d01
        class Flying(TerranBuilding, Moveable):
            code = 0x4001

    class PlanetaryFortress(TerranMain):
        code = 0x9e01

    class OrbitalCommand(TerranMain):
        code = 0xa001
        class Flying(TerranBuilding, Moveable):
            code = 0xa201

    class SupplyDepot(TerranBuilding):
        code = 0x2e01
        class Lowered(TerranBuilding):
            code = 0x4b01

    class Refinery(TerranBuilding):
        code = 0x2f01

    class Barracks(TerranBuilding, Production):
        code = 0x3001

        class Techlab(TerranBuilding):
            code = 0x4101

        class Reactor(TerranBuilding):
            code = 0x4201

        class Flying(TerranBuilding, Moveable):
            code = 0x4a01

    class EngineeringBay(TerranBuilding):
        code = 0x3101

    class MissileTurret(TerranBuilding, Attacker):
        code = 0x3201

    class Bunker(TerranBuilding, Attacker):
        code = 0x3301

    class SensorTower(TerranBuilding):
        code = 0x3401

    class GhostAcademy(TerranBuilding):
        code = 0x3501

    class Factory(TerranBuilding, Production):
        code = 0x3601

        class Techlab(TerranBuilding):
            code = 0x4301

        class Reactor(TerranBuilding):
            code = 0x4401

        class Flying(TerranBuilding, Moveable):
            code = 0x4701

    class Starport(TerranBuilding, Production):
        code = 0x3701

        class Techlab(TerranBuilding):
            code = 0x4501

        class Reactor(TerranBuilding):
            code = 0x4601

        class Flying(TerranBuilding, Moveable):
            code = 0x4801

    class Armory(TerranBuilding):
        code = 0x3901

    class FusionCore(TerranBuilding):
        code = 0x3a01

    class AutoTurret(Terran, Attacker):
        code = 0x3b01

    class PointDefenseDrone(Terran, Supporter):
        code = 0x2501

    class SiegeTank(Terran, Moveable, Attacker):
        code = 0x3c01
        # They really shouldn't be able to move but I've
        # found evidence that move commands have been recorded
        # for them.
        class Sieged(Terran, Attacker):
            code = 0x3d01

    class Viking(Terran, Moveable, Attacker):
        code = 0x3e01
        class Assault(Terran, Moveable, Attacker):
            code = 0x3f01

    class MULE(Terran, Worker):
        code = 0xb901

    class SCV(Terran, Worker):
        code = 0x4901

    class Marine(Terran, Moveable, Attacker):
        code = 0x4c01

    class Reaper(Terran, Moveable, Attacker):
        code = 0x4d01

    class Ghost(Terran, Moveable, Attacker):
        code = 0x4e01

    class Marauder(Terran, Moveable, Attacker):
        code = 0x4f01

    class Thor(Terran, Moveable, Attacker):
        code = 0x5001

    class Hellion(Terran, Moveable, Attacker):
        code = 0x5101

    class Medivac(Terran, Moveable, Supporter):
        code = 0x5201

    class Banshee(Terran, Moveable, Attacker):
        code = 0x5301

    class Raven(Terran, Moveable, Supporter):
        code = 0x5401

    class Battlecruiser(Terran, Moveable, Attacker):
        code = 0x5501


    ######################
    ## Protoss
    ######################

    class Probe(Protoss, Worker):
        code = 0x7001

    class Zealot(Protoss, Moveable, Attacker):
        code = 0x6501

    class ZealotHallucinated(Protoss, Moveable, Attacker):
        code = 0x6502

    class Stalker(Protoss, Moveable, Attacker):
        code = 0x6601

    class StalkerHalluncinated(Protoss, Moveable, Attacker):
        code = 0x6602

    class HighTemplar(Protoss, Moveable, Supporter):
        code = 0x6701

    class HighTemplarHallucinated(Protoss, Moveable, Supporter):
        code = 0x6702

    class DarkTemplar(Protoss, Moveable, Attacker):
        code = 0x6801

    class DarkTemplarHallucinated(Protoss, Moveable, Attacker):
        code = 0x6802

    class Sentry(Protoss, Moveable, Attacker):
        code = 0x6901

    class SentryHallucinated(Protoss, Moveable, Attacker):
        code = 0x6902

    class Pheonix(Protoss, Moveable, Attacker):
        code = 0x6a01

    class PhoenixHallucinated(Protoss, Moveable, Attacker):
        code = 0x6a02

    class Carrier(Protoss, Moveable, Attacker):
        code = 0x6b01

    class CarrierHallucinated(Protoss, Moveable, Attacker):
        code = 0x6b02

    class VoidRay(Protoss, Moveable, Attacker):
        code = 0x6c01

    class VoidRayHallucinated(Protoss, Moveable, Attacker):
        code = 0x6c02

    class WarpPrism(Protoss, Moveable, Supporter):
        code = 0x6d01
        class Phasing(Protoss, Supporter):
            code = 0xa401

    class WarpPrismHallucinated(Protoss, Moveable, Supporter):
        code = 0x6d02

    class Observer(Protoss, Moveable, Supporter):
        code = 0x6e01

    class Immortal(Protoss, Moveable, Attacker):
        code = 0x6f01

    class ImmortalHallucinated(Protoss, Moveable, Attacker):
        code = 0x6f02

    class Archon(Protoss, Moveable, Attacker):
        code = 0xa801

    class Colossus(Protoss, Moveable, Attacker):
        code = 0x1d01

    class ColossusHallucinated(Protoss, Moveable, Attacker):
        code = 0x1d02

    class Mothership(Protoss, Moveable, Attacker):
        code = 0x2401

    class Nexus(Protoss, Building, Main):
        code = 0x5701

    class Pylon(Protoss, Building):
        code = 0x5801

    class Assimilator(Protoss, Building):
        code = 0x5901

    class Gateway(Protoss, Building):
        code = 0x5a01
        class WarpGate(Protoss, Building):
            code = 0xa101

    class Forge(Protoss, Building):
        code = 0x5b01

    class FleetBeacon(Protoss, Building):
        code = 0x5c01

    class TwilightCouncil(Protoss, Building):
        code = 0x5d01

    class PhotonCannon(Protoss, Building, Attacker):
        code = 0x5e01

    class Stargate(Protoss, Building):
        code = 0x5f01

    class TemplarArchive(Protoss, Building):
        code = 0x6001

    class DarkShrine(Protoss, Building):
        code = 0x6101

    class RoboticsBay(Protoss, Building):
        code = 0x6201

    class RoboticsFacility(Protoss, Building):
        code = 0x6301

    class CyberneticsCore(Protoss, Building):
        code = 0x6401


    ###################
    ## Zerg
    ###################

    class Broodling(Zerg, Moveable, Attacker):
        code = 0xcf01

    class InfestedTerranEgg(Zerg, DataObject):
        code = 0xb001

    class Larva(Zerg, DataObject):
        code = 0xb101

    class Changeling(Zerg, Moveable, Supporter):
        code = 0x2601

    class ChangelingZealot(Changeling):
        code = 0x2701

    class ChangelingMarine(Changeling):
        code = 0x2801

    class ChangelingMarineShield(ChangelingMarine):
        code = 0x2901

    class ChangelingZergling(Changeling):
        code = 0x2a01

    class ChangelingZerglingWings(ChangelingZergling):
        code = 0x2b01

    class Hatchery(Zerg, Building, Main):
        code = 0x7201

    class CreepTumor(Zerg, Building):
        code = 0x7301

    class Extractor(Zerg, Building):
        code = 0x7401

    class SpawningPool(Zerg, Building):
        code = 0x7501

    class EvolutionChamber(Zerg, Building):
        code = 0x7601

    class HydraliskDen(Zerg, Building):
        code = 0x7701

    class Spire(Zerg, Building):
        code = 0x7801

    class UltraliskCavern(Zerg, Building):
        code = 0x7901

    class InfestationPit(Zerg, Building):
        code = 0x7a01

    class NydusNetwork(Zerg, Building):
        code = 0x7b01

    class BanelingNest(Zerg, Building):
        code = 0x7c01

    class RoachWarren(Zerg, Building):
        code = 0x7d01

    class Lair(Zerg, Building, Main):
        code = 0x8001

    class Hive(Zerg, Building, Main):
        code = 0x8101

    class GreaterSpire(Zerg, Building):
        code = 0x8201

    class SpineCrawler(Zerg, Building, Attacker):
        code = 0x7e01
        class Uprooted(Zerg, Building, Moveable):
            code = 0xa601

    class SporeCrawler(Zerg, Building, Attacker):
        code = 0x7f01
        class Uprooted(Zerg, Building, Moveable):
            code = 0xa701

    class InfestedTerran(Zerg, Moveable, Attacker):
        code = 0x2101
        class Burrowed(Zerg, DataObject):
            code = 0x9401

    class Baneling(Zerg, Moveable, Attacker):
        code = 0x2301
        class Cocoon(Zerg, DataObject):
            code = 0x2201
        class Burrowed(Zerg, DataObject):
            code = 0x8f01

    class Egg(Zerg, DataObject):
        code = 0x8301

    class Drone(Zerg, Worker):
        code = 0x8401
        class Burrowed(Zerg, DataObject):
            code = 0x9001

    class Zergling(Zerg, Moveable, Attacker):
        code = 0x8501
        class Burrowed(Zerg, DataObject):
            code = 0x9301

    class Overlord(Zerg, Moveable, Supporter):
        code = 0x8601

    class Hydralisk(Zerg, Moveable, Attacker):
        code = 0x8701
        class Burrowed(Zerg, DataObject):
            code = 0x9101

    class Mutalisk(Zerg, Moveable, Attacker):
        code = 0x8801

    class Ultralisk(Zerg, Moveable, Attacker):
        code = 0x8901
        class Burrowed(Zerg, DataObject):
            code = 0x9f01

    class Roach(Zerg, Moveable, Attacker):
        code = 0x8a01
        class Burrowed(Zerg, Moveable):
            code = 0x9201

    class Infestor(Zerg, Moveable, Supporter):
        code = 0x8b01
        class Burrowed(Zerg, Moveable):
            code = 0x9b01

    class Corruptor(Zerg, Moveable, Attacker):
        code = 0x8c01

    class Broodlord(Zerg, Moveable, Attacker):
        code = 0x8e01
        class Cocoon(Zerg, DataObject):
            code = 0x8d01

    class Queen(Zerg, Moveable, Attacker):
        code = 0x9a01
        class Burrowed(Zerg, DataObject):
            code = 0x9901

    class Overseer(Zerg, Moveable, Supporter):
        code = 0x9d01
        class Cocoon(Zerg, DataObject):
            code = 0x9c01

    class CreepTumorBurrowed(CreepTumor):
        code = 0xa501

    class NydusWorm(Zerg, Building):
        code = 0xa901

    ########################
    ## Neutral
    ########################

    class XelnagaTower(DataObject):
        code = 0xad01

    class Scantipede(Critter):
        code = 0xeb01
    class Urubu(Critter):
        code = 0xe201
    class FemaleKarak(Critter):
        code = 0xe401
    class FemaleUrsadak(Critter):
        code = 0xe601
    class FemaleUrsadak2(Critter):
        code = 0xe901
        name = "Female Ursadak (Exotic)"
    class Lyote(Critter):
        code = 0xe101
    class UrsadakCalf(Critter):
        code = 0xe701
    class Automaton2000(Critter):
        code = 0xea01
    class MaleKarak(Critter):
        code = 0xe301
    class MaleUrsadak(Critter):
        code = 0xe501
    class MaleUrsadak2(Critter):
        code = 0xe801
        name = "Male Ursadak (Exotic)"

    ########################
    ## Resources
    ########################

    class RichMineralField1(RichMineralField):
        code = 0xab01

    class VespeneGeyser1(VespeneGeyser):
        code = 0x00f9

    class MineralField1(MineralField):
        code = 0xf101

    class VespeneGeyser2(VespeneGeyser):
        code = 0xf201

    class VespeneGeyser3(VespeneGeyser):
        code = 0xf301

    class VespeneGeyser4(VespeneGeyser):
        code = 0xf401

    class MineralField2(MineralField):
        code = 0x017c

    class MineralField3(MineralField):
        code = 0xf801

    class MineralField4(MineralField):
        code = 0xf901

    class MineralField5(MineralField):
        code = 0xfa01

    ###########################
    ## Destructables
    ###########################

    class Debris1(Destructable):
        code = 0x10601
        name = "Destructible Debris (Braxis Alpha)"
    class Debris2(Destructable):
        code = 0x10901
        name = "Destructible Debris"
    class Debris3(Destructable):
        code = 0x10801
        name = "Destructible Debris"
    class Debris4(Destructable):
        code = 0x10701
        name = "Destructible Debris (Braxis Alpha)"

    class Rock1(Destructable):
        code = 0x10a01
        name = "Destructible Rock"
    class Rock2(Destructable):
        code = 0x10c01
        name = "Destructible Rock"
    class Rock3(Destructable):
        code = 0x10e01
        name = "Destructible Rock"
    class Rock4(Destructable):
        code = 0x10b01
        name = "Destructible Rock"
    class Rock5(Destructable):
        code = 0x10d01
        name = "Destructible Rock"
    class Rock6(Destructable):
        code = 0x10f01
        name = "Destructible Rock"
    class Rock7(Destructable):
        code = 0x11101
        name = "Destructible Rock"
    class Rock8(Destructable):
        code = 0x11001
        name = "Destructible Rock"

    class MengskStatue2(Destructable):
        code = 0x11201
        name = "Mengsk Statue"
    class MengskStatue(Destructable):
        code = 0x11301
        name = "Mengsk Statue"
    class Statue1(Destructable):
        code = 0x11401
        name = "The Gift of Freedom (Mengsk Statue Alone)"
    class GloryOfTheDominion(Destructable):
        code = 0x11501
        name = "Glory of the Dominion (Mengsk Statue)"
    class Statue2(Destructable):
        code = 0x11601
        name = "The Wolves of Korhal (Wolf Statue)"
    class CapitolStatue(Destructable):
        code = 0x11701
        name = "Capitol Statue (Globe Statue)"

    class LongRock9(Destructable):
        code = 0x11801
        name = "Destructible Rock"

    class MengshStatue3(Destructable):
        code = 0x11b01

    class WolfStatue(Destructable):
        code = 0x11d01

    class Beacon(Destructable):
        code = 0xdb01
        name = "Beacon (Protoss Large)"
    class Beacon2(Destructable):
        code = 0xdd01
        name = "Beacon (Terran Large)"
    class Beacon3(Destructable):
        code = 0xdf01
        name = "Beacon (Zerg Large)"
    class Beacon4(Destructable):
        code = 0xdc01
        name = "Beacon (Protoss Small)"
    class Beacon5   (Destructable):
        code = 0xde01
        name = "Beacon (Terran Small)"
    class Beacon6(Destructable):
        code = 0xe001
        name = "Beacon (Zerg Small)"