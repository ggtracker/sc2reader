from __future__ import absolute_import

import zlib
import pprint
import hashlib
from datetime import datetime
import time
from StringIO import StringIO
from collections import defaultdict, deque

import urllib2
from mpyq import MPQArchive

from sc2reader import utils
from sc2reader import log_utils
from sc2reader import readers, data
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

    #: A nested dictionary of player => { attr_name : attr_value } for
    #: known attributes. Player 16 represents the global context and
    #: contains attributes like game speed.
    attributes = defaultdict(dict)

    #: Fully qualified filename of the replay file represented.
    filename = str()

    #: Total number of frames in this game at 16 frames per second.
    frames = int()

    #: The SCII game engine build number
    build = int()

    #: The full version release string as seen on Battle.net
    release_string = str()

    #: A tuple of the individual pieces of the release string
    versions = tuple()

    #: The game speed: Slower, Slow, Normal, Fast, Faster
    speed = str()

    #: The operating system the replay was recorded on.
    #: Useful for interpretting certain kind of raw data.
    os = str()

    #: Deprecated, use :attr:`game_type` or :attr:`real_type` instead
    type = str()

    #: The game type choosen at game creation: 1v1, 2v2, 3v3, 4v4, FFA
    game_type = str()

    #: The real type of the replay as observed by counting players on teams.
    #: For outmatched games, the smaller team numbers come first.
    #: Example Values: 1v1, 2v2, 3v3, FFA, 2v4, etc.
    real_type = str()

    #: The category of the game, Ladder and Private
    category = str()

    #: A flag for public ladder games
    is_ladder = bool()

    #: A flag for private non-ladder games
    is_private = bool()

    #: The raw hash name of the s2ma resource as hosted on bnet depots
    map_hash = str()

    #: The name of the map the game was played on
    map_name = str()

    #: A reference to the loaded :class:`Map` resource.
    map = None

    #: The UTC time the game was ended as represented by the Windows OS
    windows_timestamp = int()

    #: The UTC time the game was ended as represented by the Unix OS
    unix_timestamp = int()

    #: The time zone adjustment for the location the replay was recorded at
    time_zone= int()

    #: Deprecated: See `end_time` below.
    date = None

    #: A datetime object representing the local time at the end of the game.
    end_time = None

    #: A datetime object representing the local time at the start of the game
    start_time = None

    #: Deprecated: See `game_length` below.
    length = None

    #: The :class:`Length` of the replay as an alternative to :attr:`frames`
    game_length = None

    #: The :class:`Length` of the replay in real time adjusted for the game speed
    real_length = None

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

    #: A list of pings sent by all the different people in the game
    pings = list()

    #: A list of packets sent between the various game clients
    packets = list()

    #: A reference to the :class:`Person` that recorded the game
    recorder = None

    #: If there is a valid winning team this will contain a :class:`Team` otherwise it will be :class:`None`
    winner = None

    #: A dictionary mapping unit unique ids to their corresponding classes
    objects = dict()

    #: A sha256 hash uniquely representing the combination of people in the game.
    #: Can be used in conjunction with date times to match different replays
    #: of the game game.
    people_hash = str()


    def __init__(self, replay_file, filename=None, load_level=4, **options):
        super(Replay, self).__init__(replay_file, filename, **options)
        self.datapack = None
        self.raw_data = dict()

        #default values, filled in during file read
        self.player_names = list()
        self.other_people = set()
        self.speed = ""
        self.type = ""
        self.os = str()
        self.game_type = ""
        self.real_type = ""
        self.category = ""
        self.is_ladder = False
        self.is_private = False
        self.map = None
        self.map_hash = ""
        self.gateway = ""
        self.events = list()
        self.events_by_type = defaultdict(list)
        self.results = dict()
        self.teams, self.team = list(), dict()
        self.players, self.player = list(), utils.PersonDict()
        self.observers = list() #Unordered list of Observer
        self.people, self.humans = list(), list() #Unordered list of Players+Observers
        self.person = utils.PersonDict() #Maps pid to Player/Observer
        self.attributes = defaultdict(dict)
        self.messages = list()
        self.recorder = None # Player object
        self.packets = list()
        self.objects = {}

        # Bootstrap the readers.
        self.registered_readers = defaultdict(list)
        self.register_default_readers()

        # Bootstrap the datapacks.
        self.registered_datapacks= list()
        self.register_default_datapacks()

        # Unpack the MPQ and read header data if requested
        if load_level >= 0:
            # Set ('versions', 'frames', 'build', 'release_string', 'length')
            self.__dict__.update(utils.read_header(replay_file))
            self.archive = utils.open_archive(replay_file)

        # Load basic details if requested
        if load_level >= 1:
            for data_file in {'replay.initData','replay.details','replay.attributes.events'}:
                self._read_data(data_file, self._get_reader(data_file))
            self.load_details()
            self.datapack = self._get_datapack()

            # Can only be effective if map data has been loaded
            if options.get('load_map', False):
                self.load_map()

        # Load players if requested
        if load_level >= 2:
            for data_file in {'replay.message.events'}:
                self._read_data(data_file, self._get_reader(data_file))
            self.load_players()

        # Load events if requested
        if load_level >= 3:
            for data_file in {'replay.game.events'}:
                self._read_data(data_file, self._get_reader(data_file))
            self.load_events()

    def load_details(self):
        if 'replay.initData' in self.raw_data:
            initData = self.raw_data['replay.initData']
            if initData.map_data:
                self.gateway = initData.map_data[0].gateway
                self.map_hash = initData.map_data[-1].map_hash.encode('hex')

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
            self.type = self.game_type = self.attributes[16]['Game Type']
            self.is_ladder = (self.category == "Ladder")
            self.is_private = (self.category == "Private")

        if 'replay.details' in self.raw_data:
            details = self.raw_data['replay.details']

            self.map_name = details.map

            if details.os == 0:
                self.os = "Windows"
                self.windows_timestamp = details.file_time-details.utc_adjustment
                self.unix_timestamp = utils.windows_to_unix(self.windows_timestamp)
                self.time_zone = details.utc_adjustment/(10**7*60*60)
                self.end_time = datetime.utcfromtimestamp(self.unix_timestamp)
            elif details.os == 1:
                self.os = "Mac"
                self.windows_timestamp = details.utc_adjustment
                self.unix_timestamp = utils.windows_to_unix(self.windows_timestamp)
                self.time_zone = (details.utc_adjustment-details.file_time)/(10**7*60*60)
                self.end_time = datetime.utcfromtimestamp(self.unix_timestamp)
            else:
                raise ValueError("Unknown operating system {} detected.".format(details.os))

            self.game_length = self.length
            self.real_length = utils.Length(seconds=int(self.length.seconds/GAME_SPEED_FACTOR[self.speed]))
            self.start_time = datetime.utcfromtimestamp(self.unix_timestamp-self.real_length.seconds)
            self.date = self.end_time #backwards compatibility

    def load_map(self):
        map_url = Map.get_url(self.gateway, self.map_hash)
        map_file = StringIO(urllib2.urlopen(map_url).read())
        self.map = Map(map_file, filename=self.map, gateway=self.gateway, map_hash=self.map_hash)

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

        # Special case FFA games and sort outmatched games in ascending order
        team_sizes = [len(team.players) for team in self.teams]
        if len(team_sizes) > 2 and sum(team_sizes) == len(team_sizes):
            self.real_type = "FFA"
        else:
            self.real_type = "v".join(str(size) for size in sorted(team_sizes))

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
                observer.region = default_region
                self.observers.append(observer)
                self.people.append(observer)
                self.person[obs_index] = observer
                obs_index += 1

        # Miscellaneous people processing
        self.humans = filter(lambda p: p.is_human, self.people)

        if 'replay.message.events' in self.raw_data:
            # Figure out recorder
            self.packets = self.raw_data['replay.message.events'].packets
            packet_senders = set(map(lambda p: p.pid, self.packets))
            human_pids = map(lambda p: p.pid, self.humans)
            recorders = list(set(human_pids) - set(packet_senders))
            if len(recorders) == 1:
                self.recorder = self.person[recorders[0]]
                self.recorder.recorder = True
            else:
                self.recorder = None
                self.logger.error("{} possible recorders remain: {}".format(len(recorders), recorders))

        player_names = sorted(map(lambda p: p.name, self.people))
        hash_input = self.gateway+":"+','.join(player_names)
        self.people_hash = hashlib.sha256(hash_input).hexdigest()

    def load_events(self):
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
            # TODO: Should this be documented or removed? I don't like it.
            self.events_by_type[event.name].append(event)
            if event.pid != 16:
                self.person[event.pid].events.append(event)

    def register_reader(self, data_file, reader, filterfunc=lambda r: True):
        """
        Allows you to specify your own reader for use when reading the data
        files packed into the .SC2Replay archives. Datapacks are checked for
        use with the supplied filterfunc in reverse registration order to give
        user registered datapacks preference over factory default datapacks.

        Don't use this unless you know what you are doing.

        :param data_file: The full file name that you would like this reader to
            parse.

        :param reader: The :class:`Reader` object you wish to use to read the
            data file.

        :param filterfunc: A function that accepts a partially loaded
            :class:`Replay` object as an argument and returns true if the
            reader should be used on this replay.
        """
        self.registered_readers[data_file].insert(0,(filterfunc, reader))

    def register_datapack(self, datapack, filterfunc=lambda r: True):
        """
        Allows you to specify your own datapacks for use when loading replays.
        Datapacks are checked for use with the supplied filterfunc in reverse
        registration order to give user registered datapacks preference over
        factory default datapacks.

        This is how you would add mappings for your favorite custom map.

        :param datapack: A :class:`BaseData` object to use for mapping unit
            types and ability codes to their corresponding classes.

        :param filterfunc: A function that accepts a partially loaded
            :class:`Replay` object as an argument and returns true if the
            datapack should be used on this replay.
        """
        self.registered_datapacks.insert(0,(filterfunc, datapack))


    # Override points
    def register_default_readers(self):
        """Registers factory default readers."""
        self.register_reader('replay.details', readers.DetailsReader_Base(), lambda r: r.build < 22612)
        self.register_reader('replay.details', readers.DetailsReader_22612(), lambda r: r.build >= 22612)
        self.register_reader('replay.initData', readers.InitDataReader_Base())
        self.register_reader('replay.message.events', readers.MessageEventsReader_Base())
        self.register_reader('replay.attributes.events', readers.AttributesEventsReader_Base(), lambda r: r.build <  17326)
        self.register_reader('replay.attributes.events', readers.AttributesEventsReader_17326(), lambda r: r.build >= 17326)
        self.register_reader('replay.game.events', readers.GameEventsReader_16117(), lambda r: 16117 <= r.build < 16561)
        self.register_reader('replay.game.events', readers.GameEventsReader_16561(), lambda r: 16561 <= r.build < 18574)
        self.register_reader('replay.game.events', readers.GameEventsReader_18574(), lambda r: 18574 <= r.build < 19595)
        self.register_reader('replay.game.events', readers.GameEventsReader_19595(), lambda r: 19595 <= r.build < 22612)
        self.register_reader('replay.game.events', readers.GameEventsReader_22612(), lambda r: 22612 <= r.build)

    def register_default_datapacks(self):
        """Registers factory default datapacks."""
        self.register_datapack(data.build16117, lambda r: 16117 <= r.build < 17811)
        self.register_datapack(data.build17811, lambda r: 17811 <= r.build < 18701)
        self.register_datapack(data.build18701, lambda r: 18701 <= r.build < 21029)
        self.register_datapack(data.build21029, lambda r: 21029 <= r.build < 22612)
        self.register_datapack(data.build22612, lambda r: 22612 <= r.build)


    # Internal Methods
    def _get_reader(self, data_file):
        for callback, reader in self.registered_readers[data_file]:
            if callback(self):
                return reader
        else:
            raise ValueError("Valid {} reader could not found for build {}".format(data_file, self.build))

    def _get_datapack(self):
        for callback, datapack in self.registered_datapacks:
            if callback(self):
                return datapack
        else:
            return None

    def _read_data(self, data_file, reader):
        data = utils.extract_data_file(data_file,self.archive)
        if data:
            data_buffer = utils.ReplayBuffer(data)
            self.raw_data[data_file] = reader(data_buffer, self)
        elif self.opt.debug and data_file != 'replay.message.events':
            raise ValueError("{0} not found in archive".format(data_file))
        else:
            self.logger.error("{0} not found in archive".format(data_file))

class Map(Resource):
    url_template = 'http://{0}.depot.battle.net:1119/{1}.s2ma'

    #: The unique hash used to identify this map on bnet's depots.
    hash = str()

    #: The gateway this map was posted to.
    #: Maps must be posted individually to each gateway.
    gateway = str()

    #: A URL reference to the location of this map on bnet's depots.
    url = str()

    #: The localized (only enUS supported right now) map name
    name = str()

    #: The map's author
    author = str()

    #: The map description as written by author
    description = str()

    #: A byte string representing the minimap in tga format.
    minimap = str()

    def __init__(self, map_file, filename=None, gateway=None, map_hash=None, **options):
        super(Map, self).__init__(map_file, filename, **options)
        self.hash = map_hash
        self.gateway = gateway
        self.url = Map.get_url(gateway, map_hash)
        self.archive = MPQArchive(map_file)
        self.minimap = self.archive.read_file('Minimap.tga')

        # TODO: We probably shouldn't favor enUS here?
        game_strings = self.archive.read_file('enUS.SC2Data\LocalizedData\GameStrings.txt')
        for line in game_strings.split('\r\n'):
            parts = line.split('=')
            if parts[0] == 'DocInfo/Name':
                self.name = parts[1]
            elif parts[0] == 'DocInfo/Author':
                self.author = parts[1]
            elif parts[0] == 'DocInfo/DescLong':
                self.description = parts[1]

    @classmethod
    def get_url(cls, gateway, map_hash):
        """Builds a download URL for the map from its components."""
        if gateway and map_hash:
            return cls.url_template.format(gateway, map_hash)
        else:
            return None


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

    #: Game speed
    game_speed = str()

    #: Game length (real-time)
    real_length = int()

    #: Game length (in-game)
    game_length = int()

    #: A dictionary of Lobby properties
    lobby_properties = dict()

    #: A dictionary of Lobby player properties
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

        self.team = dict()
        self.teams = list()
        self.players = list()
        self.winners = list()
        self.player = dict()
        self.build_orders = dict()
        self.image_urls = list()
        self.localization_urls = dict()
        self.lobby_properties = dict()
        self.lobby_player_properties = dict()

        # The first 16 bytes appear to be some sort of compression header
        buffer = utils.ReplayBuffer(zlib.decompress(summary_file.read()[16:]))

        # TODO: Is there a fixed number of entries?
        # TODO: Maybe the # of parts is recorded somewhere?
        self.parts = list()
        while buffer.left:
            self.parts.append(buffer.read_data_struct())

        # Parse basic info
        self.game_speed = GAME_SPEED_CODES[''.join(reversed(self.parts[0][0][1]))]

        # time struct looks like this:
        # { 0: 11987, 1: 283385849, 2: 1334719793L}
        # 0, 1 might be an adjustment of some sort
        self.unknown_time = self.parts[0][2][2]

        # this one is alone as a unix timestamp
        self.time = self.parts[0][8]

        # in seconds
        self.game_length = utils.Length(seconds=self.parts[0][7])
        self.real_length = utils.Length(seconds=self.parts[0][7]/GAME_SPEED_FACTOR[self.game_speed])

        # TODO: Is this the start or end time?
        self.date = datetime.utcfromtimestamp(self.parts[0][8])

        self.load_lobby_properties()
        self.load_player_info()
        self.load_player_graphs()
        self.load_map_data()
        self.load_player_builds()

    def load_player_builds(self):
        # Parse build orders
        bo_structs = [x[0] for x in self.parts[5:]]
        bo_structs.append(self.parts[4][0][3:])

        # This might not be the most effective way, but it works
        for pid, p in self.player.items():
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

    def load_map_data(self):
        # Parse map localization data
        for l in self.parts[0][6][8]:
            lang = l[0]
            urls = list()
            for hash in l[1]:
                parsed_hash = utils.parse_hash(hash)
                if not parsed_hash['server']:
                    continue
                urls.append(self.base_url_template.format(parsed_hash['server'], parsed_hash['hash'], parsed_hash['type']))

            self.localization_urls[lang] = urls

        # Parse map images
        for hash in self.parts[0][6][7]:
            parsed_hash = utils.parse_hash(hash)
            self.image_urls.append(self.base_url_template.format(parsed_hash['server'], parsed_hash['hash'], parsed_hash['type']))

    def load_player_graphs(self):
        # Parse graph and stats stucts, for each player
        for pid, p in self.player.items():
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

    def load_player_info(self):
        # Parse player structs, 16 is the maximum amount of players
        for i in range(16):
            # Check if player, skip if not
            if self.parts[0][3][i][2] == '\x00\x00\x00\x00':
                continue

            player_struct = self.parts[0][3][i]

            player = PlayerSummary(player_struct[0][0])
            player.race = RACE_CODES[''.join(reversed(player_struct[2]))]

            # TODO: Grab team id from lobby_player_properties
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

            self.players.append(player)
            self.player[player.pid] = player

            if not player.teamid in self.teams:
                self.team[player.teamid] = list()
            self.team[player.teamid].append(player.pid)

        # What does this do?
        #self.teams = [self.team[tid] for tid in sorted(self.team.keys())]

    def load_lobby_properties(self):
        #Monster function used to parse lobby properties in GameSummary
        #
        # The definition of each lobby property is in data[0][5] with the structure
        #
        # id = def[0][1] # The unique property id
        # vals = def[1]  # A list with the values the property can be
        # reqs = def[3]  # A list of requirements the property has
        # dflt = def[8]  # The default value(s) of the property
        #                this is a single entry for a global property
        #                and a list() of entries for a player property

        # The def-values is structured like this
        #
        # id = `the index in the vals list`
        # name = v[0]    # The name of the value

        # The requirement structure looks like this
        #
        # id = r[0][1][1] # The property id of this requirement
        # vals = r[1]     # A list of names of valid values for this requirement

        ###
        # The values of each property is in data[0][6][6] with the structure
        #
        # id = v[0][1]  # The property id of this value
        # vals = v[1]   # The value(s) of this property
        #                this is a single entry for a global property
        #                and a list() of entries for a player property

        ###
        # A value-entry looks like this
        #
        # index = v[0]  # The index in the def.vals array representing the value
        # unknown = v[1]

        # TODO: this indirection is confusing, fix at some point..
        data = self.parts

        # First get the definitions in data[0][5]
        defs = dict()
        for d in data[0][5]:
            k = d[0][1]
            defs[k] = {
                'id':k,
                'vals':d[1],
                'reqs':d[3],
                'dflt':d[8],
                'lobby_prop':type(d[8]) == type(dict())
                }
        vals = dict()

        # Get the values in data[0][6][6]
        for v in data[0][6][6]:
            k = v[0][1]
            vals[k] = {
                'id':k,
                'vals':v[1]
                }

        lobby_ids = [k for k in defs if defs[k]['lobby_prop']]
        lobby_ids.sort()
        player_ids = [k for k in defs if not defs[k]['lobby_prop']]
        player_ids.sort()

        left_lobby = deque([k for k in defs if defs[k]['lobby_prop']])

        lobby_props = dict()
        last_success = 0
        max = len(left_lobby)
        # We cycle through all property values 'til we're done
        while len(left_lobby) > 0 and not (last_success > max+1):
            last_success += 1
            propid = left_lobby.popleft()
            can_be_parsed = True
            active = True
            # Check the requirements
            for req in defs[propid]['reqs']:
                can_be_parsed = can_be_parsed and (req[0][1][1] in lobby_props)
                # Have we parsed all req-fields?
                if not can_be_parsed:
                    break
                # Is this requirement fullfilled?
                active = active and (lobby_props[req[0][1][1]] in req[1])

            if not can_be_parsed:
                # Try parse this later
                left_lobby.append(propid)
                continue
            last_success = 0
            if not active:
                # Ok, so the reqs weren't fullfilled, don't use this property
                continue
            # Nice! We've parsed a property
            lobby_props[propid] = defs[propid]['vals'][vals[propid]['vals'][0]][0]

        player_props = [dict() for pid in range(16)]
        # Parse each player separately (this is required :( )
        for pid in range(16):
            left_players = deque([a for a in player_ids])
            player = dict()

            # Use this to avoid an infinite loop
            last_success = 0
            max = len(left_players)
            while len(left_players) > 0 and not (last_success > max+1):
                last_success += 1
                propid = left_players.popleft()
                can_be_parsed = True
                active = True
                for req in defs[propid]['reqs']:
                    #req is a lobby prop
                    if req[0][1][1] in lobby_ids:
                        active = active and (req[0][1][1] in lobby_props) and (lobby_props[req[0][1][1]] in req[1])
                    #req is a player prop
                    else:
                        can_be_parsed = can_be_parsed and (req[0][1][1] in player)
                        if not can_be_parsed:
                            break
                        active = active and (player[req[0][1][1]] in req[1])

                if not can_be_parsed:
                    left_players.append(propid)
                    continue
                last_success = 0
                if not active:
                    continue
                player[propid] = defs[propid]['vals'][vals[propid]['vals'][pid][0]][0]

            player_props[pid] = player

        self.lobby_properties = lobby_props
        self.lobby_player_properties = player_props

    def __str__(self):
        return "{} - {} {}".format(time.ctime(self.time),self.game_length,
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
