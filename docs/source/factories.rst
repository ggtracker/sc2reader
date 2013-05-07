.. currentmodule:: sc2reader.factories

Factories
==============

Factories are used to load SCII resources from file-like objects and paths to file-like objects. Objects must implement ``read()`` such that it retrieves all the file contents.


SC2Factory
--------------------------

.. autoclass:: SC2Factory
	:members:


DictCachedSC2Factory
--------------------------

.. autoclass:: DictCachedSC2Factory
	:members:

FileCachedSC2Factory
--------------------------

.. autoclass:: FileCachedSC2Factory
	:members:

DoubleCachedSC2Factory
--------------------------

.. autoclass:: DoubleCachedSC2Factory
	:members: