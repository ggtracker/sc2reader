from data import races
from collections import defaultdict
from sc2reader.utils import ByteStream, PersonDict

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
        
        #Clean the value of leading null bytes and decode it for easier and more
        #readable comparisons in the decoding logic to follow
        while(self.value[:2] == "00"):
            self.value = self.value[2:]
        self.value = self.value.decode("hex")
        
        
        if self.id == 0x01F4:
            self.name = "Player Type"
            if   self.value == "Humn": self.value = "Human"
            elif self.value == "Comp": self.value = "Computer"
            
        elif self.id == 0x07D1:
            self.name = "Game Type"
            
        elif self.id == 0x0BB8:
            self.name = "Game Speed"
            if   self.value == "Slor": self.value = "Slower"
            elif self.value == "Norm": self.value = "Normal"
            elif self.value == "Fasr": self.value = "Faster"
            
        elif self.id == 0x0BB9:
            self.name = "Race"
            if   self.value.lower() == "prot": self.value = "Protoss"
            elif self.value.lower() == "terr": self.value = "Terran"
            elif self.value.lower() == "rand": self.value = "Random"
            
        elif self.id == 0x0BBA:
            self.name = "Color"
            if   self.value == "tc01": self.value = "Red"
            elif self.value == "tc02": self.value = "Blue"
            elif self.value == "tc03": self.value = "Teal"
            elif self.value == "tc04": self.value = "Purple"
            elif self.value == "tc05": self.value = "Yellow"
            elif self.value == "tc06": self.value = "Orange"
            elif self.value == "tc07": self.value = "Green"
            elif self.value == "tc08": self.value = "Pink"
            
        elif self.id == 0x0BBB:
            self.name = "Handicap"
            
        elif self.id == 0x0BBC:
            self.name = "Difficulty"
            if   self.value == "VyEy": self.value = "Very Easy"
            elif self.value == "Medi": self.value = "Medium"
            elif self.value == "VyHd": self.value = "Very Hard"
            elif self.value == "Insa": self.value = "Insane"
            
        elif self.id == 0x0BC1:
            self.name = "Category"
            if   self.value == "Priv": self.value = "Private"
            elif self.value == "Amm": self.value = "Ladder"
            
        elif self.id == 0x07D2:
            self.name = "Teams1v1"
            #Get the raw team number
            self.value = int(self.value[1:])
            
        elif self.id == 0x07D3:
            self.name = "Teams2v2"
            #Get the raw team number
            self.value = int(self.value[1:], 16)
            
        elif self.id == 0x07D4:
            self.name = "Teams3v3"
            #Get the raw team number
            self.value = int(self.value[1:])
            
        elif self.id == 0x07D5:
            self.name = "Teams4v4"
            #Get the raw team number
            self.value = int(self.value[1:])
            
        elif self.id == 0x07D6:
            self.name = "TeamsFFA"
            #Get the raw team number
            self.value = int(self.value[1:])
            
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
        return "%s - Player %s - %s" % (time, self.player.pid, self.text)
        
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
        super(Player,self).__init__(pid,data[0].decode("hex"))
        self.is_obs = False
        self.realm = realm
        self.uid = data[1][4]
        self.subregion = data[1][2]
        self.url = self.url_template % (self.realm, self.uid, self.subregion, self.name)
        self.actual_race = data[2].decode("hex")
        
        # Actual race seems to be localized, so try to convert to english if possible
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
    def __init__(self, elapsed_time, event_type, event_code, player_id):
        self.time, self.seconds = (elapsed_time, elapsed_time/16)
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
        return "%s - %s - %s" % (self.timestr, self.name, self.abilitystr)
        
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
    
class AbilityEvent(Event):
    name = 'AbilityEvent'

class ResourceTransferEvent(Event):
    name = 'ResourceTransfer'

class HotkeyEvent(Event):
    name = 'HotkeyEvent'
    
class SelectionEvent(Event):
    name = 'SelectionEvent'
    
class CameraMovementEvent(Event):
    name = 'CameraMovement'