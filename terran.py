def Mode(target_name, on, off):
    on_name, on_code = on
    off_name, off_code = off

    def get_class(cls):
        target = cls[target_name]
        target.__name__ = cls.__name__+target.__name
        target.abilities[off_code] = off_name
        cls.abilities[on_code] = on_name

    return get_class

def Lifts(liftoff, land):
    return Mode('Flying', on=('Liftoff', liftoff), off=('Land', land))

def Lowers(lower, raise):
    return Mode('Lowered', on=('Lower', lower), off=('Raise', raise))

def Addon(target_name, start, cancel):
    def get_class(cls):
        if isinstance(target_name, Building):
            target = target_name
        else:
            target = cls[target_name]

        cls.abilities[start] = 'Build {0} ({1})'.format(target_name, cls.__name__)
        cls.abilities[start] = 'Cancel {0} ({1})'.format(target_name, cls.__name__)

    return get_class

class TerranBuilding(Terran, Building):
    abilities = {
        0x012e00: 'Cancel build',
        0x012e01: 'Halt build',
    }

class TerranMain(TerranBuilding):
    abilities = {
        0x011710: 'Set rally point',
        0x011720: 'Set rally target',
        0x020a00: 'Train SCV',
        0x012b00: 'Cancel Production'
    }


@Lifts(liftoff=0x020000, land=0x020110)
@Transport(0x013e01, None, 0x013e33, 0x013e04)
class CommandCenter(TerranMain):
    code = 0x2d01

    class Flying(object):
        code = 0x4001

@Lifts(liftoff=0x31500, land=0x31610)
@UpgradedFrom(CommandCenter, start=0x031200, None)
class OrbitalCommand(TerranMain):
    code = 0xa001
    abilities = {
        0x010910: 'Calldown: MULE (location)',
        0x010920: 'Calldown: MULE (target)',
        0x012020: 'Calldown: Extra Supplies',
        0x013110: 'Scanner Sweep',
    }

    class Flying(object):
        code = 0xa201

@UpgradedFrom(CommandCenter, start=0x030d00, None)
class PlanetaryFortress(TerranMain):
    code = 0x9e01

@Lowers(lower=0x020c00, raise=0x020d00)
class SupplyDepot(TerranBuilding):
    code = 0x2e01

class Refinery(TerranBuilding):
    pass


@Lifts(liftoff=0x02300, land=0x020d10)
@Addon('Techlab', 0x020300, 0x02c206)
@Addon('Reactor', 0x020301, 0x02c206)
class Barracks(TerranBuilding):
    code = 0x3001

    class TechLab(Addon):
        code = 0x00
        upgrades = {

        }

    class Reactor(Addon):
        code = 0x01

    @Addon(TechLab, 0x020300, 0x02c206)
    @Addon(Reactor, 0x020301, 0x02c206)
    class Flying(object):
        code = 0x020401


class EngineeringBay(TerranBuilding):
    upgrades = {

    }

class MissileTurret(TerranBuilding, Attacker):
    pass

@Transport(0x00,0x01,0x02,0x03)
class Bunker(TerranBuilding, Attacker):
    abilities = {
        0x02390: 'Salvage',
    }

class RadarTower(TerranBuilding):
    pass

class GhostAcademy(TerranBuilding):
    upgrades = {

    }

@Lifts(0x01,0x02)
@Addon('Techlab', 0x020300, 0x02c206)
@Addon('Reactor', 0x020301, 0x02c206)
class Factory(TerranBuilding):
    code = 0x3001

    class TechLab(Addon):
        code = 0x00
        upgrades = {

        }

    class Reactor(Addon):
        code = 0x01

    @Addon(TechLab, 0x020300, 0x02c206)
    @Addon(Reactor, 0x020301, 0x02c206)
    class Flying(object):
        code = 0x020401

@Lifts(0x01,0x02)
@Addon('Techlab', 0x020300, 0x02c206)
@Addon('Reactor', 0x020301, 0x02c206)
class Starport(TerranBuilding):
    code = 0x3001

    class TechLab(Addon):
        code = 0x00
        upgrades = {

        }

    class Reactor(Addon):
        code = 0x01

    @Addon(TechLab, 0x020300, 0x02c206)
    @Addon(Reactor, 0x020301, 0x02c206)
    class Flying(object):
        code = 0x020401

class Armory(TerranBuilding):
    code = 0x03093
    upgrades = {

    }

class FusionCore(TerranBuilding):
    code = 0x0983
    upgrades = {

    }


class SCV(Terran, Mechanical):
    code = 0x08372

    abilities = {

    }

    builds = {

    }

class Marine(Terran, Bio, Army):
    code = 0x8037
    abilities = {

    }

class Maurader(Terran, Bio, Army):
    code = 0x9389
    abilities = {

    }

@Cloaks(0x03980,0x0892)
@Channels('Call down Nuke', 0x0983, 0x8938)
class Ghost(Terran, Bio, Army):
    code = 0x83839
    abilities = {

    }


@Mode('Assault',0x091,0x803)
class Viking(Terran, Mechanical, Army):
    code = 0x8793

    class Assault(Terran, Mechanical, Army):
        code = 0x8803

@Mode('Siege', 0x0893, 0x893)
class SiegeTank(Terran, Mechanical, Army):
    code = 0x0938

    class Siege(Terran, Mechanical, Army):
        code = 0x8983

@Channels('250mm Cannons',0x893,0x89)
class Thor(Terran, Mechanical, Army):
    code = 0x03083
