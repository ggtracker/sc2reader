# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import json
from collections import defaultdict

from sc2reader import log_utils
from sc2reader.utils import Length
from sc2reader.factories.plugins.utils import PlayerSelection, GameState, JSONDateEncoder, plugin


@plugin
def toJSON(replay, **user_options):
    options = dict(cls=JSONDateEncoder)
    options.update(user_options)
    obj = toDict()(replay)
    return json.dumps(obj, **options)


@plugin
def toDict(replay):
    # Build observers into dictionary
    observers = list()
    for observer in replay.observers:
        messages = list()
        for message in getattr(observer, 'messages', list()):
            messages.append({
                'time': message.time.seconds,
                'text': message.text,
                'is_public': message.to_all
            })
        observers.append({
            'name': getattr(observer, 'name', None),
            'pid': getattr(observer, 'pid', None),
            'messages': messages,
        })

    # Build players into dictionary
    players = list()
    for player in replay.players:
        messages = list()
        for message in player.messages:
            messages.append({
                'time': message.time.seconds,
                'text': message.text,
                'is_public': message.to_all
            })
        players.append({
            'avg_apm': getattr(player, 'avg_apm', None),
            'color': player.color.__dict__ if hasattr(player, 'color') else None,
            'handicap': getattr(player, 'handicap', None),
            'name': getattr(player, 'name', None),
            'pick_race': getattr(player, 'pick_race', None),
            'pid': getattr(player, 'pid', None),
            'play_race': getattr(player, 'play_race', None),
            'result': getattr(player, 'result', None),
            'type': getattr(player, 'type', None),
            'uid': getattr(player, 'uid', None),
            'url': getattr(player, 'url', None),
            'messages': messages,
        })

    # Consolidate replay metadata into dictionary
    return {
        'gateway': getattr(replay, 'gateway', None),
        'map_name': getattr(replay, 'map_name', None),
        'file_time': getattr(replay, 'file_time', None),
        'filehash': getattr(replay, 'filehash', None),
        'unix_timestamp': getattr(replay, 'unix_timestamp', None),
        'date': getattr(replay, 'date', None),
        'utc_date': getattr(replay, 'utc_date', None),
        'speed': getattr(replay, 'speed', None),
        'category': getattr(replay, 'category', None),
        'type': getattr(replay, 'type', None),
        'is_ladder': getattr(replay, 'is_ladder', False),
        'is_private': getattr(replay, 'is_private', False),
        'filename': getattr(replay, 'filename', None),
        'file_time': getattr(replay, 'file_time', None),
        'frames': getattr(replay, 'frames', None),
        'build': getattr(replay, 'build', None),
        'release': getattr(replay, 'release_string', None),
        'game_fps': getattr(replay, 'game_fps', None),
        'game_length': getattr(getattr(replay, 'game_length', None), 'seconds', None),
        'players': players,
        'observers': observers,
        'real_length': getattr(getattr(replay, 'real_length', None), 'seconds', None),
        'real_type': getattr(replay, 'real_type', None),
        'time_zone': getattr(replay, 'time_zone', None),
        'versions': getattr(replay, 'versions', None)
    }


@plugin
def APMTracker(replay):
    """
    Builds ``player.aps`` and ``player.apm`` dictionaries where an action is
    any Selection, Hotkey, or Ability event.

    Also provides ``player.avg_apm`` which is defined as the sum of all the
    above actions divided by the number of seconds played by the player (not
    necessarily the whole game) multiplied by 60.
    """
    for player in replay.players:
        player.aps = defaultdict(int)
        player.apm = defaultdict(int)
        player.seconds_played = replay.length.seconds

        for event in player.events:
            if event.name == 'SelectionEvent' or 'AbilityEvent' in event.name or 'Hotkey' in event.name:
                player.aps[event.second] += 1
                player.apm[int(event.second/60)] += 1

            elif event.name == 'PlayerLeaveEvent':
                player.seconds_played = event.second

        if len(player.apm) > 0:
            player.avg_apm = sum(player.aps.values())/float(player.seconds_played)*60
        else:
            player.avg_apm = 0

    return replay

@plugin
def CreepTracker(replay):
    from itertools import izip_longest, dropwhile
    from random import random
    from math import sqrt, pi
    
    def add_to_list(control_pid,unit_id,unit_location,\
                unit_type,event_time, creep_generating_units_list):
        length_cgu_list = len(creep_generating_units_list[control_pid])
        if length_cgu_list==0:
            creep_generating_units_list[control_pid].append([(unit_id, unit_location,unit_type,event_time)])
        else:
            previous_list = creep_generating_units_list[control_pid][length_cgu_list-1][:]
            previous_list.append((unit_id, unit_location,unit_type,event_time))
            creep_generating_units_list[control_pid].append(previous_list)
                                                
    def in_circles(point_x,point_y,cgu_radius):
        for cgu in cgu_radius:
            circle_x = cgu[0][0]
            circle_y = cgu[0][1]
            radius = cgu[1]
            distance = (circle_x-point_x)**2 + (circle_y-point_y)**2
            if distance < (radius*radius):
                return 1
        return 0

    def distance(point1,point2):
        distance = (point1[0]-point2[0])**2  + (point1[1]-point2[1])**2
        return distance

    def calculate_area(cgu_radius):
        if len(cgu_radius)==1:
            print "Area Calculated",pi*(cgu_radius[0][1]**2)
            return pi*(cgu_radius[0][1]**2)
        
         # from cgu_radius get a square which surrounds maximum
            # possible area that the creep lies in           
        max_x = max(cgu_radius, key=lambda x: x[0][0]+x[1])
        max_y = max(cgu_radius, key=lambda x: x[0][1]+x[1])
        min_x =  min(cgu_radius, key=lambda x: x[0][0] - x[1])
        min_y =  min(cgu_radius, key=lambda x: x[0][1] - x[1])

        max_x = max_x[0][0] + max_x[1]
        max_y = max_y[0][1] + max_y[1]
        min_x = min_x[0][0] - min_x[1]
        min_y = min_y[0][1] - min_y[1]

        area = 0
        for x in range(min_x,max_x):
            for y in range(min_y,max_y):
                if in_circles(x,y,cgu_radius):
                        area+=1
        return area
        

    def single_linkage_clustering(cgu_points, maxR,labels=0,cgu_length = 0):
        inf = -1000
        if labels==0:
            labels = [0 for x in cgu_points]
            cgu_length = len(cgu_points)
        if len(cgu_points) ==1:
            return [0]
        
        # calculate distance array
        distance_array = list()
        for i in range (len(cgu_points)):
            i_lengths = list()
            for j in range(len(cgu_points)):
                if i !=j:
                    if cgu_points[i][0] == inf and cgu_points [j][0] == inf:
                        i_lengths.append(-inf)
                    else:
                        i_lengths.append(distance(cgu_points[i], cgu_points[j]))
                
            distance_array.append(i_lengths)
        
        #Find closest point distance for each point
        min_array = map(lambda x:min(x), distance_array)

        #combine 2 points with smallest distance
        min_distance = min(min_array)
        if min_distance < maxR:
            point1 = min_array.index(min_distance)
            point2 = min_array[point1+1:].index(min_distance)+point1+1
            #label each cgu points
            current_label = max(labels)+1 if labels[point1] ==0 and\
                             labels[point2] ==0 else max(labels[point1],labels[point2])
            labels[point1] = current_label
            labels[point2] = current_label
            labels.append(current_label)

            new_x = (cgu_points[point1][0] + cgu_points[point2][0])/2
            new_y = (cgu_points[point1][1] + cgu_points[point2][1])/2
            cgu_points[point1]=(inf,inf)
            cgu_points[point2]=(inf,inf)
            cgu_points.append((new_x,new_y))
            
            labels = single_linkage_clustering(cgu_points,maxR,labels,cgu_length)
            return labels[0:cgu_length]
        else:
            return_value = labels[0:cgu_length]
            return return_value
        
    
    #Get Map Size
    mapinfo = replay.map.archive.read_file('MapInfo')
    mapSizeX = ord(mapinfo[16])
    mapSizeY = ord(mapinfo[20])
    mapSize = mapSizeX * mapSizeX/100

    creep_generating_units_list = dict()
    
    for player in replay.players:
        player.creep_spread_by_minute = defaultdict(int)
        player.max_creep_spread = int()
        creep_generating_units_list[player.pid] = list()
    try:
        replay.tracker_events
    except AttributeError:
        print "Replay does not have tracker events"
        return replay

    for tracker_event,game_event in izip_longest(replay.tracker_events,replay.game_events):
        
        # First search things that generate creep
        # Tumor, hatcheries, nydus and overlords generating creep

        if tracker_event and tracker_event.name == "UnitInitEvent":
            units = ["CreepTumor", "Hatchery","Nydus"] # check nydus name
            if tracker_event.unit_type_name in units:
                add_to_list(tracker_event.control_pid,tracker_event.unit_id,\
                            (tracker_event.x, tracker_event.y), \
                            tracker_event.unit_type_name,\
                            tracker_event.second,\
                            creep_generating_units_list)

        if game_event and game_event.name == "AbilityEvent":
            
            if game_event.ability_name == "GenerateCreep":
                add_to_list(game_event.control_pid,game_event.unit_id,\
                            (game_event.x, game_event.y), \
                            game_event.unit_type_name,\
                            game_event.second,\
                            creep_generating_units_list)
               
        # # Removes creep generating units that were destroyed
        if tracker_event and tracker_event.name == "UnitDiedEvent":
            for player in creep_generating_units_list:
                length_cgu_list = len(creep_generating_units_list[player])
                if length_cgu_list ==0:
                    break
                cgu_per_player = creep_generating_units_list[player][length_cgu_list-1]
                creep_generating_died = dropwhile(lambda x: x[0] != tracker_event.unit_id, \
                                            cgu_per_player)
                for creep_generating_died_unit in creep_generating_died:

                    cgu_per_player.remove(creep_generating_died_unit)
                    creep_generating_units_list[player].append(cgu_per_player)
            
    #reduce all events to last event in the minute
    last_minute_found = 0
    for player in replay.player:
        cgu_per_player_new = list()
        for cgu_per_player in creep_generating_units_list[player]:
            if len(cgu_per_player) ==0:
                continue
            cgu_last_event_time = cgu_per_player[-1][3]
        
            if (cgu_last_event_time/60)>last_minute_found:
                last_minute_found = cgu_last_event_time/60
                cgu_per_player_new.append(cgu_per_player)
        cgu_per_player = cgu_per_player_new
    

    max_creep_spread=defaultdict()
    for player in replay.player:
        # convert cg u list into centre of circles and radius
        unit_name_to_radius = {'CreepTumor': 15, "Hatchery":17,\
                            "GenerateCreep": 10, "Nydus": 5 }
        
        max_creep_spread[player] = 0
        
        for index,cgu_per_player in enumerate(creep_generating_units_list[player]):
            
            cgu_radius = map(lambda x: (x[1],   unit_name_to_radius[x[2]]),\
                                  cgu_per_player)
            cgu_points  = map(lambda x: x[0],cgu_radius)

            if cgu_points:
                labels = single_linkage_clustering(cgu_points,350)
            else:
                if index != 0:
                    replay.player[player].creep_spread_by_minute[cgu_last_event_time+1] = 0
                continue
            
            area = 0
            #if all labels 0 (all separate clusters) calculate it separately
            if max(labels) ==0:
                for cgu_radi in cgu_radius:
                    area+= pi * cgu_radi[1]**2
 
                cgu_last_event_time = cgu_per_player[-1][3]/60
                replay.player[player].creep_spread_by_minute[cgu_last_event_time] = area/mapSize
                continue

            count =0
            while True:
                clusters = filter(lambda x : True if x[0] == count else\
                  False , zip(labels,cgu_radius)  )
               
                cgu_clusters = map(lambda x:x[1], clusters)
                if count==0:
                    for cgu_radi in cgu_clusters:
                        area+= pi * cgu_radi[1]**2
                    count+=1
                    continue
                if len(clusters) ==0:
                    break
                count+=1
                area += calculate_area(cgu_clusters)
            cgu_last_event_time = cgu_per_player[-1][3]/60
            replay.player[player].creep_spread_by_minute[cgu_last_event_time] = area/mapSize

            if area>max_creep_spread[player]:
                 max_creep_spread[player] =area


    for player in replay.player:
        replay.player[player].max_creep_spread = max_creep_spread[player]/mapSize

    return replay 


@plugin
def SelectionTracker(replay):
    debug = replay.opt.debug
    logger = log_utils.get_logger(SelectionTracker)

    for person in replay.entities:
        # TODO: A more robust person interface might be nice
        person.selection_errors = 0
        player_selections = GameState(PlayerSelection())
        for event in person.events:
            error = False
            if event.name == 'SelectionEvent':
                selections = player_selections[event.frame]
                control_group = selections[event.control_group].copy()
                error = not control_group.deselect(event.mask_type, event.mask_data)
                control_group.select(event.new_units)
                selections[event.control_group] = control_group
                if debug:
                    logger.info("[{0}] {1} selected {2} units: {3}".format(Length(seconds=event.second), person.name, len(selections[0x0A].objects), selections[0x0A]))

            elif event.name == 'SetToHotkeyEvent':
                selections = player_selections[event.frame]
                selections[event.control_group] = selections[0x0A].copy()
                if debug:
                    logger.info("[{0}] {1} set hotkey {2} to current selection".format(Length(seconds=event.second), person.name, event.hotkey))

            elif event.name == 'AddToHotkeyEvent':
                selections = player_selections[event.frame]
                control_group = selections[event.control_group].copy()
                error = not control_group.deselect(event.mask_type, event.mask_data)
                control_group.select(selections[0x0A].objects)
                selections[event.control_group] = control_group
                if debug:
                    logger.info("[{0}] {1} added current selection to hotkey {2}".format(Length(seconds=event.second), person.name, event.hotkey))

            elif event.name == 'GetFromHotkeyEvent':
                selections = player_selections[event.frame]
                control_group = selections[event.control_group].copy()
                error = not control_group.deselect(event.mask_type, event.mask_data)
                selections[0xA] = control_group
                if debug:
                    logger.info("[{0}] {1} retrieved hotkey {2}, {3} units: {4}".format(Length(seconds=event.second), person.name, event.control_group, len(selections[0x0A].objects), selections[0x0A]))

            else:
                continue

            # TODO: The event level interface here should be improved
            #       Possibly use 'added' and 'removed' unit lists as well
            event.selected = selections[0x0A].objects
            if error:
                person.selection_errors += 1
                if debug:
                    logger.warn("Error detected in deselection mode {0}.".format(event.mask_type))

        person.selection = player_selections
        # Not a real lock, so don't change it!
        person.selection.locked = True

    return replay
