class MetaData(type):
    def __new__(self,clsname,bases,dct):

        #The base class is the exception to the rule
        if clsname == 'BaseData':
            return type.__new__(self,clsname,bases,dct)

        def getSC2Classes(dct):
            filter = lambda v: hasattr(v, '__bases__') and Object in v.__mro__
            return [value for key,value in dct.iteritems() if filter(value)]

        #For every class my parent has, if I don't have it, create an identical
        #class for me to have. We'll replace base references later!
        parent = bases[0]
        myClasses = [x.__name__ for x in getSC2Classes(dct)]
        for cls in getSC2Classes(parent.__dict__):
            name = cls.__name__
            if name not in myClasses:
                dct[name] = type(name, cls.__bases__, dict(cls.__dict__))

        #For all the sc2objects I have, update their base references to point
        #to my other classes. This moves the tree, not just the nodes, foward.
        #also comple the ability and type codes for mapping
        dct['types'] = dict()
        dct['abilities'] = dict()
        for cls in getSC2Classes(dct):
            #Update the base class references to this patch
            if cls.__name__ not in myClasses:
                new_bases = [dct.get(b.__name__,b) for b in cls.__bases__]
                cls.__bases__ = tuple(new_bases)

            #Collect the type code
            if 'code' in cls.__dict__:
                dct['types'][cls.code] = cls

            #Collect the ability codes
            if 'abilities' in cls.__dict__:
                for code, name in cls.abilities.iteritems():
                    dct['abilities'][code] = name

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

        return type.__new__(meta,name,bases,dct)

#All data is either an object or an ability
class Object(object):
    __metaclass__ = MetaObject
    def __init__(self, id, timestamp):
        self.id = id

    def visit(self,frame,player,object_type=None):
        pass

    def __str__(self):
        return "{0} [{1}]".format(self.name,self.id)

class BaseData(object):
    __metaclass__ = MetaData

    @classmethod
    def type(self, type_code):
        return self.types[type_code]

    @classmethod
    def ability(self, ability_code):
        return self.abilities[ability_code]

#1.3.3.18574
"""
class Data(BaseData):
    class Unit(Object):
        pass

    class Worker(Object):
        abilities = {
            0x000136: 'Gather Resources',
        }

    class Larvae(Object):
        code = 0xb101
        abilities = {
            0x320100: "Morph Drone",
            0x320102: "Morph Overlord",
        }

    class Extractor(Object):
        code = 0x7401
        abilities = {
            0x700000: "Cancel Mutation",
        }

    class SpawningPool(Object):
        code = 0x7501

    class Egg(Object):
        code = 0x8301

    class Overlord(Object):
        code = 0x8601

    class Drone(Worker):
        code = 0x8401
        abilities = {
            0x280142: 'Mutate Extractor',
            0x280123: 'Mutate Spawning Pool',
        }

    class Hatchery(Object):
        code = 0x7201

    class MineralPatch(Object):
        code = 0x17c
"""

class Protoss(object):
    pass

class Zerg(object):
    pass

class Terran(object):
    pass

class Main(object):
    pass

class Resource(Object):
    pass

class Building(Object):
    pass



class Unit(Object):
    pass

class MineralPatch(Resource):
    pass

class VespeneGeyser(Resource):
    pass

#1.4.0.19679
class Data_18092(BaseData):

    class Worker(Unit):
        abilities = {
            0x0037: 'Right Click',
        }

    class Probe(Protoss, Worker):
        code = 0x7001
        abilities = {
            0x1b0211: "Warp in Pylon",
            0x1b0213: "Warp in Gateway",
            0x1b0222: "Warp in Assimilator",
            0x5b0216: "Warp in Cybernetics Facility",
        }

    class Nexus(Protoss, Building, Main):
        code = 0x5701
        abilities = {
            0x200200: "Build Probe",
            0x250120: "Chrono Boost",
        }

    class Assimilator(Protoss, Building):
        code = 0x0058

    class Extractor(Zerg, Building):
        code = 0x0074

    class MineralPatch1(MineralPatch):
        code = 0x00f8

    class VespeneGeyser1(VespeneGeyser):
        code = 0x00f9

    class Larvae(Object):
        code = 0xb101
        abilities = {
            0x320200: "Morph Drone",
            0x320202: "Morph Overlord",
        }

    class Egg(Object):
        code = 0x8301

    class Drone(Worker):
        code = 0x8401
        abilities = {
            0x280222: "Mutate Extractor",
            0x280210: "Mutate Spawning Pool",
        }

    class Overlord(Object):
        code = 0x8601

    class MineralPatch(Resource):
        code = 0x17c

    class Hatchery(Building, Main):
        code = 0x7201
