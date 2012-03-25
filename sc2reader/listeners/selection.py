from __future__ import absolute_import

from sc2reader.listeners.utils import ListenerBase

import sc2reader
from sc2reader import events
from sc2reader import utils
from sc2reader import log_utils

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

class SelectionListener(ListenerBase):

    def setup(self, replay):
        for player in replay.people:
            player.selections = GameState(PlayerSelection())

    def accepts(self, event):
        return isinstance(event, events.SelectionEvent) or isinstance(event, events.HotkeyEvent)

    def __call__(self, event, replay):
        if replay.opt.debug:
            self.logger.debug("Event bytes: "+event.bytes.encode("hex"))

        selections = event.player.selections[event.frame]

        if isinstance(event, events.SetToHotkeyEvent):
            # Make a copy to decouple the hotkey from primary selection
            selections[event.hotkey] = selections[0x0A].copy()
            self.logger.info("[{0}] {1} set hotkey {2} to current selection".format(utils.Length(seconds=event.second),event.player.name,event.hotkey))

        elif isinstance(event, events.AddToHotkeyEvent):
            selections[event.hotkey].deselect(*event.deselect)
            selections[event.hotkey].select(selections[0x0A].objects)
            self.logger.info("[{0}] {1} added current selection to hotkey {2}".format(utils.Length(seconds=event.second),event.player.name,event.hotkey))

        elif isinstance(event, events.GetFromHotkeyEvent):
            # For some reason they leave the hotkey buffer unmodified so make a copy
            selections[0x0A] = selections[event.hotkey].copy()
            selections[0x0A].deselect(*event.deselect)
            self.logger.info("[{0}] {1} retrieved hotkey {2}, {3} units: {4}".format(utils.Length(seconds=event.second),event.player.name,event.hotkey,len(selections[0x0A].objects),selections[0x0A]))

        elif isinstance(event, events.SelectionEvent):
            selections[0x0A].deselect(*event.deselect)
            selections[0x0A].select(event.objects)
            self.logger.info("[{0}] {1} selected {2} units: {3}".format(utils.Length(seconds=event.second),event.player.name,len(selections[0x0A].objects),selections[0x0A]))

        event.selected = selections[0x0A]