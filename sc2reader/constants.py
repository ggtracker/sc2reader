# -*- coding: utf-8 -*-

# These are found in Repack-MPQ/fileset.{locale}#Mods#Core.SC2Mod#{locale}.SC2Data/LocalizedData/Editor/EditorCategoryStrings.txt
# EDSTR_CATEGORY_Race
# EDSTR_PLAYERPROPS_RACE
# The ??? means that I don't know what language it is.
# If multiple languages use the same set they should be comma separated
LOCALIZED_RACES = {

    # enUS
    'Terran': 'Terran',
    'Protoss': 'Protoss',
    'Zerg': 'Zerg',

    # ruRU
    'Терран': 'Terran',
    'Протосс': 'Protoss',
    'Зерг': 'Zerg',

    # koKR
    '테란': 'Terran',
    '프로토스': 'Protoss',
    '저그': 'Zerg',

    # ??eu
    'Terranie': 'Terran',
    'Protosi': 'Protoss',
    'Zergi': 'Zerg',

    # zhCH
    '人类': 'Terran',
    '星灵': 'Protoss',
    '异虫': 'Zerg',

    # zhTW
    '人類': 'Terran',
    '神族': 'Protoss',
    '蟲族': 'Zerg',

    # ???
    'Terrano': 'Terran',

    # deDE
    'Terraner': 'Terran',

    # esES - Spanish
    # esMX - Latin American
    # frFR - French - France
    # plPL - Polish Polish
    # ptBR - Brazilian Portuguese
}

#
# Codes as found in bytestream
#

RACE_CODES = {
    'Terr': 'Terran',
    'Zerg': 'Zerg',
    'Prot': 'Protoss',
    'RAND': 'Random',
}
MESSAGE_CODES = {
    '0': 'All',
    '2': 'Allies',
    '128': 'Header',
    '125': 'Ping',
}
TEAM_COLOR_CODES = {
    'tc01': "Red",
    'tc02': "Blue",
    'tc03': "Teal",
    'tc04': "Purple",
    'tc05': "Yellow",
    'tc06': "Orange",
    'tc07': "Green",
    'tc08': "Light Pink",
    'tc09': "Violet",
    'tc10': "Light Grey",
    'tc11': "Dark Green",
    'tc12': "Brown",
    'tc13': "Light Green",
    'tc14': "Dark Grey",
    'tc15': "Pink",
    'tc16': "??",
}
DIFFICULTY_CODES = {
    'VyEy': 'Very easy',
    'Easy': 'Easy',
    'Medi': 'Medium',
    'Hard': 'Hard',
    'VyHd': 'Very hard',
    'Insa': 'Insane',
}
GAME_TYPE_CODES = {
    'Priv': 'Private',
    'Pub':  'Public',
    'Amm':  'Ladder',
    '':     'Single',
}
# (name, key for team ids)
GAME_FORMAT_CODES = {
    '1v1': '1v1',
    '2v2': '2v2',
    '3v3': '3v3',
    '4v4': '4v4',
    '5v5': '5v5',
    '6v6': '6v6',
    'FFA': 'FFA',
}
GAME_SPEED_CODES = {
    'Slor': 'Slower',
    'Slow': 'Slow',
    'Norm': 'Normal',
    'Fast': 'Fast',
    'Fasr': 'Faster',
}

GAME_SPEED_FACTOR = {
    'Slower':   0.6,
    'Slow':     0.8,
    'Normal':   1.0,
    'Fast':     1.2,
    'Faster':   1.4
}

PLAYER_TYPE_CODES = {
    'Humn': 'Human',
    'Comp': 'Computer',
    'Open': 'Open',
    'Clsd': 'Closed',
}
GATEWAY_CODES = {
    'US': 'Americas',
    'KR': 'Asia',
    'EU': 'Europe',
    'SG': 'South East Asia',
    'XX': 'Public Test',
}
COLOR_CODES = {
    'B4141E': 'Red',
    '0042FF': 'Blue',
    '1CA7EA': 'Teal',
    'EBE129': 'Yellow',
    '540081': 'Purple',
    'FE8A0E': 'Orange',
    '168000': 'Green',
    'CCA6FC': 'Light pink',
    '1F01C9': 'Violet',
    '525494': 'Light grey',
    '106246': 'Dark green',
    '4E2A04': 'Brown',
    '96FF91': 'Light green',
    '232323': 'Dark grey',
    'E55BB0': 'Pink'
}

## Names of the different properties found in the s2gs files lobby part
LOBBY_PROPERTY_NAMES = {
    1    : 'unknown1',       #0001/0002
    2    : 'unknown2',       #0001/0002
    500  : 'Slot type',      #Clsd/Open/Humn/Comp
    1000 : 'unknown3',       #Dflt
    1001 : 'Melee',          #no/yes  no->2000, yes->2001
    2000 : 'Custom mode',    #t2/t3/t4/t5/FFA/Cust  (tX = X teams)
    2001 : 'Melee mode',     #1v1/2v2/3v3/4v4/5v5/6v6/FFA
    2002 : '1v1 Team',       #T1/T2
    2003 : '2v2 Team',       #T1/T2/T1/T2
    2004 : '3v3 Team',       #T1/T2/T1/T2/T1/T2
    2005 : '4v4 Team',       #T1/T2/T1/T2/T1/T2/T1/T2
    2006 : 'FFA Team',       #T1/T2/T3/T4/T5/T6
    2007 : '5v5 Team',       #T1/T2/T1/T2/T1/T2/T1/T2/T1/T2
    2008 : '6v6 Team',       #T1/T2/T1/T2/T1/T2/T1/T2/T1/T2/T1/T2
    2011 : "'2 Teams' team", #(T1/T2)*6
    2012 : "'3 Teams' team", #(T1/T2/T3)*6
    2013 : "'4 Teams' team", #(T1/T2/T3/T4)*6
    2014 : "'5 Teams' team", #(T1/T2/T3/T4/T5)*6
    2017 : "FFA Team",       #T1/T2/T3/T4/T5/T6
    2018 : "'Custom' team",  #(T1/T2/T3/T4/T5/T6)*5
    3000 : 'Game speed',     #Slor/Slow/Norm/Fast/Fasr
    3001 : 'Race',           #Terr/Zerg/Prot/RAND
    3002 : 'Color',          #tc01/tc02/tc03/tc04/.../tc15
    3003 : 'Handicap',       #50/60/70/80/90/100
    3004 : 'Difficulty',     #VyEy/Easy/Medi/Hard/VyHd/Insa
    3006 : 'Game countdown', #3/5/7/10/15/20/25/30   (countdown timer in lobby (seconds))
    3007 : 'Player mode',    #Part/Watch     (Participating/Watching) Watch->3008
    3008 : 'Spectate mode',  #Obs/Ref
    3009 : 'Lobby type',     #Priv/Pub/Amm
    3010 : 'unknown4',       #no/yes   (Never required)
}

BUILD_ORDER_UPGRADES = {
    # Protoss

    ## Forge
    0x2902 : 'Protoss Ground Weapons Level 1',
    0x2a02 : 'Protoss Ground Weapons Level 2',
    0x2b02 : 'Protoss Ground Weapons Level 3',
    0x2c02 : 'Protoss Ground Armor Level 1',
    0x2d02 : 'Protoss Ground Armor Level 2',
    0x2e02 : 'Protoss Ground Armor Level 3',
    0x2f02 : 'Protoss Shields Level 1',
    0x3002 : 'Protoss Shields Level 2',
    0x3102 : 'Protoss Shields Level 3',
    ## Robo bay
    0x3202 : 'Gravitic Boosters',
    0x3302 : 'Gravitic Drive',
    0x3402 : 'Extended Thermal Lance',
    ## Cyber core
    0x5002 : 'Protoss Air Weapons Level 1',
    0x5102 : 'Protoss Air Weapons Level 2',
    0x5202 : 'Protoss Air Weapons Level 3',
    0x5302 : 'Protoss Air Armor Level 1',
    0x5402 : 'Protoss Air Armor Level 2',
    0x5502 : 'Protoss Air Armor Level 3',
    0x5602 : 'Warp Gate Research',
    0x5702 : 'Hallucination',
    ## Twilight
    0x5802 : 'Charge',
    0x5902 : 'Blink',
    ## Fleet Beacon
    0x0302 : 'Graviton Catapult',
    0x7102 : 'Anion Pulse-Crystals',

    #Zerg

    ## Roach Warren
    0x0402 : 'Gial Reconstitution',
    0x0502 : 'Tunneling Claws',
    ## Ultralisk Cavern
    0x0602 : 'Chitinous Plating',
    ## Evo. chamber
    0x3702 : 'Zerg Melee Attacks Level 1',
    0x3802 : 'Zerg Melee Attacks Level 2',
    0x3902 : 'Zerg Melee Attacks Level 3',
    0x3a02 : 'Zerg Ground Carapace Level 1',
    0x3b02 : 'Zerg Ground Carapace Level 2',
    0x3c02 : 'Zerg Ground Carapace Level 3',
    0x3d02 : 'Zerg Missile Attacks Level 1',
    0x3e02 : 'Zerg Missile Attacks Level 2',
    0x3f02 : 'Zerg Missile Attacks Level 3',
    ## Lair
    0x4002 : 'Pneumatized Carapace',
    0x4102 : 'Ventral Sacs',
    0x4202 : 'Burrow',
    ## Pool
    0x4302 : 'Adrenal Glands',
    0x4402 : 'Metabolic Boost',
    ## Hydra den
    0x4502 : 'Grooved Spines',
    ## Spire
    0x4602 : 'Zerg Flyer Attacks Level 1',
    0x4702 : 'Zerg Flyer Attacks Level 2',
    0x4802 : 'Zerg Flyer Attacks Level 3',
    0x4902 : 'Zerg Flyer Carapace Level 1',
    0x4a02 : 'Zerg Flyer Carapace Level 2',
    0x4b02 : 'Zerg Flyer Carapace Level 3',
    ## Infestation pit
    0x4c02 : 'Pathogen Glands',
    0x7202 : 'Neural Parasite',
    ## Baneling Nest
    0x4d02 : 'Centrifugal Hooks',

    #Terran
    ## Engineering bay
    0x702 : 'Hi-Sec Auto Tracking',
    0x802 : 'Terran Building Armor',
    0x902 : 'Terran Infantry Weapons Level 1',
    0xa02 : 'Terran Infantry Weapons Level 2',
    0xb02 : 'Terran Infantry Weapons Level 3',
    0xc02 : 'Neosteel Frame',
    0xd02 : 'Terran Infantry Armor Level 1',
    0xe02 : 'Terran Infantry Armor Level 2',
    0xf02 : 'Terran Infantry Armor Level 3',
    ## Barracks tech lab
    0x1002 : 'Nitro Packs',
    0x1102 : 'Stimpack',
    0x1202 : 'Combat Shields',
    0x1302 : 'Concussive Shells',
    ## Factory tech lab
    0x1402 : 'Siege Tech',
    0x1502 : 'Infernal Pre-igniter',
    0x7002 : '250mm Strike Cannons',
    ## Starport tech lab
    0x1602 : 'Cloaking Field',
    0x1702 : 'Caduceus Reactor',
    0x1902 : 'Seeker Missile',
    0x1a02 : 'Durable Materials',
    0x4e02 : 'Corvid Reactor',
    ## Fusion Core
    0x1802 : 'Behemoth Reactor',
    0x4f02 : 'Weapon Refit',
    ## Ghost Academy
    0x1b02 : 'Personal Cloaking',
    0x1c02 : 'Moebiue Reactor',
    ## Armory
    0x1d02 : 'Terran Vehicle Plating Level 1',
    0x1e02 : 'Terran Vehicle Plating Level 2',
    0x1f02 : 'Terran Vehicle Plating Level 3',
    0x2002 : 'Terran Vehicle Weapons Level 1',
    0x2102 : 'Terran Vehicle Weapons Level 2',
    0x2202 : 'Terran Vehicle Weapons Level 3',
    0x2302 : 'Terran Ship Plating Level 1',
    0x2402 : 'Terran Ship Plating Level 2',
    0x2502 : 'Terran Ship Plating Level 3',
    0x2602 : 'Terran Ship Weapons Level 1',
    0x2702 : 'Terran Ship Weapons Level 2',
    0x2802 : 'Terran Ship Weapons Level 3'
    }

# TODO: Not sure if this is a complete mapping
REGIONS = {
    # United States
    'us': {
        1: 'us',
        2: 'la',
    },

    # Europe
    'eu': {
        1: 'eu',
        2: 'ru',
    },

    # Korea - appear to both map to same place
    'kr': {
        1: 'kr',
        2: 'tw',
    },
    # Taiwan - appear to both map to same place
    'tw': {
        1: 'kr',
        2: 'tw',
    },

    # China - different url scheme (www.battlenet.com.cn)?
    'cn': {
        1: 'cn',
    },

    # South East Asia
    'sea': {
        1: 'sea',
    },

    # Public Test
    'xx': {
        1: 'xx',
    },
}
