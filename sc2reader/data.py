import re

from .utils import TimeDict

OBJECTTYPE_CODES = {}
ABILITIES = {}

def _uncamel_case(name):
    """Turn 'CamelCase' into 'Camel Case'"""
    return re.sub(r'(?<=.)([A-Z])', r' \1', name)

def _make_underscored(name):
    return '_'.join(name.lower().split(' '))

class MetaGameObject(type):
    
    def __new__(cls, name, bases, dct):
        code = dct.pop('code', None)
        if code and code not in OBJECTTYPE_CODES:

            def _get_abilities(cls_data, cls_bases, ability_type='abilities'):
                abilities = cls_data.get(ability_type, {})
                for base in cls_bases:
                    abilities.update(_get_abilities(base.__dict__, base.__bases__, ability_type=ability_type))
                return abilities

            data = {
                'name': dct.get('name', False) or _uncamel_case(name),
            }
            for (key,value) in dct.items():
                if callable(value):
                    data[key] = value
            ability_dispatch = {}

            def _dispatch_ability(abilities, ability_function, prefix=False):
                for (ab_code, ab_name) in abilities.items():
                    func_name = _make_underscored(ab_name)
                    if prefix:
                        func_name = '%s_%s' % (prefix, func_name)
                    # function is overrideable
                    func = dct.get(func_name, False) or ability_function
                    ability_dispatch[ab_code] = func_name
                    def _do_ability(ab):
                        def _do(self, timestamp):
                            return func(self, timestamp, ab)
                        return _do
                    data[func_name] = _do_ability(ab_name)

            def _ability(self, timestamp, ability):
                pass
            def _move(self, timestamp, ability):
                pass
            def _cast(self, timestamp, spell):
                self.spell_casts.append((timestamp, spell,))
            def _research(self, timestamp, research):
                self.researched.append((timestamp, research,))
            def _train(self, timestamp, unit):
                self.trained.append((timestamp, unit,))
            def _build(self, timestamp, building):
                self.built.append((timestamp, building,))

            _dispatch_ability(_get_abilities(dct, bases), _ability)
            _dispatch_ability(_get_abilities(dct, bases, ability_type='move'), _move)
            _dispatch_ability(_get_abilities(dct, bases, ability_type='spells'), _cast, prefix='cast')
            _dispatch_ability(_get_abilities(dct, bases, ability_type='research'), _research, prefix='research')
            _dispatch_ability(_get_abilities(dct, bases, ability_type='train'), _train, prefix='train')
            _dispatch_ability(_get_abilities(dct, bases, ability_type='build'), _build, prefix='build')

            kls = super(MetaGameObject, cls).__new__(cls, name, bases, data)

            for (key, value) in dct.items():
                if hasattr(value, 'code'): # mode/upgrade
                    mode_code = value.code
                    if hasattr(value, 'mode') or hasattr(value, 'upgrade'):
                        mode_codes = value.mode if hasattr(value, 'mode') else value.upgrade
                        is_upgrade = hasattr(value, 'upgrade')
                        mode_dct = dict(value.__dict__.items())
                        mode_base = GameObject
                        if mode_dct.get('inherit', False):
                            mode_base = kls
                        mode_bases = tuple([mode_base,] + list(value.__bases__))
                        mode = cls.__new__(cls, value.__name__, mode_bases, mode_dct)

                        def _morph_to(self, timestamp):
                            if not is_upgrade: # upgrades cost money, which we can't track
                                self.morph_to(mode, timestamp)

                        def _morph_back(self, timestamp):
                            if not is_upgrade:
                                self.morph_to(kls, timestamp)

                        def _dispatch_morph(morph_code, morph_cls, func_name, func):
                            if not hasattr(morph_cls, func_name):
                                setattr(morph_cls, func_name, func)
                            ability_dispatch[morph_code] = func_name

                        mode_codes_to = mode_codes[0]
                        if not isinstance(mode_codes_to, list):
                            mode_codes_to = [mode_codes[0],]
                        for mode_code in mode_codes_to:
                            _dispatch_morph(mode_code, kls, 'morph_to_%s' % (_make_underscored(mode.name),), _morph_to)
                        if mode_codes[1]: # cancel
                            _dispatch_morph(mode_codes[1], mode, 'morph_to_%s' % (_make_underscored(kls.name),), _morph_back)
                        if mode_codes[2]: # cancel
                            _dispatch_morph(mode_codes[2], kls, 'cancel_morph_to_%s' % (_make_underscored(mode.name),), _morph_back)

                        OBJECTTYPE_CODES[mode_code] = mode

            ABILITIES.update(ability_dispatch)

            # Register it
            OBJECTTYPE_CODES[code] = kls
        else:
            kls = super(MetaGameObject, cls).__new__(cls, name, bases, dct)

        return kls

class GameObject(object):
    __metaclass__ = MetaGameObject

    abilities = {
        0x3700: 'Right click',
        0x5700: 'Right click in fog',
    }

    @classmethod
    def get_type(cls, code):
        return OBJECTTYPE_CODES[code]
        
    @classmethod
    def get_ability(cls, code):
        return ABILITIES[code]

    @classmethod
    def has_type(cls, code):
        return code in OBJECTTYPE_CODES

    def __init__(self, id, timestamp):
        self.id = id
        self.first_seen = None
        self.last_seen = None
        self.player = None
        self.object_types = TimeDict()
        self.object_types[timestamp] = self.__class__
        self.spell_casts = []
        self.trained = []
        self.built = []
        self.researched = []

    def name_at(self, timestamp):
        return self.__class__.name

    def visit(self, timestamp, player, object_type=None):
        self.first_seen = min(self.first_seen, timestamp) if self.first_seen else timestamp
        self.last_seen = max(self.last_seen, timestamp) if self.last_seen else timestamp

        if object_type and object_type != self.__class__:
            # TODO siege tanks should not auto-assign
            self.morph_to(object_type, timestamp)

        if not player.is_observer and not self.player:
            self.player = player

    def morph_to(self, cls, timestamp):
        self.object_types[timestamp] = cls
        self.__class__ = cls

    def alive_at(self, frame):
        return (self.first_seen and self.first_seen <= frame) and (self.last_seen and (self.last_seen > frame))
    def alive_between(self, start, end):
        return self.alive_at(start) or self.alive_at(end)

    def __repr__(self):
        return '%s (%s)' % (self.name, hex(self.id))

class Terran(object):
    race = 'Terran'
class Protoss(object):
    race = 'Protoss'
class Zerg(object):
    race = 'Zerg'

class Moveable(object):
    move = {
        0x002400: 'Stop',
        0x002620: 'Follow',
    }
class Unit(Moveable):
    move = {
        0x002610: 'Move to',
        0x002611: 'Patrol',
        0x002602: 'Hold position',
    }
class Army(object):
    move = {
        0x002602: 'Hold position',
        0x002a10: 'Attack move',
        0x002a20: 'Attack object',
    }
class SpellCaster(object):
    move = {
        0x002613: 'Scan move', # attack move for units without attack
        0x002623: 'Scan target', # attack move for units without attack
    }

class Building(object):
    abilities = {
        0x013000: 'Cancel build',
        0x013001: 'Halt build',
    }
class Production(Building):
    abilities = {
        0x011710: 'Set rally point',
        0x011720: 'Set rally target',

        0x012c00: 'Cancel', # Generic ESC cancel
        0x012c31: 'Cancel unit', # Cancel + build id
    }
    pass
class Main(Building):
    pass

#
# Some useful for stats and other things
#
class Worker(Unit):
    pass
class Scout(object):
    pass
class Detector(object):
    pass

#
# Decorators
#

def Mode(mode_code, return_code, cancel_code=None):
    def get_class(cls):
        cls.mode = (mode_code, return_code, cancel_code)
        cls.inherit = getattr(cls, 'inherit', False)
        return cls
    return get_class

def Upgrade(upgrade_code, cancel_code):
    def get_class(cls):
        cls.upgrade = (upgrade_code, None, cancel_code)
        cls.inherit = getattr(cls, 'inherit', False)
        return cls
    return get_class

def Cloak(cloak_code, decloak_code):
    def _class(cls):
        cls.cloak = lambda self, timestamp: None
        cls.decloak = lambda self, timestamp: None
        ABILITIES[cloak_code] = 'cloak'
        ABILITIES[decloak_code] = 'decloak'
        return cls
    return _class

# all, all(moving), unload unit, load unit
def Transport(all_code, all_moving_code, unload_unit_code, load_unit_code):
    def get_class(cls):
        if all_code:
            ABILITIES[all_code] = 'unload_all'
            cls.unload_all = lambda self, timestamp: None
        if all_moving_code:
            ABILITIES[all_moving_code] = 'unload_all_while_moving'
            cls.unload_all_while_moving = lambda self, timestamp: None
        if unload_unit_code:
            ABILITIES[unload_unit_code] = 'unload_unit'
            cls.unload_unit = lambda self, timestamp: None
        if load_unit_code:
            ABILITIES[load_unit_code] = 'load_unit'
            cls.load_unit = lambda self, timestamp: None
        return cls
    return get_class

#
# This is going to take a while
#

class SCV(GameObject, Worker, Terran):
    code = 0x4901
    name = 'SCV'
    abilities = {
        0x012820: 'Gather resources',
        0x012801: 'Return cargo',
        0x013100: 'Toggle Auto-Repair',
        0x013120: 'Repair',
        0x01f206: 'Halt',
    }
    build = {
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
class MULE(GameObject, Worker, Terran):
    code = 0xb901
    name = 'MULE'
    abilities = {
        0x003900: 'Toggle Auto-Repair',
        0x003920: 'Repair',
    }
# Barracks
class Marine(GameObject, Army, Terran):
    code = 0x4c01
    abilities = {
        0x013400: 'Use Stimpack (mixed)',
    }
class Marauder(GameObject, Unit, Army, Terran):
    code = 0x4f01
    abilities = {
        0x013400: 'Use Stimpack (mixed)',
        0x012100: 'Use Stimpack',
    }
class Reaper(GameObject, Unit, Army, Terran):
    code = 0x4d01

@Cloak(0x013500, 0x013501)
class Ghost(GameObject, Unit, Army, Terran):
    code = 0x4e01
    abilities = {
        0x003200: 'Hold fire',
        0x003300: 'Weapons free',
        0x031f01: 'Cancel Tactical Nuclear Strike',
    }
    spells = {
        0x032210: 'EMP Round',
        0x013620: 'Sniper Round',
        0x031f10: 'Tactical Nuclear Strike',
    }

# Factory
class Hellion(GameObject, Unit, Army, Terran):
    code = 0x5101

class SiegeTank(GameObject, Unit, Army, Terran):
    code = 0x3d01
    @Mode(0x013800, 0x013900)
    class Sieged(Army):
        code = 0x3c01

class Thor(GameObject, Unit, Army, Terran):
    code = 0x5001
    spells = {
        0x012320: '250mm Strike Cannons',
    }

# Starport
class Viking(GameObject, Unit, Army, Terran):
    code = 0x3e01
    @Mode(0x013e00, 0x013f00)
    class Landed(Unit, Army):
        code = 0x3f01

# all, all(moving), unload unit, load unit
@Transport(0x013b12, 0x013b22, 0x013b33, 0x013b20)
class Medivac(GameObject, Unit, Army, Terran):
    code = 0x5201
    spells = {
        0x013700: 'Toggle Auto-Heal',
        0x020803: 'Heal'
    }

class Raven(GameObject, Unit, SpellCaster, Terran, Detector):
    code = 0x5401
    spells = {
        0x033b10: 'Auto Turret',
        0x003e10: 'Point Defense Drone',
        0x010a20: 'Seeker Missile',
    }

@Cloak(0x013a00, 0x013a01)
class Banshee(GameObject, Unit, Army, Terran):
    code = 0x5301

class Battlecruiser(GameObject, Unit, Army, Terran):
    code = 0x5501
    spells = {
        0x013d20: 'Yamato Cannon',
    }

# Terran GameObjects
class AutoTurret(GameObject, Terran):
    code = 0x3b01
    name = 'Auto-turret'
class PointDefenseDrone(GameObject, Terran):
    code = 0x2501

# Terran Buildings
class TerranMain(Main):
    abilities = {
        0x011910: 'Set rally point',
        0x011920: 'Set rally target',
    }
    train = {
        0x020c00: 'SCV',
    }

@Transport(0x020101, None, 0x020133, None)
class CommandCenter(GameObject, TerranMain, Production, Terran):
    code = 0x2d01
    abilities = {
        0x20104: 'Load All',
    }
    
    def load_all(self, selection):
        pass

    @Mode(0x020200, 0x020310)
    class Flying(Moveable):
        code = 0x4001

    @Upgrade(0x031400, 0x031401)
    class OrbitalCommand(TerranMain, Production, Terran):
        code = 0xa001
        spells = {
            0x010b10: 'MULE',
            0x010b20: 'MULE',
            0x012220: 'Extra Supplies',
            0x013c10: 'Scanner Sweep',
        }
        @Mode(0x031700, 0x031810)
        class Flying(Moveable):
            code = 0xa201

    @Upgrade(0x030f00, 0x030f01)
    class PlanetaryFortress(TerranMain, Production, Terran):
        code = 0x9e01
        abilities = {
            0x012e00: 'Cancel', # Generic ESC cancel (only seen at PF)
        }

class SupplyDepot(GameObject, Building, Terran):
    code = 0x2e01

    @Mode(0x020e00, 0x020f00)
    class Lowered(Building):
        code = 0x4b01

class Refinery(GameObject, Building, Terran):
    code = 0x2f01

class Barracks(GameObject, Production, Terran):
    code = 0x3001
    abilities = {
        0x02c406: 'Cancel addon',
    } 
    train = {
        0x021000: 'Marine',
        0x021001: 'Reaper',
        0x021002: 'Ghost',
        0x021003: 'Marauder',
    }
    build = {
        0x020400: 'Techlab',
        0x020401: 'Reactor',
    }
    @Mode(0x020500, 0x020d10)
    class Flying(Moveable):
        code = 0x4a01
        build = {
            0x020410: 'Techlab',
            0x020411: 'Reactor',
        }
class EngineeringBay(GameObject, Building, Terran):
    code = 0x3101
    research = {
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

@Transport(0x020001, None, 0x020033, 0x20020)
class Bunker(GameObject, Building, Terran):
    code = 0x3301
    abilities = {
        0x032100: 'Salvage',
        0x032f20: 'Attack',
        0x033000: 'Stimpack',
        0x033300: 'Stop'
    }
class SensorTower(GameObject, Building, Terran):
    code = 0x3401
class MissileTurret(GameObject, Building, Terran):
    code = 0x3201

class Factory(GameObject, Production, Terran):
    code = 0x3601
    train = {
        0x021101: 'Siege Tank',
        0x021104: 'Thor',
        0x021105: 'Hellion',
    }
    build = {
        0x020600: 'Build Techlab',
        0x020601: 'Build Reactor',
    }
    abilities = {
        0x020700: 'Set rally point',
        0x02c606: 'Cancel addon',
    }
    @Mode(0x020700, 0x020a10)
    class Flying(Moveable):
        code = 0x4701
        build = {
            0x020610: 'Techlab',
            0x020611: 'Rector',
        }

class GhostAcademy(GameObject, Building, Terran):
    code = 0x3501
    abilities = {
        0x021500: 'Arm silo with Nuke',
    }
    research = {
        0x021900: 'Personal Cloaking',
        0x021901: 'Moebius Reactor',
    }

class Starport(GameObject, Production, Terran):
    code = 0x3701
    train = {
        0x021200: 'Medivac',
        0x021201: 'Banshee',
        0x021202: 'Raven',
        0x021203: 'Battlecruiser',
        0x021204: 'Viking',
    }
    build = {
        0x020800: 'Techlab',
        0x020801: 'Reactor',
    }
    abilities = {
        0x02c806: 'Cancel addon',
    }
    @Mode(0x020900, 0x020b10)
    class Flying(Moveable):
        code = 0x4801
        build = {
            0x020810: 'Techlab',
            0x020811: 'Reactor',
        }
class Armory(GameObject, Building, Terran):
    code = 0x3901
    research = {
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
class Techlab(GameObject, Building, Terran):
    code = 0x1e01
class TechlabBarracks(GameObject, Building, Terran):
    code = 0x4101
    name = "Techlab (Barracks)"
    research = {
        0x021403: 'Nitro Packs',
        0x021600: 'Stimpack',
        0x021601: 'Combat Shields',
        0x021602: 'Concussive Shells',
    }
    abilities = {
        0x012f00: 'Cancel Research',
        0x012f31: 'Cancel specific Research',
    }
class TechlabFactory(GameObject, Building, Terran):
    code = 0x4301
    name = "Techlab (Factory)"
    research = {
        0x021700: 'Siege Tech',
        0x021701: 'Infernal Pre-igniter',
        0x021702: '250mm Strike Cannons',
    }
    abilities = {
        0x012f00: 'Cancel Research',
        0x012f31: 'Cancel specific Research',
    }
class Starport(GameObject, Building, Terran):
    code = 0x4501
    name = "Techlab (Starport)"
    research = {
        0x021800: 'Cloaking Field',
        0x021802: 'Caduceus Reactor',
        0x021803: 'Corvid Rector',
        0x021806: 'Seeker Missile',
        0x021807: 'Durable Materials',
    }
    abilities = {
        0x012f00: 'Cancel Research',
        0x012f31: 'Cancel specific Research',
    }
class Reactor(GameObject, Building, Terran):
    code = 0x1f01
class Barracks(GameObject, Building, Terran):
    code = 0x4201
    name = "Reactor (Barracks)"
class Factory(GameObject, Building, Terran):
    code = 0x4401
    name = "Reactor (Factory)"
class Starport(GameObject, Building, Terran):
    code = 0x4601
    name = "Reactor (Starport)"
class FusionCore(GameObject, Building, Terran):
    code = 0x3a01
    research = {
        0x031c00: 'Weapon Refit',
        0x031c01: 'Behemoth Reactor',
    }

#
# Protoss
#
class Probe(GameObject, Worker, Protoss):
    code = 0x7001
    abilities = {
        0x012901: 'Return cargo',
    } 
    build = {
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
class Zealot(GameObject, Unit, Army, Protoss):
    code = 0x6501
class Stalker(GameObject, Unit, Army, Protoss):
    code = 0x6601
    abilities = {
        0x030b10: 'Blink',
    }
class Sentry(GameObject, Unit, Army, Protoss):
    code = 0x6901
    spells = {
        0x003f00: 'Archon',
        0x010000: 'Colossus',
        0x010100: 'High Templar',
        0x010200: 'Immortal',
        0x010300: 'Phoenix',
        0x010400: 'Probe',
        0x010500: 'Stalker',
        0x010600: 'Void Ray',
        0x010700: 'Warp Prism',
        0x010800: 'Zealot',
        0x003800: 'Guardian Shield',
        0x031910: 'Force Field',
    }
class HighTemplar(GameObject, Unit, Army, Protoss):
    code = 0x6701
    spells = {
        0x022110: 'Psionic Storm',
        0x003c20: 'Feedback',
    }
    @Upgrade(0x033c00, 0x0) # TODO: cancel code?
    class Archon(Unit, Army, Protoss):
        code = 0xa801
        abilities = {
            0x011810: 'Set rally point', # while morphing
        }

class DarkTemplar(GameObject, Unit, Army, Protoss):
    code = 0x6801
    @Upgrade(0x033c00, 0x0) # TODO: cancel code?
    class Archon(GameObject, Unit, Army, Protoss):
        code = 0xa801
class Immortal(GameObject, Unit, Army, Protoss):
    code = 0x6f01
class Colossus(GameObject, Unit, Army, Protoss):
    code = 0x1d01
class Observer(GameObject, Unit, Detector, Protoss):
    code = 0x6e01

@Transport(0x021c12, 0x021c22, 0x021c33, 0x021c20)
class WarpPrism(GameObject, Unit, Army, Protoss):
    code = 0x6d01
    @Mode(0x031a00, 0x031b00)
    class Phasing(object):
        code = 0xa401
class Phoenix(GameObject, Unit, Army, Protoss):
    code = 0x6a01
    abilities = {
        0x010c01: 'Cancel Graviton Beam',
    }
    spells = {
        0x010c20: 'Graviton Beam',
    }
class VoidRay(GameObject, Unit, Army, Protoss):
    code = 0x6c01
class Carrier(GameObject, Unit, Army, Protoss):
    code = 0x6b01
    train = {
        0x022400: 'Interceptor',
    }
class Mothership(GameObject, Unit, Army, Protoss):
    code = 0x2401
    spells = {
        0x032310: 'Vortex',
        0x003d10: 'Mass Recall',
    }
class HallucinatedImmortal(GameObject, Unit, Army, Protoss):
    code = 0x6f02
class HallucinatedColossus(GameObject, Unit, Army, Protoss):
    code = 0x1d02
class HallucinatedPhoenix(GameObject, Unit, Army, Protoss):
    code = 0x6a02
class HallucinatedVoidRay(GameObject, Unit, Army, Protoss):
    code = 0x6c02

# Buildings
class Nexus(GameObject, Main, Production, Protoss):
    code = 0x5701
    train = {
        0x022000: 'Probe',
        0x003b00: 'Mothership',
    }
    spells = {
        0x012520: 'Chrono Boost',
    }
    abilities = {
        0x011a10: 'Set rally point',
        0x011a20: 'Set rally target',
    }
class Pylon(GameObject, Building, Protoss):
    code = 0x5801
class Assimilator(GameObject, Building, Protoss):
    code = 0x5901
class Gateway(GameObject, Production, Protoss):
    code = 0x5a01
    train = {
        0x021d00: 'Zealot',
        0x021d01: 'Stalker',
        0x021d03: 'High Templar',
        0x021d04: 'Dark Templar',
        0x021d05: 'Sentry',
    }
    @Mode(0x031500, 0x031600)
    class WarpGate(Production): 
        code = 0xa101
        full_name = "Warp Gate"
        train = {
            0x030710: 'Zealot',
            0x030711: 'Stalker',
            0x030713: 'High Templar',
            0x030714: 'Dark Templar',
            0x030715: 'Sentry',
        }

class Forge(GameObject, Building, Protoss):
    code = 0x5b01
    research = {
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
class CyberneticsCore(GameObject, Building, Protoss):
    code = 0x6401
    research = {
        0x031d00: 'Air Weapons Level 1',
        0x031d01: 'Air Weapons Level 2',
        0x031d02: 'Air Weapons Level 3',
        0x031d03: 'Air Armor Level 1',
        0x031d04: 'Air Armor Level 2',
        0x031d05: 'Air Armor Level 3',
        0x031d06: 'Warp Gate',
        0x035d01: 'Hallucination',
    }
class PhotonCannon(GameObject, Building, Detector, Protoss):
    code = 0x5e01
class RoboticsFacility(GameObject, Production, Protoss):
    code = 0x6301
    train = {
        0x021f00: 'Warp Prism',
        0x021f01: 'Observer',
        0x021f02: 'Colossus',
        0x021f03: 'Immortal',
    }
class Stargate(GameObject, Production, Protoss):
    code = 0x5f01
    train = {
        0x021e00: 'Phoenix',
        0x021e02: 'Carrier',
        0x021e04: 'Void Ray',
    }
class TwilightCouncil(GameObject, Building, Protoss):
    code = 0x5d01
    research = {
        0x031e00: 'Charge',
        0x031e01: 'Blink',
    }
class FleetBeacon(GameObject, Building, Protoss):
    code = 0x5c01
    research = {
        0x003601: 'Graviton Catapult',
    }
class TemplarArchives(GameObject, Building, Protoss):
    code = 0x6001
    research = {
        0x022700: 'Khaydarin Amulet',
        0x022704: 'Psionic Storm',
    }
class DarkShrine(GameObject, Building, Protoss):
    code = 0x6101
class RoboticsBay(GameObject, Building, Protoss):
    code = 0x6201
    research = {
        0x022601: 'Gravitic Booster',
        0x022602: 'Gravitic Drive',
        0x022605: 'Extended Thermal Lance',
    }

#
# Zerg
#
class Larva(GameObject, Zerg):
    code = 0xb101
    train = {
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
class Egg(GameObject, Zerg):
    code = 0x8301

class Drone(GameObject, Worker, Zerg):
    code = 0x8401
    abilities = {
        0x022901: 'Return cargo',
        0x023600: 'Burrow',
    }
    build = {
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
    @Mode(0x023600, 0x023700)
    class Burrowed(object):
        code = 0x9001
class Queen(GameObject, Unit, Army, Zerg):
    code = 0x9a01
    spells = {
        0x033510: 'Creep Tumor',
        0x012020: 'Larva',
        0x032620: 'Transfuse',
    }
    @Mode(0x030800, 0x030900)
    class Burrowed(object):
        code = 0x9901
class Zergling(GameObject, Unit, Army, Zerg):
    code = 0x8501
    @Upgrade(0x003a00, 0x012b00)
    class BanelingCocoon(object):
        code = 0x2201
    @Mode(0x023c00, 0x023d00)
    class Burrowed(object):
        code = 0x9301
class Baneling(GameObject, Unit, Army):
    code = 0x2301
    abilities = {
        0x003500: 'Explode',
        0x011D20: 'Attack Structure'
    }
    @Mode(0x023400, 0x023500)
    class Burrowed(object):
        code = 0x8f01
class Roach(GameObject, Unit, Army, Zerg):
    code = 0x8a01
    @Mode(0x023a00, 0x023b00)
    class Burrowed(Moveable):
        code = 0x9201
        move = {
            0x033200: 'Stop', # XXX what else?
        }
class Hydralisk(GameObject, Unit, Army, Zerg):
    code = 0x8701
    @Mode(0x023800, 0x023900)
    class Burrowed(object):
        code = 0x9101
class Infestor(GameObject, Unit, Army, Zerg):
    code = 0x8b01
    spells = {
        0x003710: 'Fungal Growth',
        0x011e10: 'Infested Terran',
        0x011f20: 'Neural Paraiste',
    }
    @Mode(0x030c00, 0x030d00)
    class Burrowed(Moveable):
        code = 0x9b01
class Ultralisk(GameObject, Unit, Army, Zerg):
    code = 0x8901
    @Mode(0x031200, 0x031300)
    class Burrowed(object):
        code = 0x9f01

class Broodling(GameObject, Unit, Zerg):
    code = 0xcf01
class Changeling(GameObject, Unit, Zerg):
    code = 0x2601
    # TODO insta-change between them 
class ChangelingZealot(GameObject):
    code = 0x2701
class ChangelingMarine(GameObject):
    code = 0x2801
    description = 'Marine'
class ChangelingMarineShield(GameObject):
    code = 0x2901
    description = 'Marine'
class ChangelingZergling(GameObject):
    code = 0x2a01
    description = 'Zergling'
class ChangelingZerglingWings(GameObject):
    code = 0x2b01
    description = 'Zergling'

class InfestedTerranEgg(GameObject, Zerg):
    code = 0xb001
    @Upgrade(0x0, 0x0) # TODO codes?
    class InfestedTerran(Unit, Army):
        code = 0x2101
        @Mode(0x0, 0x0) # TODO codes?
        class Burrowed(object):
            code = 0x9401

@Transport(0x030a01, None, 0x030a33, 0x030a20)
class NydusWorm(GameObject, Building, Zerg):
    code = 0xa901

@Transport(0x030412, 0x030422, 0x030433, 0x030404)
class Overlord(GameObject, Unit, Zerg):
    code = 0x8601
    abilities = {
        0x033400: 'Generate Creep',
        0x033401: 'Stop generating Creep',
        0x030401: 'Unload all at',
    }
    @Mode(0x030e00, 0x030e01)
    class OverseerCocoon(object):
        code = 0x9c01
class Overseer(GameObject, Unit, Detector):
    code = 0x9d01
    spells = {
        0x011000: 'Changeling',
        0x040320: 'Contaminate',
    }
class Mutalisk(GameObject, Unit, Army, Zerg):
    code = 0x8801
class Corruptor(GameObject, Unit, Army, Zerg):
    code = 0x8c01
    spells = {
        0x003120: 'Corruption',
    }
    @Mode(0x023300, 0x023301)
    class BroodLordCocoon(object):
        code = 0x8d01
class BroodLord(GameObject, Unit, Army):
    code = 0x8e01
# Buildings
class SpineCrawler(GameObject, Building, Zerg):
    code = 0x7e01
    @Mode(0x033600, 0x033810, 0x033801)
    class Uprooted(object):
        code = 0xa601
class SporeCrawler(GameObject, Building, Zerg):
    code = 0x7f01
    @Mode(0x033700, 0x033910, 0x033901)
    class Uprooted(object):
        code = 0xa701

class ZergMain(Production, Main):
    abilities = {
        0x011b11: 'Set worker rally point',
        0x011b21: 'Set worker rally target',
        0x011b10: 'Set unit rally point',
        0x011b20: 'Set unit rally target',
    }
    train = {
        0x032400: 'Queen',
    }
    research = {
        0x022e03: 'Burrow',
    }
class Hatchery(GameObject, ZergMain, Zerg):
    code = 0x7201
    @Upgrade(0x022b00, 0x022b01)
    class Lair(ZergMain):
        code = 0x8001
        research = {
            0x022e01: 'Pneumatized Carapace',
            0x022e02: 'Ventral Sacs',
        }
        @Upgrade(0x022c00, 0x022c01)
        class Hive(object):
            code = 0x8101
            inherit = True

class Extractor(GameObject, Building, Zerg):
    code = 0x7401
class SpawningPool(GameObject, Building, Zerg):
    code = 0x7501
    research = {
        0x022f00: 'Adrenal Glands',
        0x022f01: 'Metabolic Boost',
    }
class EvolutionChamber(GameObject, Building, Zerg):
    code = 0x7601
    research = {
        0x022a00: 'Melee Attacks Level 1',
        0x022a01: 'Melee Attacks Level 2',
        0x022a02: 'Melee Attacks Level 3',
        0x022a03: 'Ground Carapace Level 1',
        0x022a04: 'Ground Carapace Level 2',
        0x022a05: 'Ground Carapace Level 3',
        0x022a06: 'Missile Attacks Level 1',
        0x022a07: 'Missile Attacks Level 2',
        0x026a00: 'Missile Attacks Level 3',
    }
class RoachWarren(GameObject, Building, Zerg):
    code = 0x7d01
    research = {
        0x011c01: 'Glial Reconstitution',
        0x011c02: 'Tunneling Claws',
    }
class BanelingNest(GameObject, Building, Zerg):
    code = 0x7c01
    research = {
        0x031100: 'Centrifugal Hooks',
    }
class CreepTumor(GameObject, Building, Zerg):
    code = 0x7301
    abilities = { 
        0x033a10: 'Spawn Creep Tumor',
        0x03fa06: 'Cancel Creep Tumor',
    }
class BurrowedCreepTumor(GameObject, Building, Zerg):
    code = 0xa501
    abilities = { 
        0x033a10: 'Spawn Creep Tumor',
        0x03fa06: 'Cancel Creep Tumor',
    }
class HydraliskDen(GameObject, Building, Zerg):
    code = 0x7701
    research = {
        0x023002: 'Grooved Spines',
    }
class InfestationPit(GameObject, Building, Zerg):
    code = 0x7a01
    research = {
        0x031002: 'Pathogen Glands',
        0x031003: 'Neural Parasite',
    }
class NydusNetwork(GameObject, Building, Zerg):
    code = 0x7b01
    abilities = {
        0x033d10: 'Spawn Nydus Worm',
    }
class Spire(GameObject, Building, Zerg):
    code = 0x7801
    research = {
        0x023100: 'Flyer Attacks Level 1',
        0x023101: 'Flyer Attacks Level 2',
        0x023102: 'Flyer Attacks Level 3',
        0x023103: 'Flyer Carapace Level 1',
        0x023104: 'Flyer Carapace Level 2',
        0x023105: 'Flyer Carapace Level 3',
    }
    @Upgrade(0x022d00, 0x022d01)
    class GreaterSpire(object):
        code = 0x8201
        inherit = True

class UltraliskCavern(GameObject, Building, Zerg):
    code = 0x7901
    research = {
        0x012602: 'Chitinous Plating',
    }

#
# Rest
#

class MengskStatue(GameObject):
    code = 0x11301
    name = "Mengsk Statue"
class MengskStatue2(GameObject):
    code = 0x11201
    name = "Mengsk Statue"
class Statue1(GameObject):
    code = 0x11401
    name = "The Gift of Freedom (Mengsk Statue Alone)"
class Statue2(GameObject):
    code = 0x11601
    name = "The Wolves of Korhal (Wolf Statue)"
class GloryOfTheDominion(GameObject):
    code = 0x11501
    name = "Glory of the Dominion (Mengsk Statue)"
class CapitolStatue(GameObject):
    code = 0x11701
    name = "Capitol Statue (Globe Statue)"

class Scantipede(GameObject):
    code = 0xeb01
class Urubu(GameObject):
    code = 0xe201
class FemaleKarak(GameObject):
    code = 0xe401
class FemaleUrsadak(GameObject):
    code = 0xe601
class FemaleUrsadak2(GameObject):
    code = 0xe901
    name = "Female Ursadak (Exotic)"
class Lyote(GameObject):
    code = 0xe101
class UrsadakCalf(GameObject):
    code = 0xe701
class Automaton2000(GameObject):
    code = 0xea01
class MaleKarak(GameObject):
    code = 0xe301
class MaleUrsadak(GameObject):
    code = 0xe501
class MaleUrsadak2(GameObject):
    code = 0xe801
    name = "Male Ursadak (Exotic)"

class Debris1(GameObject):
    code = 0x10601
    name = "Destructible Debris (Braxis Alpha)"
class Debris2(GameObject):
    code = 0x10901
    name = "Destructible Debris"
class Debris3(GameObject):
    code = 0x10801
    name = "Destructible Debris"
class Debris4(GameObject):
    code = 0x10701
    name = "Destructible Debris (Braxis Alpha)"

class Rock1(GameObject):
    code = 0x10a01
    name = "Destructible Rock"
class Rock2(GameObject):
    code = 0x10c01
    name = "Destructible Rock"
class Rock3(GameObject):
    code = 0x10e01
    name = "Destructible Rock"
class Rock4(GameObject):
    code = 0x10b01
    name = "Destructible Rock"
class Rock5(GameObject):
    code = 0x10d01
    name = "Destructible Rock"
class Rock6(GameObject):
    code = 0x10f01
    name = "Destructible Rock"
class Rock7(GameObject):
    code = 0x11101
    name = "Destructible Rock"
class Rock8(GameObject):
    code = 0x11001
    name = "Destructible Rock"

class Beacon(GameObject):
    code = 0xdb01
    name = "Beacon (Protoss Large)"
class Beacon2(GameObject):
    code = 0xdd01
    name = "Beacon (Terran Large)"
class Beacon3(GameObject):
    code = 0xdf01
    name = "Beacon (Zerg Large)"
class Beacon4(GameObject):
    code = 0xdc01
    name = "Beacon (Protoss Small)"
class Beacon5(GameObject):
    code = 0xde01
    name = "Beacon (Terran Small)"
class Beacon6(GameObject):
    code = 0xe001
    name = "Beacon (Zerg Small)"

class RichMineralField(GameObject):
    code = 0xab01
class MineralField(GameObject):
    code = 0xf101
class VespeneGeyser(GameObject):
    code = 0xf201
class SpacePlatformGeyser(GameObject):
    code = 0xf301
    full_name = "Space Platform Geyser"
class RichVespeneGeyser(GameObject):
    code = 0xf401
    
# The following mineral field and vespene geyser codes were found on the 'Agria Valley' map
class MineralField2(GameObject):
    code = 0xf801
    name = 'Mineral Field'
class VespeneGeyser2(GameObject):
    code = 0xf901
    name = 'Vespene Geyser'

class XelnagaTower(GameObject):
    code = 0xad01
    name = "Xel'naga Tower"

class Garbage(GameObject):
    code = 0x10201
class Garbage2(GameObject):
    code = 0x10301
    name = "Garbage (Large)"
