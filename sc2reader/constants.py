# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

# These are found in Repack-MPQ/fileset.{locale}#Mods#Core.SC2Mod#{locale}.SC2Data/LocalizedData/Editor/EditorCategoryStrings.txt
# EDSTR_CATEGORY_Race
# EDSTR_PLAYERPROPS_RACE
# The ??? means that I don't know what language it is.
# If multiple languages use the same set they should be comma separated
LOCALIZED_RACES = {
    # enUS
    "Terran": "Terran",
    "Protoss": "Protoss",
    "Zerg": "Zerg",
    # ruRU
    "Терран": "Terran",
    "Протосс": "Protoss",
    "Зерг": "Zerg",
    # koKR
    "테란": "Terran",
    "프로토스": "Protoss",
    "저그": "Zerg",
    # plPL
    "Terranie": "Terran",
    "Protosi": "Protoss",
    "Zergi": "Zerg",
    # zhCH
    "人类": "Terran",
    "星灵": "Protoss",
    "异虫": "Zerg",
    # zhTW
    "人類": "Terran",
    "神族": "Protoss",
    "蟲族": "Zerg",
    # ???
    "Terrano": "Terran",
    # deDE
    "Terraner": "Terran",
    # esES - Spanish
    # esMX - Latin American
    # frFR - French - France
    # plPL - Polish Polish
    # ptBR - Brazilian Portuguese
}

MESSAGE_CODES = {"0": "All", "2": "Allies", "128": "Header", "125": "Ping"}


GAME_SPEED_FACTOR = {
    "WoL": {"Slower": 0.6, "Slow": 0.8, "Normal": 1.0, "Fast": 1.2, "Faster": 1.4},
    "HotS": {"Slower": 0.6, "Slow": 0.8, "Normal": 1.0, "Fast": 1.2, "Faster": 1.4},
    "LotV": {"Slower": 0.2, "Slow": 0.4, "Normal": 0.6, "Fast": 0.8, "Faster": 1.0},
}

GATEWAY_CODES = {
    "US": "Americas",
    "KR": "Asia",
    "EU": "Europe",
    "SG": "South East Asia",
    "XX": "Public Test",
}


GATEWAY_LOOKUP = {0: "", 1: "us", 2: "eu", 3: "kr", 5: "cn", 6: "sea", 98: "xx"}

COLOR_CODES = {
    "B4141E": "Red",
    "0042FF": "Blue",
    "1CA7EA": "Teal",
    "EBE129": "Yellow",
    "540081": "Purple",
    "FE8A0E": "Orange",
    "168000": "Green",
    "CCA6FC": "Light Pink",
    "1F01C9": "Violet",
    "525494": "Light Grey",
    "106246": "Dark Green",
    "4E2A04": "Brown",
    "96FF91": "Light Green",
    "232323": "Dark Grey",
    "E55BB0": "Pink",
    "FFFFFF": "White",
    "000000": "Black",
}

COLOR_CODES_INV = dict(zip(COLOR_CODES.values(), COLOR_CODES.keys()))

SUBREGIONS = {
    # United States
    "us": {1: "us", 2: "la"},
    # Europe
    "eu": {1: "eu", 2: "ru"},
    # Korea - appear to both map to same place
    "kr": {1: "kr", 2: "tw"},
    # Taiwan - appear to both map to same place
    "tw": {1: "kr", 2: "tw"},
    # China - different url scheme (www.battlenet.com.cn)?
    "cn": {1: "cn"},
    # South East Asia
    "sea": {1: "sea"},
    # Singapore
    "sg": {1: "sg"},
    # Public Test
    "xx": {1: "xx"},
}


import json
import pkgutil

attributes_json = pkgutil.get_data("sc2reader.data", "attributes.json").decode("utf8")
attributes_dict = json.loads(attributes_json)
LOBBY_PROPERTIES = dict()
for key, value in attributes_dict.get("attributes", dict()).items():
    LOBBY_PROPERTIES[int(key)] = value
