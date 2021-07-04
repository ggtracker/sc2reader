# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division


class SelectionTracker(object):
    """
    Tracks a player's active selection as an input into other plugins.

    In some situations selection tracking isn't perfect. The plugin will
    detect these situations and report errors. For a player will a high
    level of selection errors, it may be best to ignore the selection
    results as they could have been severely compromised.

    Exposes the following interface, directly integrated into the player:

        for person in replay.entities:
            total_errors = person.selection_errors

            selection = person.selection
            control_group_0 = selection[0]
            ...
            control_group_9 = selection[9]
            active_selection = selection[10]

    # TODO: list a few error inducing situations
    """

    name = "SelectionTracker"

    def handleInitGame(self, event, replay):
        for person in replay.entities:
            person.selection = dict()
            for i in range(11):
                person.selection[i] = list()
            person.selection_errors = 0

    def handleSelectionEvent(self, event, replay):
        selection = event.player.selection[event.control_group]
        new_selection, error = self._deselect(
            selection, event.mask_type, event.mask_data
        )
        new_selection = self._select(new_selection, event.objects)
        event.player.selection[event.control_group] = new_selection
        if error:
            event.player.selection_errors += 1

    def handleGetControlGroupEvent(self, event, replay):
        selection = event.player.selection[event.control_group]
        new_selection, error = self._deselect(
            selection, event.mask_type, event.mask_data
        )
        event.player.selection[10] = new_selection
        if error:
            event.player.selection_errors += 1

    def handleSetControlGroupEvent(self, event, replay):
        event.player.selection[event.control_group] = event.player.selection[10]

    def handleAddToControlGroupEvent(self, event, replay):
        selection = event.player.selection[event.control_group]
        new_selection, error = self._deselect(
            selection, event.mask_type, event.mask_data
        )
        new_selection = self._select(new_selection, event.player.selection[10])
        event.player.selection[event.control_group] = new_selection
        if error:
            event.player.selection_errors += 1

    def _select(self, selection, units):
        return sorted(set(selection + units))

    def _deselect(self, selection, mode, data):
        """
        Returns false if there was a data error when deselecting
        """
        if mode == "None":
            return selection, False

        selection_size, data_size = len(selection), len(data)

        if mode == "Mask":
            # Deselect objects according to deselect mask
            sfilter = lambda bit_u: not bit_u[0]
            mask = data + [False] * (selection_size - data_size)
            new_selection = [u for (bit, u) in filter(sfilter, zip(mask, selection))]
            error = data_size > selection_size

        elif mode == "OneIndices":
            # Deselect objects according to indexes
            clean_data = list(filter(lambda i: i < selection_size, data))
            new_selection = [u for i, u in enumerate(selection) if i < selection_size]
            error = len(list(filter(lambda i: i >= selection_size, data))) != 0

        elif mode == "ZeroIndices":
            # Select objects according to indexes
            clean_data = list(filter(lambda i: i < selection_size, data))
            new_selection = [selection[i] for i in clean_data]
            error = len(clean_data) != data_size

        return new_selection, error
