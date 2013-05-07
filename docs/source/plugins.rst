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

Where buffer is a control group 0-9 or 10 which represents the active selection.

Keep in mind that the buffers are only updated for the following events:

 * The active selection changes
 * When unit types change (eggs hatch, tanks siege)

Buffers are not updated when units die unless the unit dies while selected (because
the active selection must change). Units that die while deslected won't get deselected
until the next time the control group they were saved in becomes active.
