import os
from collections import defaultdict

from mpyq import MPQArchive

import parsers
from utils import ByteStream


class Replay(object):
    
    def __init__(self, replay, partial_parse=True, full_parse=True):
        self.file = ""
        self.speed = ""
        self.release_string = ""
        self.build = ""
        self.type = ""
        self.category = ""
        self.map = ""
        self.events = list()
        self.results = dict()
        self.teams = dict()
        self.players = list()
        self.events_by_type = dict()
        self.attributes = list()
        self.length = None # (minutes, seconds) tuple
        self.messages = list()
        self.seconds = None # Length of the game in seconds
        self.versions = None # (number,number,number,number) tuple
        self.recorder = None # Player object
        self.frames = None # Integer representing FPS
        
        # TODO: Change to something better
        self.date = "" # Date when the game was played
        # TODO: hide this?
        self.files = dict() # From the mpq lib
        # TODO: investigate where this gets set
        self.file_time # Probably number of seconds or milliseconds since EPOCH (the 1970 date)
        # TODO: This is used for internal purposes, better hide it!
        self.parsed = dict()
        
        #Make sure the file exists and is readable
        if not os.access(replay, os.F_OK):
            raise ValueError("File at '%s' cannot be found" % replay)
        elif not os.access(replay, os.R_OK):
            raise ValueError("File at '%s' cannot be read" % replay)
        
        self.file = replay
        self._parse_header()
        self.files = MPQArchive(replay).extract()
        self.parsed = dict(details=False, attributes=False, messages=False, events=False)
        
        #These are quickly parsed files that contain most of the game information
        #The order is important, I need some way to reinforce it in the future
        if partial_parse or full_parse:
            self._parse_details()
            self._parse_attributes()
            self._parse_messages()
        
        if full_parse:
            self._parse_events()
    
    def _parse_header(self):
        #Open up a ByteStream for its contents
        source = ByteStream(open(self.file).read())
        
        #Check the file type for the MPQ header bytes
        if source.getBig(4) != "4D50511B":
            raise TypeError("File '%s' is not an MPQ file" % self.file)
        
        #Extract replay header data
        max_data_size = source.get_little_int(4) #possibly data max size
        header_offset = source.get_little_int(4) #Offset of the second header
        data_size = source.get_little_int(4)     #possibly data size
        
        #Extract replay attributes from the mpq
        data = source.parse_serialized_data()
        
        #Assign all the relevant information to the replay object
        self.build = data[1][4]
        self.versions = (data[1][1], data[1][2], data[1][3], self.build)
        self.releaseString = "%s.%s.%s.%s" % self.versions
        self.frames,self.seconds = (data[3], data[3]/16)
        self.length = (self.seconds/60, self.seconds%60)
        
    def _parse_details(self):
        #Get player and map information
        parsers.get_detail_parser(self.build).load(self, self.files['replay.details'])
        self.parsed['details'] = True
        
    def _parse_attributes(self):
        #The details file data is required for parsing
        if not self.parsed['details']:
            raise ValueError("The replay details must be parsed before parsing attributes")
            
        parsers.get_attribute_parser(self.build).load(self, self.files['replay.attributes.events'])
        self.parsed['attributes'] = True
        
        #We can now create teams
        self.teams = defaultdict(list)
        for player in self.players[1:]: #Skip the 'None' player 0
            self.teams[player.team].append(player)
        
    def _parse_messages(self):
        #The details file data is required for parsing
        if not self.parsed['details']:
            raise ValueError("The replay details must be parsed before parsing messages")
            
        parsers.get_message_parser(self.build).load(self, self.files['replay.message.events'])
        self.parsed['messages'] = True
        
    def _parse_events(self):
        #The details file data is required for parsing
        if not self.parsed['details']:
            raise ValueError("The replay details must be parsed before parsing events")
            
        parsers.get_event_parser(self.build).load(self, self.files['replay.game.events'])
        self.parsed['events'] = True
        
        #We can now sort events by type and get results
        self.events_by_type = defaultdict(list)
        for event in self.events:
            self.events_by_type[event.name].append(event)
            
        self._process_results()
        
    def _process_results(self):
        #The details,attributes, and events are required
        if not (self.parsed['details'] and self.parsed['attributes'] and self.parsed['events']):
            raise ValueError("The replay details must be parsed before parsing attributes")
            
        #Remove players from the teams as they drop out of the game   
        self.results = dict([team, len(players)] for team, players in self.teams.iteritems())
        for event in self.events_by_type['leave']:
            #Some spectator actions seem to be recorded, they aren't on teams anyway
            if event.player < len(self.players):
                team = self.players[event.player].team
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
        elif self.recorder:    
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
                
        for player in self.players[1:]:
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