from __future__ import absolute_import

from datetime import datetime
from collections import defaultdict
from sc2reader.constants import REGIONS, LOCALIZED_RACES
from sc2reader.objects import Player, Observer, Team

from sc2reader import utils

class Replay(object):

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
    map = str()

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

    #: A list of :class:`Person` objects from the game represnting
    #: only the human players from the :attr:`people` list
    humans = list()

    #: A list of all the chat message events from the game
    messages = list()

    #: A reference to the :class:`Person` that recorded the game
    recorder = None

    #: A flag indicating whether all the results are known or not
    winner_known = bool()

    def __init__(self, replay_file, **options):
        self.opt = utils.AttributeDict(options)
        self.datapack = None
        self.raw_data = dict()
        self.listeners = defaultdict(list)

        self.filename = getattr(replay_file,'name', 'Unavailable')
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
        self.winner_known = False
        self.packets = list()

        self.objects = {}


    def add_listener(self, event_class, listener):
        self.listeners[event_class].append(listener)

    def read_data(self, data_file, reader):
        data = utils.extract_data_file(data_file,self.archive)
        if data:
            data_buffer = utils.ReplayBuffer(data)
            self.raw_data[data_file] = reader(data_buffer, self)
        elif self.opt.debug:
            raise ValueError("{0} not found in archive".format(data_file))
        else:
            print "[Error] {0} not found in archive".format(data_file)

    def load_details(self):
        if 'replay.initData' in self.raw_data:
            initData = self.raw_data['replay.initData']
            if initData.map_data:
                self.gateway = initData.map_data[0].gateway

                #Expand this special case mapping
                if self.gateway == 'sg':
                    self.gateway = 'sea'

        if 'replay.details' in self.raw_data:
            details = self.raw_data['replay.details']
            self.map = details.map
            self.file_time = details.file_time
            self.unix_timestamp = utils.windows_to_unix(self.file_time)
            self.date = datetime.fromtimestamp(self.unix_timestamp)
            self.utc_date = datetime.utcfromtimestamp(self.unix_timestamp)

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

    def load_players(self):
        #If we don't at least have details and attributes_events we can go no further
        if 'replay.details' not in self.raw_data:
            return
        if 'replay.attributes.events' not in self.raw_data:
            return

        # Create and add the players based on attribute and details information
        player_index, observer_index, default_region = 0, 0, ''
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
                observer_index += 1

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
		self.winner_known = True
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
            all_players = self.raw_data['replay.initData'].player_names
            for i in range(observer_index,len(all_players)):
                observer = Observer(i+1,all_players[i])
                self.observers.append(observer)
                self.people.append(observer)
                self.person[i+1] = observer

        # Miscellaneous people processing
        self.humans = filter(lambda p: p.is_human, self.people)

        if 'message_events' in self.raw_data:
            # Figure out recorder
            self.packets = self.raw_data.message_events.packets
            packet_senders = map(lambda p: p.player, self.packets)
            recorders = list(set(self.humans) - set(packet_senders))
            if len(recorders) == 1:
                self.recorder = recorders[0]
                self.recorder.recorder = True
            else:
                raise ValueError("Get Recorder algorithm is broken!")


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

        #Mix them all up and sort them for playback
        def sortEvents(x,y):
            result = x.frame-y.frame
            if result == 0:
                result = x.pid-y.pid
            return result

        self.events = sorted(self.events, cmp=sortEvents)

        for event in self.events:
            event.load_context(self)
            self.events_by_type[event.name].append(event)


    def start(self):
        self.stopped = False

        for event_type, listeners in self.listeners.iteritems():
            for listener in listeners:
                listener.setup(self)

        for event in self.events:
            for event_type, listeners in self.listeners.iteritems():
                if isinstance(event, event_type):
                    for listener in listeners:
                        listener(event, self)
