CHANGELOG
============

0.5.1 - In progress
--------------------

* ``PlayerStatEvent.food_used`` and ``food_made`` are now properly divided by 4096, 3e314e81796c41f01ac116e3a115a03ffb883b3f
* ``AbilityEvent.flags`` are now processed into a dictionary mapping flag name to True/False (``AbilityEvent.flag``), a515bfa886b355a0e18497497c57eb252a4496ef
* Fixed error preventing UnitOwnerChangeEvents from being processed, ee0fc50caea5bc00dd94487791edaa8515b1cc35
* Fixed the toJSON plugin and adds new fields, 7cef03efded356f6af5e932c06241583f3f52c26
* Fixed error preventing parsing of MapHeader (s2mh) files
* APMTracker now ....

0.5.0 - May 7, 2013
--------------------

* Support for all replays (arcade replays now parse!) from all versions
* Support for the new replay.tracker.events added in 2.0.8
**Units now have birth frame, death frame, and owner information
**New events for (roughly) tracking unit positions
**New events for tracking player resource stockpiles and collection rates
**More!
* Much more comprehensive documentation.
* New unit model
** SiegeTank and SiegeTankSieged (and others with different forms) are no longer separate units.
** Units that can transform maintain a full type history.
** Units are correctly and uniquely identified by unit_id alone.
* Updated unit meta data:
** Mineral Cost
** Vespene Cost
** Supply Cost
** Flags for is_worker, is_army, is_building
* Added ability meta data:
** is_build flag marking abilities that create units
** build_unit indicating the unit type that is built
** build_time indicating the build time for the ability

0.4.0 - ???
--------------------

...

