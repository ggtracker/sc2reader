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

    # ???
    'Terrani': 'Terran',
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
    'rreT': 'Terran',
    'greZ': 'Zerg',
    'torP': 'Protoss',
    'DNAR': 'Random',
}
MESSAGE_CODES = {
    '0': 'All',
    '2': 'Allies',
    '128': 'Header',
    '125': 'Ping',
}
TEAM_COLOR_CODES = {
    '10ct': "Red",
    '20ct': "Blue",
    '30ct': "Teal",
    '40ct': "Purple",
    '50ct': "Yellow",
    '60ct': "Orange",
    '70ct': "Green",
    '80ct': "Pink",
    '90ct': "??",
    '01ct': "??",
    '11ct': "??",
    '21ct': "??",
    '31ct': "??",
    '41ct': "??",
    '51ct': "??",
    '61ct': "??",
}
DIFFICULTY_CODES = {
    'yEyV': 'Very easy',
    'ysaE': 'Easy',
    'ideM': 'Medium',
    'draH': 'Hard',
    'dHyV': 'Very hard',
    'asnI': 'Insane',
}
GAME_TYPE_CODES = {
    'virP': 'Private',
    'buP':  'Public',
    'mmA':  'Ladder',
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
    'AFF': 'FFA',
}
GAME_SPEED_CODES = {
    'rolS': 'Slower',
    'wolS': 'Slow',
    'mroN': 'Normal',
    'tsaF': 'Fast',
    'rsaF': 'Faster',
}
PLAYER_TYPE_CODES = {
    'nmuH': 'Human',
    'pmoC': 'Computer',
    'nepO': 'Open',
    'dslC': 'Closed',
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

# TODO: Not sure if this is a complete mapping
#
# Assuming only 1 Public Test Realm subregion on the following basis:
#
#   Q: Is there only one PTR server or there will be one for each region?
#   A: There's only one PTR server and it's located in North American.
#      There are no current plans to have multiple PTR servers.
#   Source: http://us.blizzard.com/support/article.xml?locale=en_US&articleId=36109
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

    # Korea
    'kr': {
        1: 'kr',
        2: 'tw',
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
