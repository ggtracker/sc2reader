from constants import LOCALIZED_RACES
from collections import defaultdict

from sc2reader.constants import *
from sc2reader.data import GameObject, ABILITIES
from sc2reader.utils import PersonDict, Selection, read_header

class Replay(object):
    
    def __init__(self, reader, replay_file):
        #Useful references
        self.reader = reader
        self.filename = replay_file.name

        #header information
        self.versions,self.frames = read_header(replay_file)
        self.build = self.versions[4]
        self.release_string = "%s.%s.%s.%s" % tuple(self.versions[1:5])
        self.seconds = self.frames/16
        self.length = (self.seconds/60, self.seconds%60)
        
        #default values, filled in during file read
        self.player_names = list()
        self.other_people = set()
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
        self.file_time = None
        
        # TODO: Test EPOCH differences between MacOsX and Windows
        # http://en.wikipedia.org/wiki/Epoch_(reference_date)
        # Notice that Windows and Mac have different EPOCHs, I wonder whether
        # this is different depending on the OS on which the replay was played.
        self.date = None # Date when the game was played in local time
        self.utc_date = None # Date when the game was played in UTC
        
        self.objects = {}
        
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
    def __init__(self, pid, name, replay):
        self.pid = pid
        self.name = name
        self.is_observer = None
        self.messages = list()
        self.events = list()
        self.recorder = False # Actual recorder will be determined using the replay.message.events file

        self.selections = {}
        self.hotkeys = {}
        self.replay = replay
        
    def get_selection(self, number=10):
        """ Get selection buffer by number """
        if number < 10:
            return self.get_hotkey(number)
        else:
            selection = self.selections.get(number, Selection())
            self.selections[number] = selection
            return selection

    def get_hotkey(self, number):
        """ Get hotkey buffer by number (does not load it) """
        hotkey = self.hotkeys.get(number, Selection())
        self.hotkeys[number] = hotkey
        return hotkey

    def load_hotkey(self, number, timestamp):
        """ Push hotkey to current selection (10) """
        hotkey = self.hotkeys.get(number, Selection())
        self.hotkeys[number] = hotkey
        selection = self.get_selection(10) # get user bank
        selection.deselect_all(timestamp)
        selection.select(hotkey.current(), timestamp)
  
class Observer(Person):
    def __init__(self, pid, name, replay):
        super(Observer,self).__init__(pid, name, replay)
        self.is_observer = True
		
class Player(Person):
    
    URL_TEMPLATE = "http://%s.battle.net/sc2/en/profile/%s/%s/%s/"
    
    def __init__(self, pid, name, replay):
        super(Player,self).__init__(pid, name, replay)
        self.is_observer = False
        # TODO: set default external interface variables?

    @property
    def url(self):
        return self.URL_TEMPLATE % (self.realm, self.uid, self.subregion, self.name)

    def __str__(self):
        return "Player %s - %s (%s)" % (self.pid, self.name, self.actual_race)
        
    def __repr__(self):
        return str(self)
        
class Event(object):
    name = 'BaseEvent'
    def apply(self): pass
    
    """Abstract Event Type, should not be directly instanciated"""
    def __init__(self, timestamp, player_id, event_type, event_code):
        self.frame = timestamp
        self.second = timestamp >> 4
        self.type = event_type
        self.code = event_code
        self.is_local = (player_id != 16)
        self.pid = player_id

        self.is_init = (event_type == 0x00)
        self.is_player_action = (event_type == 0x01)
        self.is_camera_movement = (event_type == 0x03)
        self.is_unknown = (event_type == 0x02 or event_type == 0x04 or event_type == 0x05)
        
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
    def __init__(self, framestamp, player, type, code, ability):
        super(AbilityEvent, self).__init__(framestamp, player, type, code)
        self.ability = ability

    def apply(self):
        
        if self.ability:
            if self.ability not in ABILITIES:
                print "Unknown ability (%s) in frame %s" % (hex(self.ability),self.frame)
                #raise ValueError("Unknown ability (%s)" % (hex(self.ability)),)
            else:
                ability = ABILITIES[self.ability]
                able = self.get_able_selection(ability)
                if able:
                    object = able[0]
                    ability = getattr(object, ability)
                    ability(self.frame)

        # claim units
        for obj in self.player.get_selection().current:
            obj.player = self.player

    def get_able_selection(self, ability):
        return [obj for obj in self.player.get_selection().current if hasattr(obj, ability)]
        
class TargetAbilityEvent(AbilityEvent):
    name = 'TargetAbilityEvent'
    def __init__(self, framestamp, player, type, code, ability, target):
        super(TargetAbilityEvent, self).__init__(framestamp, player, type, code, ability)
        self.target = target

    def apply(self):
        obj_id, obj_type = self.target
        if not obj_id:
            # fog of war
            pass
        else:
            obj_type = obj_type << 8 | 0x01
            try:
                type_class = GameObject.get_type(obj_type)
                # Could this be hallucinated?
                create_obj = not GameObject.has_type(obj_type & 0xfffffc | 0x2)
                    
                obj = None
                if obj_id in self.player.replay.objects:
                    obj = self.player.replay.objects[obj_id]
                elif create_obj:
                    obj = type_class(obj_id, self.frame)
                    self.player.replay.objects[obj_id] = obj

                if obj:
                    obj.visit(self.frame, self.player, type_class)
                self.target = obj
            except KeyError:
                print "Unknown object type (%s) at frame %s" % (hex(obj_type),self.frame)
        super(TargetAbilityEvent, self).apply()

class LocationAbilityEvent(AbilityEvent):
    name = 'LocationAbilityEvent'
    def __init__(self, framestamp, player, type, code, ability, location):
        super(LocationAbilityEvent, self).__init__(framestamp, player, type, code, ability)
        self.location = location

class UnknownAbilityEvent(AbilityEvent):
    name = 'UnknownAbilityEvent'
    pass

class UnknownLocationAbilityEvent(AbilityEvent):
    name = 'UnknownLocationAbilityEvent'
    pass
    
class HotkeyEvent(Event):
    name = 'HotkeyEvent'
    def __init__(self, framestamp, player, type, code, hotkey, overlay=None):
        super(HotkeyEvent, self).__init__(framestamp, player, type, code)
        self.hotkey = hotkey
        self.overlay = overlay

class SetToHotkeyEvent(HotkeyEvent):
    name = 'SetToHotkeyEvent'
    def apply(self):
        hotkey = self.player.get_hotkey(self.hotkey)
        selection = self.player.get_selection()
        hotkey[self.frame] = selection.current

        # They are alive!
        for obj in selection[self.frame]:
            obj.visit(self.frame, self.player)

class AddToHotkeyEvent(HotkeyEvent):
    name = 'AddToHotkeyEvent'
    def apply(self):
        hotkey = self.player.get_hotkey(self.hotkey)
        hotkeyed = hotkey.current[:]

        # Remove from hotkey if overlay
        if self.overlay:
            hotkeyed = self.overlay(hotkeyed)

        hotkeyed.extend(self.player.get_selection()[self.frame])
        hotkeyed = list(set(hotkeyed)) # remove dups
        hotkey[self.frame] = hotkeyed

        # They are alive!
        for obj in hotkeyed:
            obj.visit(self.frame, self.player)

class GetHotkeyEvent(HotkeyEvent):
    name = 'GetHotkeyEvent'
    def apply(self):
        hotkey = self.player.get_hotkey(self.hotkey)
        hotkeyed = hotkey.current[:]

        if self.overlay:
            hotkeyed = self.overlay(hotkeyed)

        selection = self.player.get_selection()
        selection[self.frame] = hotkeyed

        # selection is alive!
        for obj in hotkeyed:
            obj.visit(self.frame, self.player)
            
class SelectionEvent(Event):
    name = 'SelectionEvent'
    
    def __init__(self, framestamp, player, type, code, bank, objects, deselect):
        super(SelectionEvent, self).__init__(framestamp, player, type, code)
        self.bank = bank
        self.objects = objects
        self.deselect = deselect

    def apply(self):
        selection = self.player.get_selection(self.bank)

        selected = selection.current[:]
        for obj in selected: # visit all old units
            obj.visit(self.frame, self.player)

        if self.deselect:
            selected = self.deselect(selected)

        # Add new selection
        for (obj_id, obj_type) in self.objects:
            try:
                type_class = GameObject.get_type(obj_type)
                if obj_id not in self.player.replay.objects:
                    obj = type_class(obj_id, self.frame)
                    self.player.replay.objects[obj_id] = obj
                else:
                    obj = self.player.replay.objects[obj_id]
                obj.visit(self.frame, self.player, type_class)
                selected.append(obj)
            except KeyError:
                print "Unknown object type (%s) at frame %s" % (hex(obj_type),self.frame)
        
        selection[self.frame] = selected
