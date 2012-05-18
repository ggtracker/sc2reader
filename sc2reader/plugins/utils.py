from __future__ import absolute_import

import json
from functools import wraps
from datetime import datetime
from sc2reader import log_utils

from functools import wraps
def plugin(func):
    @wraps(func)
    def wrapper(**options):
        @wraps(func)
        def call(*args, **kwargs):
            opt = kwargs.copy()
            opt.update(options)
            return func(*args, **opt)
        return call
    return wrapper

class JSONDateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return json.JSONEncoder.default(self, obj)


class GameState(dict):
    def __init__(self, initial_state):
        self[0] = initial_state

    def __getitem__(self, frame):
        if frame in self:
            return super(GameState, self).__getitem__(frame)

        # If this particular key doesn't exist, create it
        prev_frame = sorted(filter(lambda key: key < frame, self.keys()))[-1]
        state = self[prev_frame].copy()
        self[frame] = state
        return state


class UnitSelection(object):
    def __init__(self, *new_objects):
        self.logger = log_utils.get_logger(UnitSelection)
        self.objects = list()
        self.select(new_objects)

    def select(self, new_objects):
        object_set = set(self.objects+list(new_objects))
        self.objects = sorted(object_set, key=lambda obj: obj.id)

    def deselect(self, mode, data):
        if mode == 0x01:
            """ Deselect objects according to deselect mask """
            mask = data
            if len(mask) < len(self.objects):
                # pad to the right
                mask = mask+[False,]*(len(self.objects)-len(mask))
            self.logger.debug("Deselection Mask: {0}".format(mask))
            self.objects = [ obj for (slct, obj) in filter(lambda (slct, obj): not slct, zip(mask, self.objects)) ]

        elif mode == 0x02:
            """ Deselect objects according to indexes """
            self.objects = [ self.objects[i] for i in range(len(self.objects)) if i not in data ]

        elif mode == 0x03:
            """ Deselect objects according to indexes """
            self.objects = [ self.objects[i] for i in data ]

    def __str__(self):
        return ', '.join(str(obj) for obj in self.objects)

    def copy(self):
        return UnitSelection(*self.objects)


class PlayerSelection(dict):
    def __init__(self):
        for bank in range(0x00, 0x0B):
            self[bank]=UnitSelection()

    def copy(self):
        new = PlayerSelection()
        for bank, selection in self.iteritems():
            new[bank] = UnitSelection(*selection.objects)
        return new
