Plugins
=============

A plugin is pretty much just a callable function or object that accepts a replay
file as a single argument. sc2reader supports assignment of plugins to different
resource types via the :meth:`SC2Factory.register_plugin` factory method.

::

    import sc2reader
    from sc2reader.plugins.replay import APMTracker, SelectionTracker
    sc2reader.register_plugin('Replay',APMTracker())
    sc2reader.register_plugin('Replay',SelectionTracker())

The order you register plugins is the order they are executed in so be careful to
put register in the right order if you have dependencies between plugins.


APMTracker
----------------

The APMTracker adds three simple fields based on a straight tally of non-camera
player action events such as selections, abilities, and hotkeys.

* ``player.aps`` = a dictionary of second => total actions in that second
* ``player.apm`` = a dictionary of minute => total actions in that minute
* ``player.avg_apm`` = Average APM as a float


SelectionTracker
--------------------

The :class:`SelectionTracker` plugin simulates every person's selection at every
frame in both the hotkey and active selection buffers. This selection information
is stored in ``person.selection`` as a two dimensional array of lists.

::

    unit_list = replay.player[1].selection[frame][buffer]

Where buffer is a hotkey 0-9 or 10 which represents the active selection.

There are a number of known flaws with the current tracking algorithm and/or the
source information on which it works:

* Deaths are not recorded. A selected unit that dies will be deselected though.
* Transformations are not recorded. A hotkey'd egg that hatches into 2 zerglings
  will not register and the egg will stay hotkeyed until the hotkey is over
  written. If the transformed unit is part of active selection the
  selection/deslection is handled properly.

To help expose these short comings a ``person.selection_errors`` tally is kept. An
error is recorded every time a selection event instructs us to do something that
would not be possible with what we believe to be the current selection. Such an
event would mean that our tracker went wrong previously.

Players that consistently use ``shift+ctrl+hotkey`` to add to hotkeys instead of
resetting hotkeys with ``ctrl+hotkey`` create tons of issues for this tracker
because selection changes in hotkeys are not recorded in the replay file.