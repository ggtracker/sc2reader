from __future__ import absolute_import

from datetime import datetime
from sc2reader.processors.todict import toDict


try:
    import json
except:
    import simplejson as json


class __JSONDateEncoder__(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return json.JSONEncoder.default(self, obj)

class jsonEncoder(object):

    def __init__(self, **user_options):
        self.options = dict(cls=__JSONDateEncoder__)
        self.options.update(user_options)

    def __call__(self, replay):
        return json.dumps(toDict(replay), **self.options)


def jsonEncode(replay):
    return jsonEncoder().__call__(replay)
