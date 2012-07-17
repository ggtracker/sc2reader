from __future__ import absolute_import

import json
from functools import wraps
from datetime import datetime
from sc2reader.log_utils import loggable

from functools import wraps
from bisect import bisect_left

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
        self._frames = list()
        self._frameset = set()
        self[0] = initial_state

    def __getitem__(self, frame):
        if frame in self:
            return super(GameState, self).__getitem__(frame)

        # Get the previous frame from our sorted frame list
        # bisect_left returns the left most key where an item is
        # less than or equal to the value in that key. If it is
        # less than we need to subtract 1
        key = bisect_left(self._frames, frame)
        if key == len(self._frames) or self._frames[key] > frame:
            prev_frame = self._frames[key - 1]
        else:
            prev_frame = self._frames[key]

        # Copy the previous state and use it as our basis here
        state = self[prev_frame].copy()
        self[frame] = state
        return state

    def __setitem__(self, frame, value):
        if frame not in self._frameset:
            self._frames.insert(bisect_left(self._frames, frame), frame)
            self._frameset.add(frame)

        super(GameState, self).__setitem__(frame, value)


@loggable
class UnitSelection(object):
    def __init__(self, objects=None):
        self.objects = objects or list()

    def select(self, new_objects):
        new_set = set(self.objects+list(new_objects))
        self.objects = sorted(new_set,key=lambda obj: obj.id)

    def deselect(self, mode, data):
        """Returns false if there was a data error when deselecting"""
        size = len(self.objects)

        if mode == 0x01:
            """ Deselect objects according to deselect mask """
            mask = data
            if len(mask) < size:
                # pad to the right
                mask = mask+[False,]*(len(self.objects)-len(mask))

            self.logger.debug("Deselection Mask: {0}".format(mask))
            self.objects = [ obj for (slct, obj) in filter(lambda (slct, obj): not slct, zip(mask, self.objects)) ]
            return len(mask) <= size

        elif mode == 0x02:
            """ Deselect objects according to indexes """
            clean_data = filter(lambda i: i < size, data)
            self.objects = [ self.objects[i] for i in range(len(self.objects)) if i not in clean_data ]
            return len(clean_data) == len(data)

        elif mode == 0x03:
            """ Deselect objects according to indexes """
            clean_data = filter(lambda i: i < size, data)
            self.objects = [ self.objects[i] for i in clean_data ]
            return len(clean_data) == len(data)

        else:
            return True

    def __str__(self):
        return ', '.join(str(obj) for obj in self.objects)

    def copy(self):
        return UnitSelection(self.objects[:])


class PlayerSelection(dict):
    def __init__(self):
        for bank in range(0x00, 0x0B):
            self[bank]=UnitSelection()

    def copy(self):
        new = PlayerSelection()
        for bank, selection in self.iteritems():
            new[bank] = UnitSelection(selection.objects[:])
        return new
