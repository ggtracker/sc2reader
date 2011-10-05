@Burrows(burrow=0x023a00, unburrow=0x023b00)
class Zergling(Zerg, Army):
    code = 0x8501

    class Burrowed(Zerg, Army):
        code = 0x9301

@Burrows(burrow=0x023200, unburrow=0x023300)
@MorphedFrom(Zergling, start=0x003800, cancel=0x012900)
class Baneling(Zerg, Army):
    code = 0x2301
    abilities = {

    }

    class Cocoon(Zerg, Cocoon):
        code = 0x2201

    class Burrowed(Zerg, Army):
        code = 0x8f01


@Burrows(burrow=0x09830, unburrow=0x8938)
class Roach(Zerg, Army):
    code = 0x0389

    class Burrowed(Zerg, Army):
        code = 0x0830

@Channels('Neural Parasite', 0x0803, 0x803)
class Infestor(Zerg, Army):
    code = 0x08377
    abilities = {

    }

    class Burrowed(Zerg, Army):
        code = 0x07037
        abilities = {

        }

class Corrupter(Zerg, Army):
    code = 0x0983097
    abilities = {

    }

@MorphedFrom(Corrupter, start=0x0370, cancel=0x0703)
class Broodlord(Zerg, Army):
    code = 0x8073

    class Cocoon(Zerg, Cocoon):
        code = 0x0730

@MutatedFrom(Hatchery, 0x0730, 0x0730)
@MutatedFrom(Spire, 0x0730, 0x0730)
@MutatedFrom(Lair, 0x0730, 0x0730)
