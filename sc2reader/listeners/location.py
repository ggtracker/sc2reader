from __future__ import absolute_import

from sc2reader import utils
from sc2reader.events import LocationAbilityEvent
from sc2reader.listeners.utils import ListenerBase


class LocationListener(ListenerBase):

	def accepts(self, event):
		return isinstance(event, LocationAbilityEvent) and event.ability!=0x3601 # and event.ability # and event.ability != 0x3601

	def __call__(self, event, replay):
		if replay.opt.debug:
			print event.bytes.encode('hex')

		ability = event.ability
		if ability is not None and ability in replay.datapack.abilities:
			ability = replay.datapack.ability(event.ability)

		print "[{0}] {1} used ability {2} at location: {3}, {4}".format(utils.Length(seconds=event.second),event.player.name, ability, event.location[0], event.location[1])
