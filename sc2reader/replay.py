import os
from collections import defaultdict

from mpyq import MPQArchive

import parsers
from objects import ByteStream


class Replay(object):
    
    def __init__(self,replay):
        #Make sure the file exists and is readable
        if not os.access(replay,os.F_OK):
            raise ValueError("File at '%s' cannot be found" % replay)
        elif not os.access(replay,os.R_OK):
            raise ValueError("File at '%s' cannot be read" % replay)
            
        #Open up a ByteStream for its contents
        source = ByteStream(open(replay).read())
        
        #Check the file type for the MPQ header bytes
        if source.getBig(4) != "4D50511B":
            raise TypeError("File '%s' is not an MPQ file" % replay)
        
        #Extract replay header data
        self.parseMPQHeader(source)
        
        #Parse the rest of the archive
        self.parseMPQArchive(MPQArchive(replay))
        
        #Use the parsed information to reorganize the data
        self.setDerivedValues()
    
    def parseMPQHeader(self,source):
        #Read the MPQ file header
        max_data_size = source.getLittleInt(4) #possibly data max size
        header_offset = source.getLittleInt(4) #Offset of the second header
        data_size = source.getLittleInt(4)     #possibly data size

        #Extract replay attributes from the mpq
        data = source.parseSerializedData()
        self.build = data[1][4]
        self.versions = (data[1][1],data[1][2],data[1][3],self.build)
        self.releaseString = "%s.%s.%s.%s" % self.versions
        self.frames,self.seconds = (data[3],data[3]/16)
        self.length = (self.seconds/60,self.seconds%60)
        
    def parseMPQArchive(self,archive):
        #Extract the archive files
        files = archive.extract()
        eventsFile = files['replay.game.events']
        detailsFile = files['replay.details']
        messageFile = files['replay.message.events']
        attributesFile = files['replay.attributes.events']
        
        #Load the details file first to get player information
        parsers.getDetailParser(self.build).load(self,detailsFile)
        
        #Next load the attributes file to fill out players and get team information
        parsers.getAttributeParser(self.build).load(self,attributesFile)
        
        #Finally load the events file to get gameplay data and APM
        parsers.getEventParser(self.build).load(self,eventsFile)
        
        #We'll also load up the messages for a peak at what was going on
        parsers.getMessageParser(self.build).load(self,messageFile)
        
    def setDerivedValues(self):
        self.teams = defaultdict(list)
        for player in self.players[1:]: #Skip the 'None' player 0
            self.teams[player.team].append(player)

        self.eventsByType = defaultdict(list)
        for event in self.events:
            self.eventsByType[event.name].append(event)
        
        self.processResults()
        
    def processResults(self):
        #Remove players from the teams as they drop out of the game   
        self.results = dict([team,len(players)] for team,players in self.teams.iteritems())
        for event in self.eventsByType['leave']:
            team = self.players[event.player].team
            self.results[team] -= 1 
                
        #mark all teams with no players left as losing, save the rest of the teams
        remaining = set()
        for team,count in self.results.iteritems():
            if count == 0:
                self.results[team] = "Lost"
            else:
                remaining.add(team)
        
        #If, at the end, only one team remains then that team has won
        if len(remaining) == 1:
            self.results[remaining.pop()] = "Won"
        else:    
            #The other results are unknown except in the (common) case that the
            #recorder is the last one on his team to leave. In this case, the
            #result for his team can be known
            for team in set(remaining):
                #the new set above is important because you shouldn't modify 
                #elements in collections that you are currently looping over
                if team == self.recorder.team and self.results[team]==1:
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

	replay = Replay(r'C:\Users\graylinkim\Documents\StarCraft II\Accounts\55711209\1-S2-1-2358439\Replays\Unsaved\Arid Wastes.SC2Replay')
	print "%s on %s - played: %s" % (replay.type,replay.map,replay.date)
	for player in replay.players[1:]:
		print "%s: %s" % (player,player.result)