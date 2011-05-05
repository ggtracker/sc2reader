from collections import defaultdict
from sc2reader.objects import *
from sc2reader.utils import key_in_bases

#####################################################
# Metaclass used to help enforce the usage contract
#####################################################
class MetaProcessor(type):
    def __new__(meta, class_name, bases, class_dict):
        if class_name != "Processor": #Parent class is exempt from checks
            assert 'required_readers' in class_dict or key_in_bases('required_readers',bases), \
                "%s must define attribute 'required_readers' as an iterable" % class_name

            assert 'required_processors' in class_dict or key_in_bases('required_processors',bases), \
                "%s must define attribute 'required_processors' as an iterable" % class_name

            assert 'process' in class_dict or key_in_bases('process',bases), \
                "%s must define method 'Replay process(self, replay)'" % class_name

        return type.__new__(meta, class_name, bases, class_dict)

class Processor(object):
    required_readers = []
    required_processors = []
    __metaclass__ = MetaProcessor
    
#####################################################

class PeopleProcessor(Processor):
    def process(self, replay):
        obs_players = list(replay.player_names)
        for player in replay.players:
            obs_players.remove(player.name)
        
        for pid,name in enumerate(obs_players):
            replay.observers.append(Observer(pid+len(replay.players)+1,name,replay))
        
        for person in replay.observers+replay.players:
            replay.people.append(person)
            replay.person[person.pid] = person
            
        return replay

#####################################################

class AttributeProcessor(Processor):
    def process(self, replay):
        data = defaultdict(dict)
        for attr in replay.attributes:
            data[attr.player][attr.name] = attr.value
            
        #Get global settings first
        replay.speed = data[16]['Game Speed']
        
        #TODO: Do we need the category variable at this point?
        replay.category = data[16]['Category']
        replay.is_ladder = (replay.category == "Ladder")
        replay.is_private = (replay.category == "Private")
        
        replay.type = data[16]['Game Type']

        #Set player attributes as available, requires already populated player list
        for pid, attributes in data.iteritems():
            if pid != 16:
                player = replay.person[pid]
                player.color_text = attributes['Color']
                player.team = attributes['Teams'+replay.type]
                player.choosen_race = attributes['Race']
                player.difficulty = attributes['Difficulty']
                player.type = attributes['Player Type']
                    
        return replay
    
#####################################################

class RecorderProcessor(Processor):
    def process(self, replay):
        recorders = list(replay.people)
        for person in list(replay.people):
            if person.pid in replay.other_people:
                recorders.remove(person)
                
        if len(recorders) == 1:
            replay.recorder = recorders[0]
            replay.recorder.recorder = True
            
        return replay

#####################################################

class MessageProcessor(Processor):
    def process(self, replay):
        for message in replay.messages:
            try:
                message.sender = replay.person[message.sender_id]
            except KeyError:
                #Some sites will add messages as a non-existant player
                #In this instances, just drop the messages
                pass
                
        return replay

#####################################################
    
class TeamsProcessor(Processor):
    def process(self, replay):
        for player in replay.players:
            replay.teams[player.team].append(player)
            
        return replay
    
#####################################################

class EventProcessor(Processor):
    def process(self, replay):
        replay.events_by_type = defaultdict(list)
        for event in replay.events:
            if event.is_local:
                person = replay.person[event.pid]
                event.player = person
                person.events.append(event)
                
            event.apply()
            replay.events_by_type[event.name].append(event)    

        return replay

#####################################################

class ApmProcessor(Processor):
    def process(self, replay):
        # Set up needed variables
        for player in replay.players:
            player.avg_apm = 0
            player.aps = dict() # Doesn't contain seconds with zero actions
            player.apm = dict() # Doesn't contain minutes with zero actions
        # Gather data
        for event in replay.events:
            if event.is_local and event.is_player_action:
                person = event.player
                if not person.is_observer:
                    # Calculate APS, APM and average
                    if event.second in person.aps:
                        person.aps[event.second] += 1
                    else:
                        person.aps[event.second] = 1
                        
                    minute = event.second/60
                    if minute in person.apm:
                        person.apm[minute] += 1
                    else:
                        person.apm[minute] = 1
                        
                    person.avg_apm += 1

        # Average the APM for actual players
        for player in replay.players:
            player.avg_apm /= player.events[-1].second/60.0
            
        return replay

#####################################################

class ResultsProcessor(Processor):
    def _process_results(self, replay):
        #Knowing the team results, map results to the players as well
        for player in replay.players:
            player.result = replay.results[player.team]

    def process(self, replay):
        # Check if replay file has recorded the winner
        remaining = set()
        for player in replay.players:
            if player.outcome == 1:
                replay.results[player.team] = "Won"
            elif player.outcome == 2:
                replay.results[player.team] = "Lost"
            else:
                remaining.add(player.team)
        if len(remaining) == 0:
            self._process_results(replay)
            return replay
        
        #Remove players from the teams as they drop out of the game   
        replay.results = dict([team, len(players)] for team, players in replay.teams.iteritems())
        
        for event in replay.events_by_type['PlayerLeave']:
            #Some observer actions seem to be recorded, they aren't on teams anyway
            #Their pid will always be higher than the players
            if event.pid <= len(replay.players):
                team = replay.person[event.pid].team
                replay.results[team] -= 1 
                
        #mark all teams with no players left as losing, save the rest of the teams
        remaining = set()
        for team, count in replay.results.iteritems():
            if count == 0:
                replay.results[team] = "Lost"
            else:
                remaining.add(team)
        
        #If, at the end, only one team remains then that team has won
        if len(remaining) == 1:
            replay.results[remaining.pop()] = "Won"
        
        #Because you can also end the game by destroying all buildings, games
        #with 1 player teams can't be known unless all other players leave
        #we also can't do this if replay.recorder is unknown
        elif replay.type != 'FFA' and replay.type != '1v1' and replay.recorder:
            #The other results are unknown except in the (common) case that the
            #recorder is the last one on his team to leave. In this case, the
            #result for his team can be known
            for team in set(remaining):
                #the new set above is important because you shouldn't modify 
                #elements in collections that you are currently looping over
                if team == replay.recorder.team and replay.results[team] == 1:
                    replay.results[team] = "Lost"
                    remaining.remove(team)
                else:
                    replay.results[team] = "Unknown"
            
            #If, at the end, only one team remains then that team has won
            if len(remaining) == 1:
                replay.results[remaining.pop()] = "Won"
                replay.winner_known = True
        
        #If the winner can't be known mark all remaining player.result as unknown
        else:
            for team in remaining:
                replay.results[team] = "Unknown"
        
        self._process_results(replay)
            
        return replay
