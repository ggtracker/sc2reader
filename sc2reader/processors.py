from collections import defaultdict
from sc2reader.objects import *

def PeopleProcessor(replay):
    obs_players = list(replay.player_names)
    for player in replay.players:
        obs_players.remove(player.name)
    
    for pid,name in enumerate(obs_players):
        replay.observers.append(Observer(pid+len(replay.players)+1,name))
    
    for person in replay.observers+replay.players:
        replay.people.append(person)
        replay.person[person.pid] = person
        
    return replay
        
def AttributeProcessor(replay):
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
    

def RecorderProcessor(replay):
    recorders = list(replay.people)
    for person in list(replay.people):
        if person.pid in replay.other_people:
            recorders.remove(person)
            
    if len(recorders) == 1:
        replay.recorder = recorders[0]
        replay.recorder.recorder = True
        
    return replay

def MessageProcessor(replay):
    for message in replay.messages:
        try:
            message.sender = replay.person[message.sender_id]
        except KeyError:
            #Some sites will add messages as a non-existant player
            #In this instances, just drop the messages
            pass
            
    return replay
    
def TeamsProcessor(replay):
    for player in replay.players:
        replay.teams[player.team].append(player)
        
    return replay
    

def EventProcessor(replay):
    replay.events_by_type = defaultdict(list)
    for event in replay.events:
        replay.events_by_type[event.name].append(event)    

    for event in replay.events:
        if event.is_local:
            person = replay.person[event.player]
            person.events.append(event)
            
    return replay
            
def ApmProcessor(replay):
    for event in replay.events:
        if event.is_local and event.is_player_action:
            person = replay.person[event.player]
            if not person.is_obs:
                # Calculate APS, APM and average
                if event.seconds in person.aps:
                    person.aps[event.seconds] += 1
                else:
                    person.aps[event.seconds] = 1
                    
                minute = event.seconds/60
                if minute in person.apm:
                    person.apm[minute] += 1
                else:
                    person.apm[minute] = 1
                    
                person.avg_apm += 1

    # Average the APM for actual players
    for player in replay.players:
        player.avg_apm /= player.events[-1].seconds/60.0
        
    return replay
        
def ResultsProcessor(replay):
    #Remove players from the teams as they drop out of the game   
    replay.results = dict([team, len(players)] for team, players in replay.teams.iteritems())
    
    for event in replay.events_by_type['PlayerLeave']:
        #Some observer actions seem to be recorded, they aren't on teams anyway
        #Their pid will always be higher than the players
        if event.player <= len(replay.players):
            team = replay.person[event.player].team
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
    
    #Knowing the team results, map results to the players as well
    for player in replay.players:
        player.result = replay.results[player.team]
        
    return replay