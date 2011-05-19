.. default-domain:: py

sc2reader
==================

Basic Usage
-------------

The sc2reader package itself can be configured and used to read replay files
right out of the box! This lightweight approach to usage provides default
options for full replay parsing so no configuration is necessary for normal use.

The ``configure`` function can be used to change this default configuration for
all future package reads. The options, where supplied, will overwrite the 
default values. The ``read`` function takes a location, either file or
directory, and returns a single replay or a list of replays respectively.

::

    import sc2reader
    
    sc2reader.configure(**options)
    replay = sc2reader.read(file)

Alternatively, you can also pass options directly to the read function. This
causes sc2reader to do a one off read with the given options, leaving the
defaults unchanged.

::

    import sc2reader
    
    sc2reader.read(file,**options)

If you prefer a class based approach or want to have several different
configurations on hand try the above approach. Just initialize the SC2Reader
with the desired options (sane defaults provided) and use it just like you
would the package! To better reflect the structure of the source code, the rest
of the documentation will use this class based approach.

::

    from sc2reader import SC2Reader
    
    #sane defaults provided
    reader = SC2Reader(**options)
    replay = reader.read(file)

These three top level interfaces should remain fairly stable in the near to mid
future.


Options
-----------

SC2Reader behavior can be configured with a number of options which can either
be specified individually by keyword argument or packaged into a dictionary.

::

    import sc2reader
    from sc2reader import SC2Reader, PARTIAL
    
    #Its often cleaner to package the options into a dict first
    options = dict(
            processors=[ExamplePostProcessor],
            parse=PARTIAL,
            directory='C:\Users\Me\Documents...',
        )
        
    #The various different configuration methods
    reader = SC2Reader(processors=[PostProcessor],parse=PARTIAL)
    sc2reader.read(location,**options)
    sc2reader.configure(**options)

Options currently available are described below:

.. option:: processors

    *Default: []*
    
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
    
    *Default: ""*
    
    Specifies the directory in which the files to be read reside (defaults to
    None). Does a basic `os.path.join` with the file names as passed in.
    
.. option:: parse

    *Default: FULL*
    
    Three parse levels are provided for general convenience:
    
    *   ``FULL`` parse will parse through all available files and produce the
        most comprehensive replay object. 
    *   ``PARTIAL`` parse will skip the game events file, resulting in loss of
        detailed game information but with significant time savings.
    *   ``CUSTOM`` parse allows a user with intimate knowledge of sc2reader to
        hand build their own parse style.
    
.. option:: verbose

    *Default: False*
    
    The verbose option can be used to get a detailed readout of the replay
    parsing progress. **Experimental Option**
