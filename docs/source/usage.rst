.. default-domain:: py

sc2reader
==================

Use Patterns
---------------

There are two primary usage patterns for sc2reader as illustrated below::

    import sc2reader
    
    #method 1
    replay = sc2reader.read(file,options)
    
    #method 2
    reader = sc2reader.config(options)
    replay = reader.read(file)

Each time read is called on the sc2reader package, the options are used to
configure the parsing and processors. For application where this repeated
configuration is either too slow or harmful, ``config`` will pass back a
pre-configured reader which can give a performance improvement.

The replay object passed back contains all the game information in a densely
linked object hierarchy described more fully in the :doc:`objects <objects>` page.

Options
-----------

sc2reader behavior can be configured with a number of options which can either
be specified individually by keyword argument or packaged into a dictionary::

    options = dict(
            'processors': [PostProcessor],
            'parse': sc2reader.FULL,
            'debug':True,
        )
    
    sc2reader.config(processors=[PostProcessor],parse=sc2reader.FULL)
    sc2reader.config(options=options)
    sc2reader.config(**options)
    
Options currently available are described below:

.. option:: processors

    Specifies a list of processors to apply to the replay object after it is
    constructed but before it is returned::
        
        ...
        for processor in processors:
            replay = processor(replay)
        return replay
        
    Its primary purpose is to allow developers to push post processing back
    into the sc2reader module. It can also be used as a final gateway for
    transforming the replay datastructure into something more useful for your
    purposes. Eventually sc2reader will come with a small contrib module with
    useful post-processing tasks out of the box.
    
.. option:: directory
    
    Specifies the directory in which the files to be read reside (defaults to
    None). Does a basic `os.path.join` with the file names as passed in.
    
.. option:: debug

    Turns on debugging features of sc2reader. See :doc:`debug`.
    
    