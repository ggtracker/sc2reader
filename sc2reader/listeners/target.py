from __future__ import absolute_import

from sc2reader import utils
from sc2reader.events import TargetAbilityEvent
from sc2reader.listeners.utils import ListenerBase


class TargetListener(ListenerBase):

	def accepts(self, event):
		return isinstance(event, TargetAbilityEvent) #and event.ability in (0x3700, 0x5700)

	def __call__(self, event, replay):
		if replay.opt.debug:
			print event.bytes.encode('hex')

		ability = event.ability
		if ability is not None and ability in replay.datapack.abilities:
			ability = replay.datapack.ability(event.ability)

		print "[{0}] {1} used ability {2} on {3}".format(utils.Length(seconds=event.second),event.player.name, ability, event.target)
