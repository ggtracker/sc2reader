Processors
=================

jsonEncode
---------------

    The jsonEncode processor can be used to return a encoded json string instead
    of a replay object. This shortcut processor might be useful for web apps or
    interprocess communication perhaps.

    ::

        >>> import sc2reader;
        >>> from sc2reader.processors import jsonEncode
        >>> print sc2reader.read_file('test_replays/1.4.0.19679/36663.SC2Replay', processors=[jsonEncode])

    The processor also comes in a slightly different class based flavor which
    allows you to configure the encoding process by basically piping your options
    through to python's ``json.dumps`` standard library function.

    ::

        >>> import sc2reader;
        >>> from sc2reader.processors import jsonEncoder
        >>> print sc2reader.read_file(
        ...     'test_replays/1.4.0.19679/36663.SC2Replay',
        ...     processors=[jsonEncoder(indent=4)]
        ... )
        {
            "category": "Ladder",
            "map": "Xel'Naga Caverns",
            "players": [
                {
                    "uid": 934659,
                    "play_race": "Terran",
                    "color": {
                        "a": 255,
                        "r": 180,
                        "b": 30,
                        "g": 20
                    },
                    "pick_race": "Terran",
                    "pid": 1,
                    "result": "Win",
                    "name": "MaNNErCHOMP",
                    "url": "http://us.battle.net/sc2/en/profile/934659/1/MaNNErCHOMP/",
                    "messages": [
                        {
                            "text": "lol",
                            "is_public": true,
                            "time": 9
                        },
                        {
                            "text": "sup bra",
                            "is_public": true,
                            "time": 23
                        },
                        {
                            "text": ":(",
                            "is_public": true,
                            "time": 48
                        }
                    ],
                    "type": "Human",
                    "avg_apm": 148.13353566009107
                },
                {
                {
                    "uid": 493391,
                    "play_race": "Protoss",
                    "color": {
                        "a": 255,
                        "r": 0,
                        "b": 255,
                        "g": 66
                    },
                    "pick_race": "Protoss",
                    "pid": 2,
                    "result": "Loss",
                    "name": "vVvHasuu",
                    "url": "http://us.battle.net/sc2/en/profile/493391/1/vVvHasuu/",
                    "messages": [],
                    "type": "Human",
                    "avg_apm": 143.52583586626139
                }
            ],
            "type": "1v1",
            "is_ladder": true,
            "utc_date": "2011-09-21 06:49:47",
            "file_time": 129610613871027307,
            "observers": [],
            "frames": 10552,
            "build": 19679,
            "date": "2011-09-21 02:49:47",
            "unix_timestamp": 1316587787,
            "filename": "test_replays/1.4.0.19679/36663.SC2Replay",
            "speed": "Faster",
            "gateway": "us",
            "is_private": false,
            "release": "1.4.0.19679"
        }