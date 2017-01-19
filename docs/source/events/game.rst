.. currentmodule:: sc2reader.events.game

Game Events
=============

Game events are what the Starcraft II engine uses to reconstruct games for you to watch
and take over in. Because the game is deterministic, only event data directly created by
a player action is recorded. These player actions are then replayed automatically when
watching a replay. Because the AI is 100% deterministic no events are ever recorded for a
computer player.

.. automodule:: sc2reader.events.game
	:members:
