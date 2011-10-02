from __future__ import absolute_import
from datetime import datetime
import functools
try:
    import json
except:
    import simplejson as json

class __JSONDateEncoder__(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return json.JSONEncoder.default(self, obj)


def jsonProcessor(replay):
    def __getattr(object, name, default):
        return getattr(object, name, default)
    _getattr = functools.partial(__getattr, default=None)
    json_data = {
        'gateway': _getattr(replay, 'gateway'),
        'map': _getattr(replay, 'map'),
        'file_time': _getattr(replay, 'file_time'),
        'unix_timestamp': _getattr(replay, 'unix_timestamp'),
        'date': _getattr(replay, 'date'),
        'utc_date': _getattr(replay, 'utc_date'),
        'speed': _getattr(replay, 'speed'),
        'category': _getattr(replay, 'category'),
        'type': _getattr(replay, 'type'),
        'is_ladder': _getattr(replay, 'is_ladder', default=False),
        'is_private': _getattr(replay, 'is_private', default=False),
        'filename': _getattr(replay, 'filename'),
        'file_time': _getattr(replay, 'file_time'),
        'frames': _getattr(replay, 'frames'),
        'build': _getattr(replay, 'build'),
        'release': _getattr(replay, 'release_string'),
    }
    players = []
    for player in replay.players:
        p = {
            'avg_apm': _getattr(player, 'avg_apm'),
            'color': _getattr(player, 'color'),
            'name': _getattr(player, 'name'),
            'pick_race': _getattr(player, 'pick_race'),
            'pid': _getattr(player, 'pid'),
            'play_race': _getattr(player, 'play_race'),
            'result': _getattr(player, 'result'),
            'type': _getattr(player, 'type'),
            'uid': _getattr(player, 'uid'),
            'url': _getattr(player, 'url'),
            'messages': [],
        }
        for message in player.messages:
            msg_time = '%s:%s' % ((message.time/16)/60, (message.time/16)%60)
            p['messages'].append({
                'time': msg_time,
                'text': message.text,
                'is_public': message.sent_to_all
            })
        players.append(p)
    json_data['players'] = players
    observers = []
    for observer in replay.observers:
        observers.append({
            'name': _getattr(observer, 'name'),
            'messages': _getattr(observer, 'messages', default=[]),
            'pid': _getattr(observer, 'pid'),
        })
    json_data['observers'] = observers
    encoded = json.dumps(json_data, cls=__JSONDateEncoder__)
    return encoded
