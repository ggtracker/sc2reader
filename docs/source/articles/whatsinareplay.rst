
What is in a Replay?
=======================

A SC2Replay file is an archive, just like a like zip or tar file. Inside there are several files, each with a specific purpose. The important ones can be split into three categories.


Initial State:
----------------

These first three files describe the initial state of the game before any events occur.

* replay.initData - Records game client information and lobby slot data.
* replay.details - Records basic player and game data.
* replay.attributes.events - Records assorted player and game attributes from the lobby.

The Starcraft II game client can be thought of as a deterministic state machine. Given an initial state and a list of events, the end state can be exactly replicated.


Input Events:
----------------

The next two files provide a feed of player actions in the game.

* replay.message.events - Records chat messages and pings.
* replay.game.events - Records every action of every person in the game.

When you watch a replay the game just reads from these feeds. When you take over from a replay, the game client cuts the feeds and switches over to live mouse/keyboard input. Because the AI is deterministic the replay never contains message/game events for them.


Output Events:
----------------

The last file provides a record of important events from the game.

* replay.tracker.events - Records important game events and game state updates.

This file was introduced in 2.0.4 and is unncessary for the Starcraft II to reproduce the game. Instead, it records interesting game events and game state for community developers to use when analyzing replays.


What isn't in a replay?
--------------------------

Replays are specifically designed to only include data essential to recreate the game. Game state is not recorded because the game engine can recreate it based off the other information. That means no player resource counts, colleciton rates, supply values, vision, unit positions, unit deaths, etc. Information that you are super interested in probably is not directly recorded. Fortunately since 2.0.4 tracker events now record some of this information; prior to that patch we had to run our own simulations to guess at most of the data.


The other important aspect of this is that instead of completely describing all of the game data (unit data, ability data, map info, etc), replays maintain a list of dependencies. These dependencies might look like this:

* Core.SC2Mod
* Liberty (multi).SC2Mod
* Swarm (multi).SC2Mod
* Teams2.SC2Mod
* Current Patch.SC2mod
* GameHeart.SC2Mod
* Map.SC2Map

As part of the replay pre-load process, each of these dependencies is fetched and all of their associated data is loaded into memory. When Battle.net tells you it is "Fetching Files", it can often be referring to dependencies like this.

sc2reader has attempted to mitigate this serious deficiency by packaging its own game data files. Basic cost, build time, and race information has been packaged. For many people this will be enough. Future versions of sc2reader will provide support for game data exports from the World Editor (introduced in patch 2.0.10). These exports should provide a much more robust dataset to work with.
