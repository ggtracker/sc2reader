import os
from collections import defaultdict

from mpyq import MPQArchive

import parsers
from utils import ByteStream, PlayerDict
        
class Replay(object):
    
    def __init__(self, replay, partial_parse=True, full_parse=True):
        self.filename = replay
        self.speed = ""
        self.release_string = ""
        self.build = ""
        self.type = ""
        self.category = ""
        self.is_ladder = False
        self.is_private = False
        self.map = ""
        self.realm = ""
        self.events = list()
        self.results = dict()
        self.teams = defaultdict(list)
        self.players = list() #Unordered list of Player
        self.player = PlayerDict() #Maps pid to Player
        self.events_by_type = dict()
        self.attributes = list()
        self.length = None # (minutes, seconds) tuple
        self.messages = list()
        self.seconds = None # Length of the game in seconds
        self.versions = None # (number,number,number,number) tuple
        self.recorder = None # Player object
        self.frames = None # Integer representing FPS
        self.winner_known = False

        # Set in parsers.DetailParser.load, should we hide this?
        self.file_time = None # Probably number milliseconds since EPOCH
        # Marked as private in case people want raw file access
        self._files = dict() # Files extracted from mpyq

         #Used internally to ensure parse ordering
        self.__parsed = dict(details=False, attributes=False, messages=False, events=False, initdata=False)
        
        # TODO: Change to something better
        # http://en.wikipedia.org/wiki/Epoch_(reference_date)
        # Notice that Windows and Mac have different EPOCHs, I wonder whether
        # this is different depending on the OS on which the replay was played.
        self.date = "" # Date when the game was played
        
        #Make sure the file exists and is readable, first and foremost
        if not os.access(self.filename, os.F_OK):
            raise ValueError("File at '%s' cannot be found" % self.filename)
        elif not os.access(self.filename, os.R_OK):
            raise ValueError("File at '%s' cannot be read" % self.filename)
            
        #Always parse the header first, the extract the files
        self._parse_header()

        #Manually extract the contents of SC2Replay file (bypass the listfile)
        archive = MPQArchive(replay, listfile=False)
        self._files['replay.initData'] = archive.read_file('replay.initData')
        self._files['replay.details'] = archive.read_file('replay.details')
        self._files['replay.attributes.events'] = archive.read_file('replay.attributes.events')
        self._files['replay.message.events'] = archive.read_file('replay.message.events')
        self._files['replay.game.events'] = archive.read_file('replay.game.events')
                
        #These are quickly parsed files that contain most of the game information
        #The order is important, I need some way to reinforce it in the future
        if partial_parse or full_parse:
            self._parse_initdata()
            self._parse_details()
            self._parse_attributes()
            self._parse_messages()
        
        #Parsing events takes forever, so only do this on request
        if full_parse:
            self._parse_events()
    
    def add_player(self,player):
        self.players.append(player)
        self.player[player.pid] = player
        
    def _parse_header(self):
        #Open up a ByteStream for its contents
        source = ByteStream(open(self.filename).read())
        
        #Check the file type for the MPQ header bytes
        #if source.get_big(4) != "4D50511B":
        #    raise TypeError("File '%s' is not an MPQ file" % self.filename)
        
        #Extract replay header data
        max_data_size = source.get_little_int(4) #possibly data max size
        header_offset = source.get_little_int(4) #Offset of the second header
        data_size = source.get_little_int(4)     #possibly data size
        
        #Extract replay attributes from the mpq
        data = source.parse_serialized_data()
        
        #Assign all the relevant information to the replay object
        self.build = data[1][4]
        self.versions = (data[1][1], data[1][2], data[1][3], self.build)
        self.release_string = "%s.%s.%s.%s" % self.versions
        self.frames, self.seconds = (data[3], data[3]/16)
        self.length = (self.seconds/60, self.seconds%60)
        
    def _parse_initdata(self):
        parsers.get_initdata_parser(self.build).load(self, self._files['replay.initData'])
        self.__parsed['initdata'] = True
        
    def _parse_details(self):
        if not self.__parsed['initdata']:
            raise ValueError("The replay initdata must be parsed before parsing details")
            
        #Get player and map information
        parsers.get_detail_parser(self.build).load(self, self._files['replay.details'])
        self.__parsed['details'] = True
        
    def _parse_attributes(self):
        #The details file data is required for parsing
        if not self.__parsed['details']:
            raise ValueError("The replay details must be parsed before parsing attributes")
            
        parsers.get_attribute_parser(self.build).load(self, self._files['replay.attributes.events'])
        self.__parsed['attributes'] = True
        
        #We can now create teams
        for player in self.players: #Skip the 'None' player 0
            self.teams[player.team].append(player)
        
    def _parse_messages(self):
        #The details file data is required for parsing
        if not self.__parsed['details']:
            raise ValueError("The replay details must be parsed before parsing messages")
            
        parsers.get_message_parser(self.build).load(self, self._files['replay.message.events'])
        self.__parsed['messages'] = True
        
    def _parse_events(self):
        #The details file data is required for parsing
        if not self.__parsed['details']:
            raise ValueError("The replay details must be parsed before parsing events")
            
        parsers.get_event_parser(self.build).load(self, self._files['replay.game.events'])
        self.__parsed['events'] = True
        
        #We can now sort events by type and get results
        self.events_by_type = defaultdict(list)
        for event in self.events:
            self.events_by_type[event.name].append(event)
            
        self._process_results()
        
    def _process_results(self):
        #The details,attributes, and events are required
        if not (self.__parsed['details'] and self.__parsed['attributes'] and self.__parsed['events']):
            raise ValueError("The replay details must be parsed before parsing attributes")
            
        #Remove players from the teams as they drop out of the game   
        self.results = dict([team, len(players)] for team, players in self.teams.iteritems())
        for event in self.events_by_type['leave']:
            #Some spectator actions seem to be recorded, they aren't on teams anyway
            if event.player <= len(self.players):
                team = self.player[event.player].team
                self.results[team] -= 1 
                
        #mark all teams with no players left as losing, save the rest of the teams
        remaining = set()
        for team, count in self.results.iteritems():
            if count == 0:
                self.results[team] = "Lost"
            else:
                remaining.add(team)
        
        #If, at the end, only one team remains then that team has won
        if len(remaining) == 1:
            self.results[remaining.pop()] = "Won"
        
        #Because you can also end the game by destroying all buildings, FFA can't be known
        elif self.type != 'FFA' and self.type != '1v1':
            #The other results are unknown except in the (common) case that the
            #recorder is the last one on his team to leave. In this case, the
            #result for his team can be known
            for team in set(remaining):
                #the new set above is important because you shouldn't modify 
                #elements in collections that you are currently looping over
                if team == self.recorder.team and self.results[team] == 1:
                    self.results[team] = "Lost"
                    remaining.remove(team)
                else:
                    self.results[team] = "Unknown"
            
            #If, at the end, only one team remains then that team has won
            if len(remaining) == 1:
                self.results[remaining.pop()] = "Won"
                self.winner_known = True
        
        #If the winner can't be known mark all remaining player.result as unknown
        else:
            for team in remaining:
                self.results[team] = "Unknown"
        
        #Knowing the team results, map results to the players as well
        for player in self.players:
            player.result = self.results[player.team]
                

if __name__ == '__main__':
    from pprint import PrettyPrinter
    pprint = PrettyPrinter(indent=2).pprint
    
    #replay = Replay(r'C:\Users\graylinkim\sc2reader\tests\test1-2.sc2replay')
    #replay = Replay(r'C:\Users\graylinkim\Documents\StarCraft II\Accounts\55711209\1-S2-1-2358439\Replays\VersusAI\Agria Valley.sc2replay')
    replay = Replay(r'C:\Users\graylinkim\Documents\StarCraft II\Accounts\55711209\1-S2-1-2358439\Replays\VersusAI\hotkeys_selection_change.sc2replay')
    for event in replay.events:
        print "%s: %s" % (event.name,' '.join(event.bytes[i*2:(i+1)*2] for i in range(0,len(event.bytes)/2)))
        raw_input('')
	"""
	replay = Replay(r'C:\Users\graylinkim\Documents\StarCraft II\Accounts\55711209\1-S2-1-2358439\Replays\Unsaved\Arid Wastes.SC2Replay')
	print "%s on %s - played: %s" % (replay.type,replay.map,replay.date)
	for player in replay.players[1:]:
		print "%s: %s" % (player,player.result)
	"""