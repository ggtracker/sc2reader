.. currentmodule:: sc2reader.replay

Main Structures
======================

The outline of the key structures in the replay object.


Replay
--------------

.. autoclass:: Replay

    .. autoattribute:: filename
    .. autoattribute:: frames
    .. autoattribute:: build
    .. autoattribute:: release_string
    .. autoattribute:: length
    .. autoattribute:: speed
    .. autoattribute:: type
    .. autoattribute:: category
    .. autoattribute:: is_ladder
    .. autoattribute:: is_private
    .. autoattribute:: map
    .. autoattribute:: gateway
    .. autoattribute:: events
    .. autoattribute:: results
    .. autoattribute:: teams
    .. autoattribute:: team
    .. autoattribute:: players
    .. autoattribute:: player
    .. autoattribute:: observers
    .. autoattribute:: people
    .. autoattribute:: person
    .. autoattribute:: humans
    .. autoattribute:: messages
    .. autoattribute:: recorder
    .. autoattribute:: winner_known


.. currentmodule:: sc2reader.objects


Team
----------------

.. autoclass:: Team

    .. autoattribute:: number
    .. autoattribute:: players
    .. autoattribute:: result
    .. autoattribute:: lineup


Person
-------------

.. autoclass:: Person

    .. autoattribute:: pid
    .. autoattribute:: name
    .. autoattribute:: is_observer
    .. autoattribute:: is_human
    .. autoattribute:: messages
    .. autoattribute:: events
    .. autoattribute:: recorder


Observer
---------------

.. autoclass:: Observer    



Player
------------------

.. autoclass:: Player

    .. autoattribute:: team
    .. autoattribute:: url
    .. autoattribute:: result
    .. autoattribute:: color
    .. autoattribute:: pick_race
    .. autoattribute:: play_race
    .. autoattribute:: difficulty
    .. autoattribute:: handicap
    .. autoattribute:: region
    .. autoattribute:: subregion
