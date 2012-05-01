from __future__ import absolute_import

import zlib
import pprint
import hashlib
from datetime import datetime
import time
from StringIO import StringIO
from collections import defaultdict

from mpyq import MPQArchive

from sc2reader import utils
from sc2reader import log_utils
from sc2reader.objects import Player, Observer, Team, PlayerSummary, Graph
from sc2reader.constants import REGIONS, LOCALIZED_RACES, GAME_SPEED_FACTOR, GAME_SPEED_CODES, RACE_CODES, PLAYER_TYPE_CODES, TEAM_COLOR_CODES, GAME_FORMAT_CODES, GAME_TYPE_CODES, DIFFICULTY_CODES


class Resource(object):
    def __init__(self, file_object, filename=None, **options):
        self.opt = utils.AttributeDict(options)
        self.logger = log_utils.get_logger(self.__class__)
        self.filename = filename or getattr(file_object,'name','Unavailable')

        file_object.seek(0)
        self.filehash = hashlib.sha256(file_object.read()).hexdigest()
        file_object.seek(0)

class Replay(Resource):

    #: Fully qualified filename of the replay file represented.
    filename = str()

    #: Total number of frames in this game at 16 frames per second.
    frames = int()

    #: The SCII game engine build number
    build = int()

    #: The full version release string as seen on Battle.net
    release_string = str()

    #: The :class:`Length` of the replay as an alternative to :attr:`frames`
    length = utils.Length()

    #: The effective game speed when the game was played.
    speed = str()

    #: The game type: 1v1, 2v2, 3v3, 4v4, FFA
    type = str()

    #: The category of the game, Ladder and Private
    category = str()

    #: A flag for public ladder games
    is_ladder = bool()

    #: A flag for private non-ladder games
    is_private = bool()

    #: The name of the map the game was played on
    map = None

    #: The gateway the game was played on: us, eu, sea, etc
    gateway = str()

    #: An integrated list of all the game events
    events = list()

    #: A dict mapping team numbers to their game result
    results = dict()

    #: A list of :class:`Team` objects from the game
    teams = list()

    #: A dict mapping team number to :class:`Team` object
    team = dict()

    #: A list of :class:`Player` objects from the game
    players = list()

    #: A dual key dict mapping player names and numbers to
    #: :class:`Player` objects
    player = utils.PersonDict()

    #: A list of :class:`Observer` objects from the game
    observers = list()

    #: A list of :class:`Person` objects from the game representing
    #: both the player and observer lists
    people = list()

    #: A dual key dict mapping :class:`Person` object to their
    #: person id's and names
    person = utils.PersonDict()

    #: A list of :class:`Person` objects from the game representing
    #: only the human players from the :attr:`people` list
    humans = list()

    #: A list of all the chat message events from the game
    messages = list()

    #: A reference to the :class:`Person` that recorded the game
    recorder = None

    #: If there is a valid winning team this will contain a :class:`Team` otherwise it will be :class:`None`
    winner = None

    def __init__(self, replay_file, filename=None, **options):
        super(Replay, self).__init__(replay_file, filename, **options)
        self.datapack = None
        self.raw_data = dict()
        self.listeners = defaultdict(list)

        self.__dict__.update(utils.read_header(replay_file))
        self.archive = utils.open_archive(replay_file)

        #default values, filled in during file read
        self.player_names = list()
        self.other_people = set()
        self.speed = ""
        self.type = ""
        self.category = ""
        self.is_ladder = False
        self.is_private = False
        self.map = ""
        self.gateway = ""
        self.events = list()
        self.events_by_type = defaultdict(list)
        self.results = dict()

        self.teams, self.team = list(), dict()
        self.players, self.player = list(), utils.PersonDict()
        self.observers = list() #Unordered list of Observer

        self.people, self.humans = list(), list() #Unordered list of Players+Observers

        self.person = utils.PersonDict() #Maps pid to Player/Observer
        self.attributes = list()
        self.messages = list()
        self.recorder = None # Player object
        self.packets = list()

        self.objects = {}


    def add_listener(self, event_class, listener):
        self.listeners[event_class].append(listener)

    def read_data(self, data_file, reader):
        data = utils.extract_data_file(data_file,self.archive)
        if data:
            data_buffer = utils.ReplayBuffer(data)
            self.raw_data[data_file] = reader(data_buffer, self)
        elif self.opt.debug and data_file != 'replay.message.events':
            raise ValueError("{0} not found in archive".format(data_file))
        else:
            self.logger.error("{0} not found in archive".format(data_file))

    def load_details(self):
        if 'replay.initData' in self.raw_data:
            initData = self.raw_data['replay.initData']
            if initData.map_data:
                self.gateway = initData.map_data[0].gateway
                self.map_hash = initData.map_data[-1].map_hash

                #Expand this special case mapping
                if self.gateway == 'sg':
                    self.gateway = 'sea'

        if 'replay.attributes.events' in self.raw_data:
            # Organize the attribute data to be useful
            self.attributes = defaultdict(dict)
            attributesEvents = self.raw_data['replay.attributes.events']
            for attr in attributesEvents:
                self.attributes[attr.player][attr.name] = attr.value

            # Populate replay with attributes
            self.speed = self.attributes[16]['Game Speed']
            self.category = self.attributes[16]['Category']
            self.type = self.attributes[16]['Game Type']
            self.is_ladder = (self.category == "Ladder")
            self.is_private = (self.category == "Private")

        if 'replay.details' in self.raw_data:
            details = self.raw_data['replay.details']

            self.map_name = details.map

            self.windows_timestamp = details.file_time-details.utc_adjustment
            self.unix_timestamp = utils.windows_to_unix(self.windows_timestamp)
            self.time_zone = details.utc_adjustment/(10**7*60*60)

            self.end_time = datetime.utcfromtimestamp(self.unix_timestamp)
            self.game_length = self.length
            self.real_length = utils.Length(seconds=int(self.length.seconds/GAME_SPEED_FACTOR[self.speed]))
            self.start_time = datetime.utcfromtimestamp(self.unix_timestamp-self.real_length.seconds)
            self.date = self.end_time #backwards compatibility

    def load_players(self):
        #If we don't at least have details and attributes_events we can go no further
        if 'replay.details' not in self.raw_data:
            return
        if 'replay.attributes.events' not in self.raw_data:
            return

        # Create and add the players based on attribute and details information
        player_index, obs_index, default_region = 0, 1, ''
        player_data = self.raw_data['replay.details'].players
        for pid, attributes in sorted(self.attributes.iteritems()):

            # We've already processed the global attributes
            if pid == 16: continue

            # Open Slots are skipped because it doesn't seem useful to store
            # an "Open" player to fill a spot that would otherwise be empty.
            if attributes['Player Type'] == 'Open': continue

            # Get the player data from the details file, increment the index to
            # Keep track of which player we are processing
            pdata = player_data[player_index]
            player_index += 1

            # If this is a human player, push back the initial observer index in
            # the list of all human players we gathered from the initdata file.
            if attributes['Player Type'] == 'Human':
                obs_index += 1

            # Create the player using the current pid and the player name from
            # The details file. This works because players are stored in order
            # of pid inside of the details file. Attributes and Details must be
            # processed together because Details doesn't index players by or
            # store their player ids; Attributes can provide that information
            # and allow for accurate pid mapping even with computers, observers,
            # and open open slots.
            #
            # General information re: each player comes from the following files
            #   * replay.initData
            #   * replay.details
            #   * replay.attribute.events
            #
            # TODO: recognize current locale and use that instead of western
            # TODO: fill in the LOCALIZED_RACES table
            player = Player(pid,pdata.name)

            # Cross reference the player and team lookups
            team_number = attributes['Teams'+self.type]
            if not team_number in self.team:
                self.team[team_number] = Team(team_number)
                self.teams.append(self.team[team_number])
            self.team[team_number].players.append(player)
            player.team = self.team[team_number]

            # Do basic win/loss processing from details data
            if   pdata.result == 1:
                player.team.result = "Win"
                self.winner = player.team
            elif pdata.result == 2:
                player.team.result = "Loss"

            player.pick_race = attributes['Race']
            player.play_race = LOCALIZED_RACES.get(pdata.race, pdata.race)
            player.difficulty = attributes['Difficulty']
            player.is_human = (attributes['Player Type'] == 'Human')
            player.uid = pdata.bnet.uid
            player.subregion = pdata.bnet.subregion
            player.handicap = pdata.handicap

            # We need initData for the gateway portion of the url!
            if 'replay.initData' in self.raw_data and self.gateway:
                player.gateway = self.gateway
                if player.is_human and player.subregion:
                    player.region = REGIONS[self.gateway][player.subregion]
                    default_region = player.region

            # Conversion instructions to the new color object:
            #   color_rgba is the color object itself
            #   color_hex is color.hex
            #   color is str(color)
            player.color = utils.Color(**pdata.color._asdict())

            # Each player can be referenced in a number of different ways,
            # primarily for convenience of access in any given situation.
            self.people.append(player)
            self.players.append(player)
            self.player[pid] = player
            self.person[pid] = player

        #Create an store an ordered lineup string
        for team in self.teams:
            team.lineup = sorted(player.play_race[0].upper() for player in team)

        if 'replay.initData' in self.raw_data:
            # Assign the default region to computer players for consistency
            # We know there will be a default region because there must be
            # at least 1 human player or we wouldn't have a self.
            for player in self.players:
                if not player.is_human:
                    player.region = default_region

            # Create observers out of the leftover names gathered from initData
            all_players = [p.name for p in self.players]
            all_people = self.raw_data['replay.initData'].player_names
            for obs_name in all_people:
                if obs_name in all_players: continue

                observer = Observer(obs_index,obs_name)
                observer.gateway = self.gateway
                self.observers.append(observer)
                self.people.append(observer)
                self.person[obs_index] = observer
                obs_index += 1

        # Miscellaneous people processing
        self.humans = filter(lambda p: p.is_human, self.people)

        if 'replay.message.events' in self.raw_data:
            # Figure out recorder
            self.packets = self.raw_data['replay.message.events'].packets
            packet_senders = map(lambda p: p.pid, self.packets)
            human_pids = map(lambda p: p.pid, self.humans)
            recorders = list(set(human_pids) - set(packet_senders))
            if len(recorders) == 1:
                self.recorder = self.person[recorders[0]]
                self.recorder.recorder = True
            else:
                raise ValueError("Get Recorder algorithm is broken!")

        player_names = sorted(map(lambda p: p.name, self.people))
        hash_input = self.gateway+":"+','.join(player_names)
        self.people_hash = hashlib.sha256(hash_input).hexdigest()

    def load_events(self, datapack=None):
        self.datapack = datapack

        # Copy the events over
        # TODO: the events need to be fixed both on the reader and processor side
        if 'replay.game.events' in self.raw_data:
            self.events += self.raw_data['replay.game.events']

        if 'replay.message.events' in self.raw_data:
            self.messages = self.raw_data['replay.message.events'].messages
            self.pings = self.raw_data['replay.message.events'].packets
            self.packets = self.raw_data['replay.message.events'].pings
            self.events += self.messages+self.pings+self.packets

        self.events = sorted(self.events, key=lambda e: e.frame)

        for event in self.events:
            event.load_context(self)
            self.events_by_type[event.name].append(event)
            if event.pid != 16:
                self.person[event.pid].events.append(event)


    def start(self):
        self.stopped = False

        for listener in self.listeners:
            listener.setup(self)

        for event in self.events:
            for listener in self.listeners:
                if listener.accepts(event):
                    listener(event, self)


class Map(Resource):
    url_template = 'http://{0}.depot.battle.net:1119/{1}.s2ma'

    def __init__(self, map_file, filename=None, gateway=None, map_hash=None, **options):
        super(Map, self).__init__(map_file, filename, **options)
        self.hash = map_hash
        self.gateway = gateway
        self.url = Map.get_url(gateway, map_hash)
        self.archive = MPQArchive(StringIO(self.file))
        self.minimap = self.archive.read_file('Minimap.tga')

    @classmethod
    def get_url(gateway, map_hash):
        if gateway and map_hash:
            return Map.url_template.format(gateway, map_hash)
        else:
            return None

    def load(self):
        self.read_game_strings()

    def read_game_strings(self):
        self.game_strings = self.archive.read_file('enUS.SC2Data\LocalizedData\GameStrings.txt')
        for line in self.game_strings.split('\r\n'):
            parts = line.split('=')
            if parts[0] == 'DocInfo/Name':
                self.name = parts[1]
            elif parts[0] == 'DocInfo/Author':
                self.author = parts[1]
            elif parts[0] == 'DocInfo/DescLong':
                self.description = parts[1]


class GameSummary(Resource):
    base_url_template = 'http://{0}.depot.battle.net:1119/{1}.{2}'
    url_template = 'http://{0}.depot.battle.net:1119/{1}.s2gs'

    stats_keys = [
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
    lobby_keys = {
        3000 : ('game_speed', GAME_SPEED_CODES),
        2001 : ('game_type', GAME_FORMAT_CODES), #1v1/2v2/3v3/4v4/5v5/6v6/FFA
        3010 : ('unknown1', {'sey':'yes', 'on':'no'} ), #yes/no
        3006 : ('unknown2', {'3':'3','5':'5','7':'7','01':'10','51':'15','02':'20','52':'25','03':'30'}), #3',5/7/10/15/20/25/30
        1001 : ('unknown3', {'sey':'yes', 'on':'no'}), #yes/no
        1000 : ('unknown4', {'tlfD':'Default'}), #Dflt
        2000 : ('unknown5', {'2t':'t2', '3t':'t3', 'AFF':'FFA', 'tsuC':'Custom'}), #t2/t3/FFA/Cust
        3007 : ('unknown6', {'traP':'Part'}),
        3009 : ('lobby_type', GAME_TYPE_CODES) #Priv/Pub/Amm (Auto MatchMaking)
        }
    lobby_player_keys = {
        500 : ('slot_state', PLAYER_TYPE_CODES), #Clsd/Open/Humn/Comp
        3001 : ('race', RACE_CODES),
        3003 : ('energy', {'05':'50','06':'60','07':'70','08':'80','09':'90','001':'100'}),
        3002 : ('color', TEAM_COLOR_CODES),
        3004 : ('difficulty', DIFFICULTY_CODES),
        3008 : ('nonplayer_mode', {'sbO':'Observer','feR':'Ref'}), #Obs/Ref        
        
        #Team properties
        2012 : ('team_t3', {'1T':'T1', '2T':'T2', '3T':'T3'}),
        
        
        }
    
    #: Game speed
    game_speed = str()

    #: Game length (real-time)
    game_length = int()

    #: Game length (in-game)
    game_length_ingame = int()

    #: Lobby properties
    lobby_properties = dict()
    
    #: Lobby player properties
    lobby_player_properties = dict()

    #: Game completion time
    time = int()

    #: Players, a dict of :class`PlayerSummary` from the game
    players = dict()

    #: Teams, a dict of pids
    teams = dict()

    #: Winners, a list of the pids of the winning players
    winners = list()

    #: Build orders, a dict of build orders indexed by player id
    build_orders = dict()

    #: Map image urls
    image_urls = list()

    #: Map localization urls
    localization_urls = dict()
    
    def __init__(self, summary_file, filename=None, **options):
        super(GameSummary, self).__init__(summary_file, filename,**options)

        self.players = dict()
        self.build_orders = dict()
        self.image_urls = list()
        self.localization_urls = dict()
        self.lobby_properties = dict()
        self.lobby_player_properties = dict()
        self.teams = dict()
        self.winners = list()

        self.data = zlib.decompress(summary_file.read()[16:])
        self.parts = list()
        buffer = utils.ReplayBuffer(self.data)
        while buffer.left:
            part = buffer.read_data_struct()
            self.parts.append(part)

        # Parse basic info
        self.game_speed = GAME_SPEED_CODES[''.join(reversed(self.parts[0][0][1]))]

        # time struct looks like this:
        # { 0: 11987, 1: 283385849, 2: 1334719793L}
        # 0, 1 might be an adjustment of some sort
        self.unknown_time = self.parts[0][2][2]
        
        # this one is alone
        self.time = self.parts[0][8]

        self.game_length_ingame = self.parts[0][7]
        self.game_length = self.game_length_ingame / GAME_SPEED_FACTOR[self.game_speed]

        # parse lobby properties
        (self.lobby_properties, self.lobby_player_properties) = utils.get_lobby_properties(self.parts)

        # Parse player structs, 16 is the maximum amount of players
        for i in range(16):
            player = None
            # Check if player, skip if not
            if self.parts[0][3][i][2] == '\x00\x00\x00\x00':
                continue
            player_struct = self.parts[0][3][i]

            player = PlayerSummary(player_struct[0][0])
            player.race = RACE_CODES[''.join(reversed(player_struct[2]))]
            # I haven't found how to get the teams yet
            player.teamid = 0
            player.is_winner = (player_struct[1][0] == 0)
            if player.is_winner:
                self.winners.append(player.pid)

            # Is the player an ai?
            if type(player_struct[0][1]) == type(int()):
                player.is_ai = True
            else:
                player.is_ai = False
                
                player.bnetid = player_struct[0][1][0][3]
                player.subregion = player_struct[0][1][0][2]

                # int
                player.unknown1 = player_struct[0][1][0]
                # {0:long1, 1:long2}
                # Example:
                # { 0: 3405691582L, 1: 11402158793782460416L}
                player.unknown2 = player_struct[0][1][1]
            
            self.players[player.pid] = player
            if not player.teamid in self.teams:
                self.teams[player.teamid] = list()
            self.teams[player.teamid].append(player.pid)
            
        # Parse graph and stats stucts, for each player
        for pid in self.players:
            p = self.players[pid]
            # Graph stuff
            xy = [(o[2], o[0]) for o in self.parts[4][0][2][1][p.pid]]
            p.army_graph = Graph([], [], xy_list=xy)

            xy = [(o[2], o[0]) for o in self.parts[4][0][1][1][p.pid]]
            p.income_graph = Graph([], [], xy_list=xy)
            
            # Stats stuff
            stats_struct = self.parts[3][0]
            # The first group of stats is located in parts[3][0]
            for i in range(len(stats_struct)):
                p.stats[self.stats_keys[i]] = stats_struct[i][1][p.pid][0][0]
            # The last piece of stats is in parts[4][0][0][1]
            p.stats[self.stats_keys[len(stats_struct)]] = self.parts[4][0][0][1][p.pid][0][0]
        
        # Parse map localization data
        for l in self.parts[0][6][8]:
            lang = l[0]
            urls = list()
            for hash in l[1]:
                parsed_hash = utils.parse_hash(hash)
                if parsed_hash['server'] == '\x00\x00':
                    continue
                urls.append(self.base_url_template.format(parsed_hash['server'], parsed_hash['hash'], parsed_hash['type']))
                    
            self.localization_urls[lang] = urls

        # Parse map images
        for hash in self.parts[0][6][7]:
            parsed_hash = utils.parse_hash(hash)
            self.image_urls.append(self.base_url_template.format(parsed_hash['server'], parsed_hash['hash'], parsed_hash['type']))


        # Parse build orders
        
        bo_structs = [x[0] for x in self.parts[5:]]
        bo_structs.append(self.parts[4][0][3:])

        # This might not be the most effective way, but it works
        for pid in self.players:
            p = self.players[pid]
            bo = list()
            for bo_struct in bo_structs:
                for order in bo_struct:
                    
                    if order[0][1] >> 24 == 0x01:
                        # unit
                        parsed_order = utils.get_unit(order[0][1])
                    elif order[0][1] >> 24 == 0x02:
                        # research
                        parsed_order = utils.get_research(order[0][1])
                    
                    for entry in order[1][p.pid]:
                        bo.append({
                                'supply' : entry[0],
                                'total_supply' : entry[1]&0xff,
                                'time' : (entry[2] >> 8) / 16,
                                'order' : parsed_order,
                                'build_index' : entry[1] >> 16,
                                })
            bo.sort(key=lambda x: x['build_index'])
            self.build_orders[p.pid] = bo
                        

    def __str__(self):
        return "{} - {:0>2}:{:0>2}:{:0>2} {}".format(time.ctime(self.time),
                                         int(self.game_length)/3600,
                                         (int(self.game_length)%3600)/60,
                                         (int(self.game_length)%3600)%60,
                                         'v'.join(''.join(self.players[p].race[0] for p in self.teams[tid]) for tid in self.teams))

    

class MapInfo(Resource):
    url_template = 'http://{0}.depot.battle.net:1119/{1}.s2mi'

    #: Name of the Map
    map_name = str()

    #: Language
    language = str()

    #: Hash of referenced s2mh file
    s2mh_hash = str()

    #: URL of referenced s2mh file
    s2mh_url = str()

    def __init__(self, info_file, filename=None, **options):
        super(MapInfo, self).__init__(info_file, filename, **options)
        self.data = utils.ReplayBuffer(info_file).read_data_struct()
        self.map_name = self.data[0][7]
        self.language = self.data[0][13]
        parsed_hash = utils.parse_hash(self.data[0][1])
        self.s2mh_hash =  parsed_hash['hash']
        self.s2mh_url = MapHeader.url_template.format(parsed_hash['server'], self.s2mh_hash)

    def __str__(self):
        return self.map_name

class MapHeader(Resource):
    base_url_template = 'http://{0}.depot.battle.net:1119/{1}.{2}'
    url_template = 'http://{0}.depot.battle.net:1119/{1}.s2mh'
    image_url_template = 'http://{0}.depot.battle.net:1119/{1}.s2mv'

    #: The name of the map
    name = str()

    #: Hash of map file
    map_hash = str()

    #: Link to the map file
    map_url = str()
    
    #: Hash of the map image
    image_hash = str()

    #: Link to the image of the map (.s2mv)
    image_url = str()

    #: Localization dictionary, {language, url}
    localization_urls = dict()

    #: Blizzard map
    blizzard = False

    def __init__(self, header_file, filename=None, **options):
        super(MapHeader, self).__init__(header_file, filename, **options)
        self.data = utils.ReplayBuffer(header_file).read_data_struct()

        # Name
        self.name = self.data[0][1]

        # Blizzard
        self.blizzard = (self.data[0][11] == 'BLIZ')
        
        # Parse image hash
        parsed_hash = utils.parse_hash(self.data[0][1])
        self.image_hash = parsed_hash['hash']
        self.image_url = self.image_url_template.format(parsed_hash['server'], parsed_hash['hash'])
        
        # Parse map hash
        parsed_hash = utils.parse_hash(self.data[0][2])
        self.map_hash = parsed_hash['hash']
        self.map_url = self.base_url_template.format(parsed_hash['server'], parsed_hash['hash'], parsed_hash['type'])
        
        # Parse localization hashes
        l18n_struct = self.data[0][4][8]
        for l in l18n_struct:
            parsed_hash = utils.parse_hash(l[1][0])
            self.localization_urls[l[0]] = self.base_url_template.format(parsed_hash['server'], parsed_hash['hash'], parsed_hash['type'])
