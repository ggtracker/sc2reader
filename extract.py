import zlib, sys, pprint
from sc2reader.utils import ReplayBuffer
from sc2reader.data.build19595 import Data_19595 as DataObject

unitData = DataObject()

races = {'Prot':'Protoss','Zerg':'Zerg','Terr':'Terran','RAND':'Random'}
data_names = [
    'R',
    'U',
    'S',
    'O',
    'AUR',
    'RCR',
    'WC',
    'UT',
    'KUC',
    'SB',
    'SRC',
    
]
data_names_pretty = [
    'Resources',
    'Units',
    'Structures',
    'Overview',
    'Average Unspent Resources',
    'Resource Collection Rate',
    'Workers Created',
    'Units Trained',
    'Killed Unit Count',
    'Structures Built',
    'Structures Razed Count'
]
# Obviously not complete
abilities = {
    # Protoss
    ## Twilight
    0x5902 : 'Blink',
    # Charge
    
    ## Cyber core
    0x5602 : 'Warp Gate',
    0x5702 : 'Hallucination',
    # Air Weapons 1-3
    # Air Armor 1-3
    # Hallucination

    ## Robo bay
    # Obs, speed
    # Prism, speed
    0x3402 : 'Extended Thermal Lance',
    
    #Zerg
    ## Pool
    0x4402 : 'Metabolic Boost',
    # Adrenal glands
    
    ## Evo. chamber
    0x3a02 : 'Zerg Ground Carapace Level 1',
    0x3b02 : 'Zerg Ground Carapace Level 2', #extrapolated
    0x3c02 : 'Zerg Ground Carapace Level 3', #extrapolated
    0x3d02 : 'Zerg Missile Attacks Level 1',
    0x3e02 : 'Zerg Missile Attacks Level 2', #extrapolated
    0x3f02 : 'Zerg Missile Attacks Level 3', #extrapolated
    
    ## Lair
    0x4202 : 'Burrow',
    
    #Terran
    ## Factory tech lab
    0x1402 : 'Siege tech'
    }
lobby_properties = {
    3000 : 'game_speed',
    2001 : 'game_type', #1v1/2v2/3v3/4v4/5v5/6v6/FFA
    3010 : 'unknown1', #yes/no
    3006 : 'unknown2', #3/5/7/10/15/20/25/30
    1001 : 'unknown3', #yes/no
    1000 : 'unknown4', #Dflt
    2000 : 'unknown5', #t2/t3/FFA/Cust
    3009 : 'lobby_type' #Priv/Pub/Amm (Auto MatchMaking)
    
}
player_properties = {
    500 : 'slot_state', #Clsd/Open/Humn/Comp
    3001 : 'race',
    3003 : 'energy',
    3002 : 'color',
    3004 : 'difficulty',
    3008 : 'nonplayer_mode' #Obs/Ref        
}

def getRealm(str):
    return ""
def loadPlayerPropTemplate(prop_struct):
    ret = dict()
    for prop in prop_struct:
        if not prop[0][1] in player_properties:
            continue
        
        ret[prop[0][1]] = [o[0] for o in prop[1]]
    return ret
def loadLobbyPropTemplate(prop_struct):
    ret = dict()
    for prop in prop_struct:
        if not prop[0][1] in lobby_properties:
            continue
        ret[prop[0][1]] = [o[0] for o in prop[1]]
    return ret
def getLobbyProperties(prop_struct, prop_template):
    ret = dict()
    for p in prop_struct:
        if not p[0][1] in prop_template:
            continue
        ret[lobby_properties[p[0][1]]] =(
            prop_template[p[0][1]][p[1][0]])
    return ret

def getLobby(data):
    props = loadLobbyPropTemplate(data[0][5])
    
    return {
        'properties':getLobbyProperties(data[0][6][6], props)
            }

def getPlayerProperties(pindex, prop_struct, prop_template):
    ret = dict()
    for p in prop_struct:
        if not p[0][1] in prop_template:
            continue
        ret[player_properties[p[0][1]]] =(
            prop_template[p[0][1]][p[1][pindex][0]])
    return ret

def getPlayers(data):

    props = loadPlayerPropTemplate(data[0][5])

    players = []
    parr = data[0][3]
    for i in range(16):
        if not (parr[i][0][1] == 0):
            player = getPlayer(data, i)
            player['properties'] = getPlayerProperties(i, data[0][6][6], props)
            players.append(player)

    return players
def getIncomeGraph(data, index):
    return getGraph(data[4][0][1][1], index)
def getArmyGraph(data, index):
    return getGraph(data[4][0][2][1], index)
def getGraph(graph, index):
    return [(o[2], o[0]) for o in graph[index]] 
def getPlayer(data, index):
    pinfo = data[0][3][index]
    pdata = data[3][0]

    player = {
        'id': "{}/{}/{}".format(getRealm(pinfo[0][1][0][1]), pinfo[0][1][0][2], pinfo[0][1][0][3]),
        'race' : races[pinfo[2]]
        }

    stats = {}

    for i in range(len(pdata)):
        stats[data_names[i]] = pdata[i][1][index][0][0]
    stats[data_names[len(pdata)]] = data[4][0][0][1][index][0][0]
    player['stats'] = stats
    player['graphs'] = {}
    player['graphs']['income'] = getIncomeGraph(data, index)
    player['graphs']['army'] = getArmyGraph(data, index)

    return player
def flip_int(num, b):
    """
    Flips the b first bytes in num
    Example:
    (0x12345, 3) -> 0x452301
    (0x00112233, 4) -> 0x33221100
    """
    o = 0
    for i in range(b/2):
        o |= ((num & (0xff << i*8)) << (b-(2*i+1))*8)
        o |= ((num & (0xff << (b-(i+1))*8)) >> (b-(2*i+1)) * 8)
    if b % 2 == 1:
        o |= (num & (0xff << (b/2)*8))
    return o
    
def toTime(bo_time):
    return (bo_time >> 8) / 16
def toUnit(bo_unit):
    #print(hex(flip_int(bo_unit, 4)))
    i = ((bo_unit & 0xff) << 8) | 0x01
    if bo_unit >> 24 == 1:
        return {'name':unitData.type(i).name, 'type':hex(i), 'id':hex(bo_unit)}
    return None
def toAbility(bo_ability):
    #print(hex(flip_int(bo_unit, 4)))
    i = ((bo_ability & 0xff) << 8) | 0x02
    if bo_ability >> 24 == 2:
        return {'name':abilities[i] if i in abilities else "Unknown ability ({})".format(hex(i)), 'type':hex(i), 'id':hex(bo_ability)}
        
    return None
def getBuildOrder(unit_structs, index):
    ''' [ {supply, time, unit} ] '''
    bo = []
    for unit_struct in unit_structs:
        for u in unit_struct:
            # is unit
            if u[0][1] >> 24 == 1:
                unit = toUnit(u[0][1])
            elif u[0][1] >> 24 == 2:
                unit = toAbility(u[0][1])
            if not unit:
                print("Unknown code {}".format(u))
                continue
            for entry in u[1][index]:
                bo.append({
                        'supply' : entry[0],
                        'total_supply' : entry[1]&0xff,
                        'time' : toTime(entry[2]),
                        'time_hex' : hex(entry[2]>>8),
                        'order' : unit,
                        'build_index' : entry[1] >> 16,
                        'struct_as_hex' : {0:hex(entry[0]),
                                           1:hex(entry[1]),
                                           2:hex(entry[2]),
                                                 }
                        })
    bo.sort(key=lambda x: x['build_index'])
    return bo
def getBuildOrderOthers(struct):
    ret = list()
    for x in struct:
        if x[1][1] > 0xffff:
            ret.append({
                    'type':x[1][1],
                    'type_hex':hex(x[1][1]),
                    'player':x[2][0][1],
                    'others':[x[2][0][2],
                              #x[2][2][1], 
                              #x[2][2][2], 
                              x[4]]
                    })
    return ret

def getBuildOrders(data):
    unit_structs = [x[0] for x in data[5:]]
    unit_structs.append(data[4][0][3:])
    players = {}
    for i in range(15):
            bo = getBuildOrder(unit_structs, i)
            if len(bo) > 0:
                players[i] = bo
    all = [u for p in players for u in players[p]]
    all.sort(key=lambda x: x['build_index'])
    return [players, all, getBuildOrderOthers(data[1][0])]

def main():
    arg = sys.argv[2] if len(sys.argv) >= 3 else "pprint"
    with open(sys.argv[1],"rb") as s2gs:
        raw_data = zlib.decompress(s2gs.read()[16:])
        data = list()
        buffer = ReplayBuffer(raw_data)
        while buffer.left:
            part = buffer.read_data_struct()
            data.append(part)
                
        if arg == "players":
            pprint.PrettyPrinter(indent=2).pprint(getPlayers(data))
        elif arg == "lobby":
            pprint.PrettyPrinter(indent=2).pprint(getLobby(data))
        elif arg == "pprint":
            pprint.PrettyPrinter(indent=2).pprint(data)
        elif arg == "bo":
            pprint.PrettyPrinter(indent=2).pprint(getBuildOrders(data))
        elif arg == "bo2":
            bos = getBuildOrders(data)[0]
            players = getPlayers(data)
            for p in bos:
                print("== {} - {} ==".format(players[p]['race'], players[p]['id']))
                for u in bos[p]:
                    print("{:0>2}:{:0>2}  {:<25} {:>2}/{}".format(u['time'] / 60,
                                                    u['time'] % 60,
                                                    u['order']['name'],
                                                    u['supply'],
                                                    u['total_supply']))
main()
