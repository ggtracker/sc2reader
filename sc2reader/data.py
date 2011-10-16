import re

class MetaData(type):

    @classmethod
    def getSC2Classes(self, dct):
        #Get only DataObject classes and ignore all other attributes to allow for
        #flexibility in object class definition.
        filter = lambda v: hasattr(v, '__bases__') and DataObject in v.__mro__
        return [value for key,value in dct.iteritems() if filter(value)]

    @classmethod
    def copyObjects(self, src, dst):
        #For every class my parent has, if I don't have it, create an identical
        #class for me to have. We'll replace base references later!
        myClasses = [x.__name__ for x in self.getSC2Classes(dst.__dict__)]
        for cls in self.getSC2Classes(src.__dict__):
            name = cls.__name__
            if name not in myClasses:
                setattr(dst, name, type(name, cls.__bases__, dict(cls.__dict__)))
            else:
                new_cls = getattr(dst, name)
                new_cls.code = cls.code
                self.copyObjects(cls, new_cls)

    @classmethod
    def pull_abilities(self, cls):
        #Follow the bases tree down and pull all the ability codes up with you.
        if not hasattr(cls,'abilities'):
            cls.abilities = dict()

        for base in cls.__bases__:

            #Depth First Pulling. If performance is an issue we can track
            #completed classes since this will result in a lot of redundant work.
            if DataObject in base.__mro__:
                self.pull_abilities(base)

            #If we've got an abilities list, update ours...carefully.
            if hasattr(base, 'abilities'):
                for code, name in base.abilities.iteritems():
                    if code in cls.abilities:
                        if name != cls.abilities[code]:
                            msg = "Ability codes shouldn't duplicate: {0:X} => {1}, {2}!"
                            raise KeyError(msg.format(code, name, cls.abilities[code]))
                        else:
                            pass #it is okay
                    else:
                        cls.abilities[code] = name
            else:
                pass #Some bases are just classifiers

    @classmethod
    def apply_decorators(self, cls):
        for subcls in self.getSC2Classes(cls.__dict__):
            for decorator in getattr(subcls, 'decorators', []):
                decorator()

            self.apply_decorators(subcls)

    @classmethod
    def pull_subclasses(self, cls):
        for subcls in self.getSC2Classes(cls.__dict__):
            if DataObject in subcls.__mro__:
                self.pull_subclasses(subcls)
                for subsubcls in self.getSC2Classes(subcls.__dict__):
                    if DataObject in subsubcls.__mro__:
                        setattr(cls, subsubcls.__name__, subsubcls)

    def __new__(self, clsname, bases, dct):
        #The base class is the exception to the rule
        if clsname == 'BaseData':
            return type.__new__(self,clsname,bases,dct)

        #Save a list of the classes we started with. We'll need it to pull base
        #class references forward and pick up the new abilities.
        myClasses = [x.__name__ for x in self.getSC2Classes(dct)]

        #In order for this to work, its easier if we already have made a class
        #to get around some inconvenient dictproxy issues.
        data = type.__new__(self,clsname,bases,dct)

        #Recursively copy missing classes into my dictionary. Now I can be lazy and
        #only list objects with abilities in each dictionary.
        self.copyObjects(bases[0], data)

        #Now that all the objects have been filled in we should apply the decorators.
        #The decorators are wrapped up so that they don't get processed until after
        #the dependencies might have been copied up from an other dictionary.
        self.apply_decorators(data)

        #Pull all the nested classes up. Because some decorators alter subclasses
        #this is only safe after evaluating the decorators.
        self.pull_subclasses(data)

        #For all the sc2objects I have, update their base references to point
        #to my other classes. This moves the tree, not just the nodes, foward.
        #also comple the ability and type codes for mapping
        dct['types'] = dict()
        dct['abilities'] = dict()
        for cls in self.getSC2Classes(data.__dict__):

            #Update the base class references if possible. Otherwise use the old ones
            if cls.__name__ not in myClasses:
                new_bases = list()
                for base in cls.__bases__:
                    if hasattr(data, base.__name__):
                        new_bases.append(getattr(data, base.__name__))
                    else:
                        new_bases.append(base)
                cls.__bases__ = tuple(new_bases)

            #Pull in ability information from the newly updated base references
            #into the top level abilities dictionary for this class
            self.pull_abilities(cls)

            #Collect the type code if its present. Otherwise, skip its abilities
            #Every ability must be tied to specific units with codes.
            if 'code' in cls.__dict__:
                dct['types'][cls.code] = cls

                #Collect the ability codes, all classes should have an
                #abilities dictionary at this point, even if its empty.
                #Make sure to only collect valid unit abilities.
                for code, name in cls.abilities.iteritems():
                    dct['abilities'][code] = name

            else:
                pass #Some classes are just classifiers

        return type.__new__(self,clsname,bases,dct)

class MetaObject(type):
    def __new__(meta,name,bases,dct):
        dct['name']=name
        if not 'abilities' in dct:
            dct['abilities'] = dict()

        for base in bases:
            if 'abilties' in base.__dict__:
                for code, name in base.abilities.iteritems():
                    dct['abilities'][code] = name
            if not 'code' in dct and 'code' in base.__dict__:
                dct['code'] = base.code

        return type.__new__(meta,name,bases,dct)

#All data is either an object or an ability
class DataObject(object):
    __metaclass__ = MetaObject
    def __init__(self, id, timestamp):
        self.id = id

    def visit(self,frame,player,object_type=None):
        pass

    def __str__(self):
        return "{0} [{1:0>8X}]".format(self.__class__.__name__,self.id)


######################
## Decorators
######################

def Wrapped(func):
    def _wrapper(*args, **kwargs):
        def get_class(cls):
            if not hasattr(cls,'decorators'):
                cls.decorators = list()

            if not hasattr(cls,'abilities'):
                cls.abilities = dict()

            cls.decorators.append(lambda: func(cls, *args, **kwargs))
            return cls

        return get_class
    return _wrapper

@Wrapped
def Cloaks(cls, cloak, decloak):
    if not hasattr(cls, 'abilities'):
        cls.__dict__['abilities'] = dict()

    cls.abilities[cloak] = 'Cloak'
    cls.abilities[decloak] = 'Decloak'

@Wrapped
def Channels(cls, ability, start, cancel):
    cls.abilities[start] = ability
    cls.abilities[cancel] = "Cancel "+ability

@Wrapped
def Mode(cls, target_name, on, off):
    #some modes are not instant and the switch can be cancelled part way.
    on_name, on_code, on_cancel = on
    off_name, off_code, off_cancel = off

    target = getattr(cls,target_name)
    target.__name__ = "{0} ({1})".format(cls.__name__, target.__name__)
    if not hasattr(target, 'abilities'):
        target.abilities = dict()

    if not hasattr(cls, 'abilities'):
        cls.abilities = dict()

    cls.abilities[on_code] = on_name
    cls.abilities[on_cancel] = 'Cancel {0}'.format(on_name)
    target.abilities[off_code] = off_name
    target.abilities[off_cancel] = 'Cancel {0}'.format(off_name)

    #It seems like we need to actually cross list the mode
    #abilities. Maybe spamming screwed up the event listing?
    #Found a Sieged tank that had the "Seiege" ability used
    #while already seiged.
    #test_replays/1.2.2.17811/1.SC2REplay, player 2 - 9:40
    cls.abilities[off_code] = off_name
    cls.abilities[off_cancel] = 'Cancel {0}'.format(off_name)
    target.abilities[on_code] = on_name
    target.abilities[on_cancel] = 'Cancel {0}'.format(on_name)


def Lifts(liftoff, land):
    return Mode('Flying', ('Lift off', liftoff, None), ('Land', land, None))

def Burrows(burrow, unburrow):
    return Mode('Burrowed', ('Burrow',burrow,None), ('Unburrow',unburrow,None))

def Lowers(lower, raise_):
    return Mode('Lowered', ('Lower Supply Depot',lower,None), ('Raise Supply Depot',raise_,None))

def Uproots(uproot, root, cancel):
    return Mode('Uprooted',('Uproot',uproot,None),('Root',root,cancel))

@Wrapped
def UpgradeFrom(cls, target, start, cancel):
    target.abilities[start] = 'Upgrade to {0}'.format(target.__name__)
    target.abilities[cancel] = 'Cancel upgrade to {0}'.format(target.__name__)

@Wrapped
def Transports(cls, all_code, all_moving_code, unload_unit_code, load_unit_code):
    if all_code:
        cls.abilities[all_code] = 'Unload All'
    if all_moving_code:
        cls.abilities[all_moving_code] = 'Unload All (while moving)'
    if unload_unit_code:
        cls.abilities[unload_unit_code] = 'Unload Unit'
    if load_unit_code:
        cls.abilities[load_unit_code] = 'Load Unit'

@Wrapped
def AddOn(cls, target, start, move, cancel):
    if isinstance(target, DataObject):
        target = target.__name__

    cls.abilities[start] = 'Construct '+target
    cls.abilities[move] = 'Construct {0} (move first)'.format(target)
    cls.abilities[cancel] = 'Cancel '+target

    if hasattr(cls, target):
        getattr(cls,target).__name__ += ' ({0})'.format(cls.__name__)

@Wrapped
def MergeFrom(cls, sources, start, cancel):
    for source in sources:
        if not hasattr(source,'abilities'): source.abilities = dict()
        source.abilities[start] = 'Merge into {0}'.format(cls.__name__)
        source.abilities[cancel] = 'Cancel Merge'

@Wrapped
def MorphedFrom(cls, source, start, cancel):
    cocoon = cls.Cocoon
    cocoon.__name__ = cls.__name__+'Cocoon'

    if not hasattr(source, 'abilities'): source.abilities = dict()
    if not hasattr(cocoon, 'abilities'): cls.Cocoon.abilities = dict()

    source.abilities[start] = 'Morph to {0}'.format(cls.__name__)
    cocoon.abilities[cancel] = 'Cancel Morph to {0}'.format(cls.__name__)

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

    class MineralField5(MineralField):
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

'''
#1.3.0.18092
class Data_18092(BaseData):

    class Unit(DataObject):
        abilities = {
            0x260002: "Hold Position",
        }

    class Moveable(Unit):
        abilities = {
            0x260002: "Hold Position",
            0x000037: 'Right Click',
        }

    class Attacker(Unit):
        abilities = {
            0x2a0010: "Attack",
        }

    class Army(Moveable, Attacker):
        pass

    class Worker(Moveable, Attacker):
        abilities = {
            0x0057: "Gather",
        }

    class Addon(Building):
        pass

    class Colossus(Protoss, Army):
        code = 0x1d01

    class ColossusHallucinated(Protoss, Army):
        code = 0x1d02

    class Techlab(Terran, Addon):
        code = 0x1e01

    class Reactor(Terran, Addon):
        code = 0x1f01

    # ...

    class InfestedTerran(Zerg, Army):
        code = 0x2101

    class BanelingCocoon(Zerg, DataObject):
        code = 0x2201

    class Baneling(Zerg, Army):
        code = 0x2301

    class Mothership(Protoss, Army):
        code = 0x2401

    class PointDefenseDrone(Terran, DataObject):
        code = 0x2501

    class Changeling(Zerg, Unit):
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

    # ...

    class CommandCenter(Terran, Building, Main):
        code = 0x2d01

    class SupplyDepot(Terran, Building):
        code = 0x2e01

    class Refinery(Terran, Building):
        code = 0x2f01

    class Barracks(Terran, Building):
        code = 0x3001

    class EgnineeringBay(Terran, Building):
        code = 0x3101

    class MissileTurret(Terran, Building, Attacker):
        code = 0x3201

    class Bunker(Terran, Building, Attacker):
        code = 0x3301

    class SensorTower(Terran, Building):
        code = 0x3401

    class GhostAcademy(Terran, Building):
        code = 0x3501

    class Factory(Terran, Building):
        code = 0x3601

    class Starport(Terran, Building):
        code = 0x3701

    # ...

    class Armory(Terran, Building):
        code = 0x3901

    class FusionCore(Terran, Building):
        code = 0x3a01

    class AutoTurret(Terran, Attacker):
        code = 0x3b01

    class SiegeTank(Terran, Army):
        code = 0x3c01

    class UnsiegedTank(SiegeTank):
        code = 0x3d01

    class Viking(Terran, Army):
        code = 0x3e01

    class LandedViking(Viking):
        code = 0x3f01

    class CommandCenterFlying(CommandCenter):
        code = 0x4001

    class TechlabBarracks(Techlab):
        code = 0x4101

    class ReactorBarracks(Reactor):
        code = 0x4201

    class TechlabFactory(Techlab):
        code = 0x4301

    class ReactorFactory(Reactor):
        code = 0x4401

    class TechlabStarport(Techlab):
        code = 0x4501

    class ReactorStarport(Reactor):
        code = 0x4601

    class FactoryFlying(Factory):
        code = 0x4701

    class StarportFlying(Starport):
        code = 0x4801

    class SCV(Terran, Worker):
        code = 0x4901

    class BarracksFlying(Barracks):
        code = 0x4a01

    class SupplyDepotLowered(SupplyDepot):
        code = 0x4b01

    class Marine(Terran, Army):
        code = 0x4c01

    class Reaper(Terran, Army):
        code = 0x4d01

    class Ghost(Terran, Army):
        code = 0x4e01

    class Marauder(Terran, Army):
        code = 0x4f01

    class Thor(Terran, Army):
        code = 0x5001

    class Hellion(Terran, Army):
        code = 0x5101

    class Medivac(Terran, Army):
        code = 0x5201

    class Banshee(Terran, Army):
        code = 0x5301

    class Raven(Terran, Army):
        code = 0x5401

    class Battlecruiser(Terran, Army):
        code = 0x5501

    # ...

    class Nexus(Protoss, Building, Main):
        code = 0x5701

    class Pylon(Protoss, Building):
        code = 0x5801

    class Assimilator(Protoss, Building):
        code = 0x5901

    class Gateway(Protoss, Building):
        code = 0x5a01

    class Forge(Protoss, Building):
        code = 0x5b0

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

    class Zealot(Protoss, Army):
        code = 0x6501

    class ZealotHallucinated(Protoss, Army):
        code = 0x6502

    class Stalker(Protoss, Army):
        code = 0x6601

    class StalkerHalluncinated(Protoss, Army):
        code = 0x6602

    class HighTemplar(Protoss, Army):
        code = 0x6701

    class HighTemplarHallucinated(Protoss, Army):
        code = 0x6702

    class DarkTemplar(Protoss, Army):
        code = 0x6801

    class DarkTemplarHallucinated(Protoss, Army):
        code = 0x6802

    class Sentry(Protoss, Army):
        code = 0x6901

    class SentryHallucinated(Protoss, Army):
        code = 0x6902

    class Phoenix(Protoss, Army):
        code = 0x6a01

    class PhoenixHallucinated(Protoss, Army):
        code = 0x6a02

    class Carrier(Protoss, Army):
        code = 0x6b01

    class CarrierHallucinated(Protoss, Army):
        code = 0x6b02

    class VoidRay(Protoss, Army):
        code = 0x6c01

    class VoidRayHallucinated(Protoss, Army):
        code = 0x6c02

    class WarpPrism(Protoss, Army):
        code = 0x6d01

    class WarpPrismHallucinated(Protoss, Army):
        code = 0x6d02

    class Observer(Protoss, Unit):
        code = 0x6e01

    class Immortal(Protoss, Army):
        code = 0x6f01

    class ImmortalHallucinated(Protoss, Army):
        code = 0x6f02

    class Probe(Protoss, Worker):
        code = 0x7001

    # ...

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

    class SpineCrawler(Zerg, Building, Attacker):
        code = 0x7e01

    class SporeCrawler(Zerg, Building, Attacker):
        code = 0x7f01

    class Lair(Zerg, Building, Main):
        code = 0x8001

    class Hive(Zerg, Building, Main):
        code = 0x8101

    class GreaterSpire(Zerg, Building):
        code = 0x8201

    class Egg(Zerg, Unit):
        code = 0x8301

    class Drone(Zerg, Worker):
        code = 0x8401

    class Zergling(Zerg, Army):
        code = 0x8501

    class Overlord(Zerg, Unit):
        code = 0x8601

    class Hydralisk(Zerg, Army):
        code = 0x8701

    class Mutalisk(Zerg, Army):
        code = 0x8801

    class Ultralisk(Zerg, Army):
        code = 0x8901

    class Roach(Zerg, Army):
        code = 0x8a01

    class Infestor(Zerg, Army):
        code = 0x8b01

    class Corruptor(Zerg, Army):
        code = 0x8c01

    class BroodLordCocoon(Zerg, Unit):
        code = 0x8d01

    class BroodLord(Zerg, Army):
        code = 0x8e01

    class BanelingBurrowed(Baneling):
        code = 0x8f01

    class DroneBurrowed(Drone):
        code = 0x9001

    class HydraliskBurrowed(Hydralisk):
        code = 0x9101

    class RoachBurrowed(Roach):
        code = 0x9201

    class ZerglingBurrowed(Zergling):
        code = 0x9301

    class InfestedTerranBurrowed(InfestedTerran):
        code = 0x9401

    #...

    class Queen(Zerg, Army):
        code = 0x9a01

    class QueenBurrowed(Queen):
        code = 0x9901

    class InfestorBurrowed(Infestor):
        code = 0x9b01

    class OverseerCocoon(Zerg, Unit):
        code = 0x9c01

    class Overseer(Zerg, Unit):
        code = 0x9d01

    class PlanetaryFortress(Terran, Building, Main):
        code = 0x9e01

    class UltraliskBurrowed(Ultralisk):
        code = 0x9f01

    class OrbitalCommand(Terran, Building, Main):
        code = 0xa001

    class WarpGate(Protoss, Building):
        code = 0xa101

    class OrbitalCommandFlying(OrbitalCommand):
        code = 0xa201

    # ...

    class WarpPrismPhasing(WarpPrism):
        code = 0xa401

    class CreepTumorBurrowed(CreepTumor):
        code = 0xa501

    class SpineCrawlerUprooted(SpineCrawler):
        code = 0xa601

    class SporeCrawlerUprooted(SporeCrawler):
        code = 0xa701

    class Archon(Protoss, Army):
        code = 0xa801

    class NydusWorm(Zerg, Building):
        code = 0xa901

    # ...

    class RichMineralField1(RichMineralField):
        code = 0xab01

    # ...

    class XelnagaTower(DataObject):
        code = 0xad01

    # ...

    class InfestedTerranEgg(Zerg, DataObject):
        code = 0xb001

    class Larva(Zerg, DataObject):
        code = 0xb101

    # ...
    class MULE(Terran, Worker):
        code = 0xb901

    # ...

    class Broodling(Zerg, Army):
        code = 0xcf01

    # ...


    class VespeneGeyser1(VespeneGeyser):
        code = 0x00f9


    class MineralField1(MineralField):
        code = 0x00f8

    class MineralField2(MineralField):
        code = 0x017c

    class MineralField3(MineralField):
        code = 0xf801

    class MineralField4(MineralField):
        code = 0xf901
'''

class Data_17326(BaseData):

    class DataObject(DataObject):
        abilities = {
            0x3700: 'Right click',
            0x5700: 'Right click in fog',
        }

    class Moveable(DataObject):
        abilities = {
            0x002400: 'Stop',
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

    @Transports(0x020001, None, 0x020033, 0x20020)
    class Bunker(TerranBuilding):
        abilities = {
            0x032100: 'Salvage',
            0x033000: 'Stimpack', #Can bunkers really stimpack?
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
    @AddOn('Techlab', start=0x020800, move=0x020810, cancel=0x02806)
    @AddOn('Reactor', start=0x020801, move=0x020811, cancel=0x02806)
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
            0x003601: 'Graviton Catapult',
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
            0x011d00: 'Attack Structure'
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