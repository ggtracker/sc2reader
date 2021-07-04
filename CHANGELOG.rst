CHANGELOG
============

1.7.0 - May 17, 2021
--------------------
* Add DOI to the README #128
* Add various missing attributes for co-op replays #129
* Add support for python 3.8, 3.9 #132 #136
* Fix owner on an event with no unit #133
* Add support for ResourceTradeEvent #135
* Fix depot URL template #139

1.6.0 - July 30, 2020
---------------------
* Add support for protocol 80949 (StarCraft 5.0) #122
* Fix toJson script #118

1.5.0 - January 18, 2020
------------------------
* Add support for protocol 77379 #106 #107
* Workaround for missing data #102 #104

1.4.0 - August 19, 2019
-----------------------
* Add support for protocol 75689 #95

1.3.2 - August 9, 2019
----------------------
* Allow pytest #84
* Format code with black #87
* Fix UnitTypeChangeEvent.__str__ #92
* Add Stetmann #93

1.3.1 - November 29, 2018
-------------------------
* Parse backup if data is missing #69

1.3.0 - November 16, 2018
-------------------------
* Added support for protocol 70154 (StarCraft 4.7.0)
* Added support for Zeratul
* Updated CircleCI build for Python 3.7
* Fixed a bug with printing TrackerEvent

1.2.0 - October 7, 2018
-----------------------
* Added support for Tychus
* Verified that StarCraft 4.6.1 replays work

1.1.0 - June 26, 2018
---------------------
* Added support for protocol 65895 (StarCraft 4.4.0)

1.0.0 - May 18, 2018
--------------------
* Added support for protocol 48258 through 64469
* Update game data and scripts for generating game data
* Fix ggtracker/sc2reader CircleCI build for python 3
* Added support for parsing Co-op replays

0.8.0 - December 16, 2016
---------------------------
* Merged into ggtracker/sc2reader, which mostly means that we have a bunch of parsing fixes.  Thanks @StoicLoofah!

0.7.0 -
---------------------------

* Deprecated unit.killed_by in favor of unit.killing_player
* Added unit.killed_units
* Added unit.killing_unit
* Added UnitDiedEvent.killing_player
* Added UnitDiedEvent.killing_unit
* Deprecated UnitDiedEvent.killer_pid in favor of UnitDiedEvent.killing_player_id
* Deprecated UnitDiedEvent.killer in favor of UnitDiedEvent.killing_player
* Use generic UnitType and Ability classes for data. This means no more unit._type_class.__class__.__name__. But hopefully people were not doing that anyway.
* Now a CorruptTrackerFileError is raised when the tracker file is corrupted (generally only older resume_from_replay replays)
* Removed the defunct replay.player_names attribute.
* Removed the defunct replay.events_by_type attribute.
* Removed the defunct replay.other_people attribute.
* Replays can now be pickled and stored for later consumption.
* All references to the gateway attribute have been replaced in favor of region; e.g. replay.region
* Use generic UnitType and Ability classes for data. This means no more unit._type_class.__class__.__name__. But hopefully people were not doing that anyway.
* Now a CorruptTrackerFileError is raised when the tracker file is corrupted (generally only older resume_from_replay replays)
* Added replay.resume_from_replay flag. See replay.resume_user_info for additional info.
* PacketEvent is now ProgressEvent.
* SetToHotkeyEvent is now SetControlGroupEvent.
* AddToHotkeyEvent is now AddToControlGroupEvent.
* GetFromHotkeyEvent is now GetControlGroupEvent.
* PlayerAbilityEvent is no longer part of the event hierarchy.
* AbilityEvent doubled as both an abstract and concrete class (very bad, see #160). Now split into:
   * AbilityEvent is now CommandEvent
   * AbilityEvent is now BasicCommandEvent
* TargetAbilityEvent is now TargetUnitCommandEvent
* LocationAbilityEvent is now TargetPointCommandEvent
* SelfAbilityEvent is now DataCommandEvent
* Removed the defunct replay.player_names attribute.
* Removed the defunct replay.events_by_type attribute.
* Removed the defunct replay.other_people attribute.

* event.name is no longer a class property; it can only be accessed from an event instance.
* PingEvents now have new attributes:
   * event.to_all - true if ping seen by all
   * event.to_allies - true if ping seen by allies
   * event.to_observers - true if ping seen by observers
   * event.location - tuple of (event.x, event.y)


0.6.4 - September 22nd 2013
---------------------------

* Fix bug in code for logging errors.
* Fix siege tank supply count.
* Small improvements to message.events parsing.

0.6.3 - September 15th 2013
---------------------------

* Properly mark hallucinated units.

0.6.2 - September 5th 2013
--------------------------
* Fix rare bug where TargetedAbility events could overwrite unit types.
* Substantial performance boost (20% in local testing)
* Fixed serious bug with FileCaching that affected Python3 users.
* Plugins can now yield PluginExit events to broadcast their shutdown.

0.6.1 - August 13th 2013
------------------------

* Fix bug in event ordering that caused game events to process before tracker events.
* Fix APMTracker to count APM for all humans, not just players.

0.6.0 - August 12th 2013
------------------------

New Stuff:
~~~~~~~~~~~~~~~~

* Adds python 3.2+ support
* Adds support for patch 2.0.10.
* Adds experimental SC2Map.MapInfo parsing support.
* Implements new replay GameEngine and plugin support.
* Added a sc2json script contributed by @ChrisLundquist
* Adds plugin GameHeartNormalizer plugin by @StoicLoofah
* Hooked up coveralls.io for coverage reporting: https://coveralls.io/r/GraylinKim/sc2reader
* Hooked up travis-ci for continuous testing: https://travis-ci.org/GraylinKim/sc2reader
* Switched to built in python unittest module for testing.

Changed Stuff (non-backwards compatible!):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Summary.teams is now summary.team; summary.team is now summary.teams. To conform with replay name conventions
* Fixed #136, unit types from tracker events are used when available.
* Deprecated player.gateway for player.region
* Reorganized the person/player/observer hierarchy. Top level classes are now Computer, Participant, and Observer. Participant and Computer are both children of player so any isinstance code should still work fine.
* Player.uid now means something completely different! Use player.toon_id instead
* Player.uid is now the user id of the player (was player.cid)
* PersonDict can no longer be constructed from a player list and new players cannot be added by string (name). Only integer keys accepted for setting.
* Log a warning instead of throwing an exception when using an unknown colors.
   * An unknown hex value will use the hex value as the name.
   * An unknown color name will use 0x000000 as the color.
* Finally straighten out all these replay player list/dicts
   * human/humans -> human entities, indexed by uid
   * computer/computers -> computer entities, indexed by pid
   * player/players -> actually playing in the game, indexed by pid
   * observer/observers -> observing the game, indexed by uid
   * entities -> players + observers || humans + computers, indexed by pid
   * client/clients - (deprecated) same as human/humans
   * people/person - (deprecated) same as entity/entities


0.5.1 - June 1, 2013
--------------------

* Fixes several game event parsing issues for older replays.
* Properly maps ability ids for armory vehicle & ship armor upgrades.
* Uses the US depot for SEA battle.net depot dependencies.
* ``PlayerStatEvent.food_used`` and ``food_made`` are now properly divided by 4096
* ``AbilityEvent.flags`` are now processed into a dictionary mapping flag name to True/False (``AbilityEvent.flag``)
* Fixed error preventing UnitOwnerChangeEvents from being processed
* Fixed the toJSON plugin and adds new fields
* Fixed error preventing parsing of MapHeader (s2mh) files
* APMTracker now properly calculates average APM to the last second played by each player instead of using the number of replay minutes in the denominator.

0.5.0 - May 7, 2013
--------------------

* Support for all replays (arcade replays now parse!) from all versions
* Support for the new replay.tracker.events added in 2.0.8
   * Units now have birth frame, death frame, and owner information
   * New events for (roughly) tracking unit positions
   * New events for tracking player resource stockpiles and collection rates
   * More!
* Much more comprehensive documentation.
* New unit model
   * SiegeTank and SiegeTankSieged (and others with different forms) are no longer separate units.
   * Units that can transform maintain a full type history.
   * Units are correctly and uniquely identified by unit_id alone.
* Updated unit meta data:
   * Mineral Cost
   * Vespene Cost
   * Supply Cost
   * Flags for is_worker, is_army, is_building
* Added ability meta data:
   * is_build flag marking abilities that create units
   * build_unit indicating the unit type that is built
   * build_time indicating the build time for the ability

