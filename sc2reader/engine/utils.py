# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from bisect import bisect_left


class GameState(dict):
    def __init__(self, initial_state):
        self._frames = list()
        self._frameset = set()
        self[0] = initial_state
        self.locked = False

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

        # If we've locked the game state we don't need deep copies anymore
        if self.locked:
            state = self[prev_frame]
        else:
            # Copy the previous state and use it as our basis here
            state = self[prev_frame]
            if hasattr(state, "copy"):
                state = state.copy()

        self[frame] = state
        return state

    def __setitem__(self, frame, value):
        if frame not in self._frameset:
            self._frames.insert(bisect_left(self._frames, frame), frame)
            self._frameset.add(frame)

        super(GameState, self).__setitem__(frame, value)
