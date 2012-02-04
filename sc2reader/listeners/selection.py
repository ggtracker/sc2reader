from sc2reader import events
from sc2reader import utils

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

class SelectionListener(object):

    def setup(self, replay):
        for player in replay.people:
            player.selections = GameState(PlayerSelection())

    def __call__(self, event, replay):

        if isinstance(event, events.HotkeyEvent):
            selections = event.player.selections[event.frame]
            hotkey_selection = selections[event.hotkey]

            if isinstance(event, events.SetToHotkeyEvent):
                selections[event.hotkey] = selections[0x0A].copy()
                print "[{0}] {1} set hotkey {2} to current selection".format(utils.Length(seconds=event.second),event.player.name,event.hotkey)

            if isinstance(event, events.AddToHotkeyEvent):
                selections[event.hotkey].deselect(*event.deselect)
                selections[event.hotkey].select(selections[0x0A].objects)
                print "[{0}] {1} added current selection to hotkey {2}".format(utils.Length(seconds=event.second),event.player.name,event.hotkey)

            if isinstance(event, events.GetFromHotkeyEvent):
                selections[0x0A] = selections[event.hotkey]
                print "[{0}] {1} retrieved hotkey {2}: {3}".format(utils.Length(seconds=event.second),event.player.name,event.hotkey,selections[event.hotkey])

            event.selected = selections[event.hotkey]

        if isinstance(event, events.SelectionEvent):
            selections = event.player.selections[event.frame]
            selections[0x0A].deselect(*event.deselect)
            selections[0x0A].select(event.objects)

            event.selected = selections[0x0A]
            print "[{0}] {1} selected: {2}".format(utils.Length(seconds=event.second),event.player.name,event.selected)