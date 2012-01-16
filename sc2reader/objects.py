from __future__ import absolute_import

from collections import namedtuple

from sc2reader.constants import *
from sc2reader.utils import PersonDict, AttributeDict

Location = namedtuple('Location',('x','y'))
Details = namedtuple('Details',['players','map','unknown1','unknown2','unknown3','file_time','unknown4','unknown5','unknown6','unknown7','unknown8','unknown9','unknown10','unknown11'])

MapData = namedtuple('MapData',['unknown','gateway','map_hash'])
PlayerData = namedtuple('PlayerData',['name','bnet','race','color','unknown1','unknown2','handicap','unknown3','result'])
ColorData = namedtuple('ColorData',['a','r','g','b'])
BnetData = namedtuple('BnetData',['unknown1','unknown2','subregion','uid'])

class Color(AttributeDict):
    @property
    def hex(self):
        return "{0.r:02X}{0.g:02X}{0.b:02X}".format(self)

    def __str__(self):
        if not hasattr(self,'name'):
            self.name = COLOR_CODES[self.hex]
        return self.name

class Team(object):
    def __init__(self,number):
        self.number = number
        self.players = list()
        self.result = "Unknown"

    def __iter__(self):
        return self.players.__iter__()



class Attribute(object):

    def __init__(self, data):
        #Unpack the data values and add a default name of unknown to be
        #overridden by known attributes; acts as a flag for exclusion
        self.header, self.id, self.player, self.value, self.name = tuple(data+["Unknown"])

        #Strip off the null bytes
        while self.value[-1] == '\x00': self.value = self.value[:-1]

        if self.id == 0x01F4:
            self.name, self.value = "Player Type", PLAYER_TYPE_CODES[self.value]

        elif self.id == 0x07D1:
            self.name,self.value = "Game Type", GAME_FORMAT_CODES[self.value]

        elif self.id == 0x0BB8:
            self.name, self.value = "Game Speed", GAME_SPEED_CODES[self.value]

        elif self.id == 0x0BB9:
            self.name, self.value = "Race", RACE_CODES[self.value]

        elif self.id == 0x0BBA:
            self.name, self.value = "Color", TEAM_COLOR_CODES[self.value]

        elif self.id == 0x0BBB:
            self.name = "Handicap"

        elif self.id == 0x0BBC:
            self.name, self.value = "Difficulty", DIFFICULTY_CODES[self.value]

        elif self.id == 0x0BC1:
            self.name, self.value = "Category", GAME_TYPE_CODES[self.value]

        elif self.id == 0x07D2:
            self.name = "Teams1v1"
            self.value = int(self.value[0])

        elif self.id == 0x07D3:
            self.name = "Teams2v2"
            self.value = int(self.value[0])

        elif self.id == 0x07D4:
            self.name = "Teams3v3"
            self.value = int(self.value[0])

        elif self.id == 0x07D5:
            self.name = "Teams4v4"
            self.value = int(self.value[0])

        elif self.id == 0x07D6:
            self.name = "TeamsFFA"
            self.value = int(self.value[0])

        # Complete guesses here, there are several ids that might be correct
        elif self.id == 0x07D7:
            self.name = "Teams5v5"
            self.value = int(self.value[0])

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "%s: %s" % (self.name, self.value)

class Person(object):
    def __init__(self, pid, name):
        self.pid = pid
        self.name = name
        self.is_observer = None
        self.messages = list()
        self.events = list()
        self.recorder = False # Actual recorder will be determined using the replay.message.events file

class Observer(Person):
    def __init__(self, pid, name):
        super(Observer,self).__init__(pid, name)
        self.is_observer = True
        self.type = 'Human'

class Player(Person):

    URL_TEMPLATE = "http://%s.battle.net/sc2/en/profile/%s/%s/%s/"

    def __init__(self, pid, name):
        super(Player,self).__init__(pid, name)
        self.is_observer = False
        # self.result = "Win","Loss","Unknown"
        # self.team = Team()
        # TODO: set default external interface variables?

    @property
    def url(self):
        return self.URL_TEMPLATE % (self.gateway, self.uid, self.subregion, self.name)

    def __str__(self):
        return "Player %s - %s (%s)" % (self.pid, self.name, self.play_race)

    def __repr__(self):
        return str(self)

    @property
    def result(self):
        return self.team.result

    def format(self, format_string):
        return format_string.format(**self.__dict__)