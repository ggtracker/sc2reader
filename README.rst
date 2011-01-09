sc2reader
============

Parses replays from build version 16561 and up. After parsing, replays will have
the following structure::

    replay: {
        'attributes': dict([player number,list( Attribute )]),
        'build': int,
        'date': string,
        'events': list( Event ),
        'eventsByType': dict([string,list( Event )]),
        'length': (int,int),
        'map': string,
        'messages': list( Message ),
        'players': list( Player ),
        'recorder': Player,
        'releaseString': string,
        'results': dict([int,list( Player )]),
        'speed': string,
        'teams': dict([int, list( Player )]),
        'type': string
    }
    
And will contain the following objects::

    player: {
        'color': string,
        'difficulty': string,
        'handicap': int,
        'name': string,
        'pid': int (player number),
        'race': string,
        'recorder': boolean,
        'result': string("Won/Lost/Unknown"),
        'rgba': (int,int,int,int),
        'team': int,
        'type': string ("Human/Computer"),
        'url': string (us.battle.net/sc2 url)
    }
    
    event: {
        'name': string,
        'player': int (player number),
        'time': int (in frames),
        'timestr': "MM:SS",
    }
    
    message: {
        'player': int,
        'target': int,
        'text': string
        'time': (minutes,seconds),
    }
    
    attribute: {
        'name': string,
        'player': int,
        'value': varies by attribute,
    }
