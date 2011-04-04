from constants import races
from collections import defaultdict
from sc2reader.utils import PersonDict
from sc2reader.constants import *

class Replay(object):
    
    def __init__(self, filename, release, frames=0):
        #Split and offset for matching indexes if they pass in the release string
        if isinstance(release,basestring): release = [None]+release.split('.') 
        
        #Assign all the relevant information to the replay object
        self.build = release[4]
        self.versions = (release[1], release[2], release[3], release[4])
        self.release_string = "%s.%s.%s.%s" % self.versions
        self.frames, self.seconds = (frames, frames/16)
        self.length = (self.seconds/60, self.seconds%60)
        
        self.player_names = list()
        self.other_people = set()
        self.filename = filename
        self.speed = ""
        self.type = ""
        self.category = ""
        self.is_ladder = False
        self.is_private = False
        self.map = ""
        self.realm = ""
        self.events = list()
        self.results = dict()
        self.teams = defaultdict(list)
        self.observers = list() #Unordered list of Observer
        self.players = list() #Unordered list of Player
        self.people = list() #Unordered list of Players+Observers
        self.person = PersonDict() #Maps pid to Player/Observer
        self.events_by_type = dict()
        self.attributes = list()
        self.messages = list()
        self.recorder = None # Player object
        self.winner_known = False

        # Set in parsers.DetailParser.load, should we hide this?
        self.file_time = None # Probably number milliseconds since EPOCH
        
        # TODO: Test EPOCH differences between MacOsX and Windows
        # http://en.wikipedia.org/wiki/Epoch_(reference_date)
        # Notice that Windows and Mac have different EPOCHs, I wonder whether
        # this is different depending on the OS on which the replay was played.
        self.date = None # Date when the game was played in local time
        self.utc_date = None # Date when the game was played in UTC
        
class Attribute(object):
    
    def __init__(self, data):
        #Unpack the data values and add a default name of unknown to be
        #overridden by known attributes; acts as a flag for exclusion
        self.header, self.id, self.player, self.value, self.name = tuple(data+["Unknown"])
        
        #Strip off the null bytes
        while self.value[-1] == '\x00': self.value = self.value[:-1]
   
        if self.id == 0x01F4:
            self.name, self.value = "Player Type", PLAYER_TYPES[self.value]
            
        elif self.id == 0x07D1:
            self.name,self.value = "Game Type",''.join(reversed(self.value))
            
        elif self.id == 0x0BB8:
            self.name, self.value = "Game Speed", GAME_SPEEDS[self.value]
            
        elif self.id == 0x0BB9:
            self.name, self.value = "Race", RACES[self.value]
            
        elif self.id == 0x0BBA:
            self.name, self.value = "Color", TEAM_COLORS[self.value]
            
        elif self.id == 0x0BBB:
            self.name = "Handicap"
            
        elif self.id == 0x0BBC:
            self.name, self.value = "Difficulty", DIFFICULTIES[self.value]
            
        elif self.id == 0x0BC1:
            self.name, self.value = "Category", GAME_TYPES[self.value]
            
        elif self.id == 0x07D2:
            self.name = "Teams1v1"
            #Get the raw team number
            self.value = int(self.value[0])
            
        elif self.id == 0x07D3:
            self.name = "Teams2v2"
            #Get the raw team number
            self.value = int(self.value[0])
            
        elif self.id == 0x07D4:
            self.name = "Teams3v3"
            #Get the raw team number
            self.value = int(self.value[0])
            
        elif self.id == 0x07D5:
            self.name = "Teams4v4"
            #Get the raw team number
            self.value = int(self.value[0])
            
        elif self.id == 0x07D6:
            self.name = "TeamsFFA"
            #Get the raw team number
            self.value = int(self.value[0])
            
        #print "%s (%s) - %s - %s" % (self.name, self.id, self.player, self.value)
    
    def __repr__(self):
        return str(self)
        
    def __str__(self):
        return "%s: %s" % (self.name, self.value)
    
class Message(object):
    
    def __init__(self, time, pid, target, text):
        self.time, self.sender_id, self.target, self.text = time, pid, target, text
        self.seconds = time/16
        self.sent_to_all = (self.target == 0)
        self.sent_to_allies = (self.target == 2)
        
    def __str__(self):
        time = ((self.time/16)/60, (self.time/16)%60)
        return "%s - Player %s - %s" % (time, self.sender_id, self.text)
        
    def __repr__(self):
        return str(self)

# Actor is a base class for Observer and Player
class Person(object):
    def __init__(self, pid, name):
        self.pid = pid
        self.name = name
        self.is_obs = None
        self.messages = list()
        self.events = list()
        self.recorder = False # Actual recorder will be determined using the replay.message.events file

class Observer(Person):
    def __init__(self, pid, name):
        super(Observer,self).__init__(pid,name)
        self.is_obs = True
		
class Player(Person):
    
    url_template = "http://%s.battle.net/sc2/en/profile/%s/%s/%s/"
    
    def __init__(self, pid, data, realm="us"):
        # TODO: get a map of realm,subregion => region in here
        super(Player,self).__init__(pid,data[0])
        self.is_obs = False
        self.realm = realm
        self.uid = data[1][4]
        self.subregion = data[1][2]
        self.url = self.url_template % (self.realm, self.uid, self.subregion, self.name)
        self.actual_race = data[2]
        
        # Actual race seems to be localized, so try to convert to english if possible
        
        # Some European language, like DE will have races written slightly differently (ie. Terraner).
        # To avoid these differences, only examine the first letter, which seem to be consistent across languages.
        if self.actual_race[0] == 'T':
            self.actual_race = "Terran"
        if self.actual_race[0] == 'P':
            self.actual_race = "Protoss"
        if self.actual_race[0] == 'Z':
            self.actual_race = "Zerg"
            
        if self.actual_race in races:
            self.actual_race = races[self.actual_race]
            
        self.choosen_race = "" # Populated from the replay.attribute.events file
        self.color_rgba = dict([
                ['r', data[3][1]], 
                ['g', data[3][2]], 
                ['b', data[3][3]], 
                ['a', data[3][0]], 
            ])
            
        self.result = None
        self.color_hex = "%02X%02X%02X" % (data[3][1], data[3][2], data[3][3])
        self.color_text = "" # The text of the player color (Red, Blue, etc) to be supplied later
        self.handicap = data[6]
        self.team = None # A number to be supplied later
        self.type = "" # Human or Computer
        self.avg_apm = 0
        self.aps = dict() # Doesn't contain seconds with zero actions
        self.apm = dict() # Doesn't contain minutes with zero actions
        
    def __str__(self):
        return "Player %s - %s (%s)" % (self.pid, self.name, self.actual_race)
        
    def __repr__(self):
        return str(self)

        
        
class Event(object):
    name = 'BaseEvent'
    def apply(self): pass
    
    """Abstract Event Type, should not be directly instanciated"""
    def __init__(self, timestamp, player_id, event_type, event_code):
        self.time, self.seconds = (timestamp, timestamp >> 4)
        self.timestr = "%s:%s" % (self.seconds/60, str(self.seconds%60).rjust(2, "0"))
        self.type = event_type
        self.code = event_code
        self.is_local = (player_id != 16)
        self.player = player_id
        self.bytes = bytes
        self.abilitystr = ""
        
        # Added for convenience
        self.is_init = (event_type == 0x00)
        self.is_player_action = (event_type == 0x01)
        self.is_camera_movement = (event_type == 0x03)
        self.is_unknown = (event_type == 0x02 or event_type == 0x04 or event_type == 0x05)
	
    def __str__(self):
        return "%s - %s - %s (%s,%s)" % (self.timestr, self.player, self.name, hex(self.type), hex(self.code))
        
    def __repr__(self):
        return str(self)
        
class UnknownEvent(Event):
    name = 'UnknownEvent'
    
class PlayerJoinEvent(Event):
	name = 'PlayerJoin'
	
class GameStartEvent(Event):
    name = 'GameStart'
    
class PlayerLeaveEvent(Event):
	name = 'PlayerLeave'
    
class CameraMovementEvent(Event):
    name = 'CameraMovement'
    
class ResourceTransferEvent(Event):
    name = 'ResourceTransfer'
    def __init__(self, frames, pid, type, code, target, minerals, vespene):
        super(ResourceTransferEvent, self).__init__(frames, pid, type, code)
        self.sender = pid
        self.reciever = target
        self.minerals = minerals
        self.vespene = vespene
        
class AbilityEvent(Event):
    name = 'AbilityEvent'
    def __init__(self, timestamp, player, type, code, ability):
        super(AbilityEvent, self).__init__(timestamp, player, type, code)
        self.ability = ability

    def apply(self):
        if self.ability:
            if self.ability not in ABILITIES:
                raise ValueError("Unknown ability (%s)" % (hex(self.ability)),)
            self.ability = ABILITIES[self.ability]
            able = self.get_able_selection()
            if able:
                object = able[0]
                ability = getattr(object, self.ability)
                ability(self.timestamp)

        # claim units
        for obj in self.player.get_selection().current:
            obj.player = self.player

    def get_able_selection(self):
        return [obj for obj in self.player.get_selection().current if hasattr(obj, self.ability)]
        
class TargetAbilityEvent(AbilityEvent):
    name = 'TargetAbilityEvent'
    def __init__(self, timestamp, player, type, code, ability, target):
        super(TargetAbilityEvent, self).__init__(timestamp, player, type, code, ability)
        self.target = target

    def apply(self):
        obj_id, obj_type = self.target
        if not obj_id:
            # fog of war
            pass
        else:
            obj_type = obj_type << 8 | 0x01

            type_class = GameObject.get_type(obj_type)
            # Could this be hallucinated?
            create_obj = not GameObject.has_type(obj_type & 0xfffffc | 0x2)
                
            obj = None
            if obj_id in self.player.game.objects:
                obj = self.player.game.objects[obj_id]
            elif create_obj:
                obj = type_class(obj_id, self.timestamp)
                self.player.game.objects[obj_id] = obj

            if obj:
                obj.visit(self.timestamp, self.player, type_class)
            self.target = obj
        
        super(TargetAbilityEvent, self).apply()

class LocationAbilityEvent(AbilityEvent):
    name = 'LocationAbilityEvent'
    def __init__(self, timestamp, player, type, code, ability, location):
        super(LocationAbilityEvent, self).__init__(timestamp, player, type, code, ability)
        self.location = location

class HotkeyEvent(Event):
    name = 'HotkeyEvent'
    def __init__(self, timestamp, player, type, code, hotkey, overlay=None):
        super(HotkeyEvent, self).__init__(timestamp, player, type, code)
        self.hotkey = hotkey
        self.overlay = overlay

class SetToHotkeyEvent(HotkeyEvent):
    name = 'SetToHotkeyEvent'
    def apply(self):
        hotkey = self.player.get_hotkey(self.hotkey)
        selection = self.player.get_selection()
        hotkey[self.timestamp] = selection.current

        # They are alive!
        for obj in selection[self.timestamp]:
            obj.visit(self.timestamp, self.player)

class AddToHotkeyEvent(HotkeyEvent):
    name = 'AddToHotkeyEvent'
    def apply(self):
        hotkey = self.player.get_hotkey(self.hotkey)
        hotkeyed = hotkey.current[:]

        # Remove from hotkey if overlay
        if self.overlay:
            hotkeyed = self.overlay(hotkeyed)

        hotkeyed.extend(self.player.get_selection()[self.timestamp])
        hotkeyed = list(set(hotkeyed)) # remove dups
        hotkey[self.timestamp] = hotkeyed

        # They are alive!
        for obj in hotkeyed:
            obj.visit(self.timestamp, self.player)

class GetHotkeyEvent(HotkeyEvent):
    name = 'GetHotkeyEvent'
    def apply(self):
        hotkey = self.player.get_hotkey(self.hotkey)
        hotkeyed = hotkey.current[:]

        if self.overlay:
            hotkeyed = self.overlay(hotkeyed)

        selection = self.player.get_selection()
        selection[self.timestamp] = hotkeyed

        # selection is alive!
        for obj in hotkeyed:
            obj.visit(self.timestamp, self.player)
            
class SelectionEvent(Event):
    name = 'SelectionEvent'
    
    def __init__(self, timestamp, player, type, code, bank, objects, deselect):
        super(SelectionEvent, self).__init__(timestamp, player, type, code)
        self.bank = bank
        self.objects = objects
        self.deselect = deselect

    def apply(self):
        selection = self.player.get_selection(self.bank)

        selected = selection.current[:]
        for obj in selected: # visit all old units
            obj.visit(self.timestamp, self.player)

        if self.deselect:
            selected = self.deselect(selected)

        # Add new selection
        for (obj_id, obj_type) in self.objects:
            type_class = GameObject.get_type(obj_type)
            if obj_id not in self.player.game.objects:
                obj = type_class(obj_id, self.timestamp)
                self.player.game.objects[obj_id] = obj
            else:
                obj = self.player.game.objects[obj_id]
            obj.visit(self.timestamp, self.player, type_class)
            selected.append(obj)
        
        selection[self.timestamp] = selected
