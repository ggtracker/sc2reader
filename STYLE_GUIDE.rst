STYLE GUIDE
==============

Use your common sense and have some decency. Also try to stick to the following where reasonable.


Absolute Imports
----------------------

Always use absolute imports::

	from __future__ import absolute_import

That means imports should always start with sc2reader... instead of being relative to the current module.

	from sc2reader.utils import ReplayBuffer


Explicit Imports
---------------------

Prefer explicit imports to globbed imports

	from sc2reader.events import ChatEvent

is better than

	from sc2reader.events import *


Formatting Strings
-----------------------

Use string.format(args) instead string % (args).

To support python 2.6, use numerical indexes even though it is a pain in the ass::

	"{0} minerals, {1} gas, {2} terrazine, and {3} custom".format(self.minerals, self.vespene, self.terrazine, self.custom)

