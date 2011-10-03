.. sc2reader documentation master file, created by
   sphinx-quickstart on Sun May 01 12:39:48 2011.


sc2reader Official Documentation
=====================================

Stuff in here...

Use and Configuration
=======================

Basic Use
-------------

The sc2reader package itself can be configured and used to read replay files
right out of the box! This lightweight approach to usage provides default
options for full replay parsing so no configuration is necessary for normal use.

read
~~~~~~~~

::

    >>> import sc2reader
    >>> sc2reader.read('test_replays/1.4.0.19679/36663.SC2Replay')
    [<sc2reader.objects.Replay object at 0x944822c>]

Notice that a list of Replay_ objects was returned. That is because the read
function is always plural and will return a list regardless of how many replays
it finds at the path that you send it.

It works by (optionally) recursing through the specified path (if its a directory)
and grabbing all files of the .SC2Replay file type and parsing them. Because of
this, while the path you send it must always exist it is possible for the read_
function to return an empty array of not files are found. This scanning process
if fairly configurable by several of the available Options_.

Because frequently you will be parsing only a single file or will be in an
environment where you only have access to file or file-like objects, a read_file_
function is available as well.

read_file
~~~~~~~~~~~~

::

    >>> import sc2reader
    >>> replay = sc2reader.read_file('test_replays/1.4.0.19679/36663.SC2Replay')
    >>> print "{0} on {1}, played on {2}".format(replay.type, replay.map, replay.date)
    1v1 on Xel'Naga Caverns, played on 2011-09-21 02:49:47

The read file function can accept either a path to a single file or a reference
to a file-like object. A file-like object must implement the ``seek`` and
``read`` methods to be valid. These two functions read_file_ and read_ provide
the interface for constructing replays from file objects.


configure
~~~~~~~~~~~

::

    >>> import sc2reader
    >>> sc2reader.configure(files=sc2reader.config.files.partial)
    >>> replay = sc2reader.read_file('CustomMap.SC2Replay')

The configure_ function can be used to change the default configuration of the
replay parser and processor. This can be used to effect scanning of the file
tree, the output and logging destination, and the fullness of the parsing. In
the example above, we have restricted the file set to a partial parse and
excluded the replay.game.events file from the parsing process. While sc2reader
doesn't support custom games, by restricting the fileset it can successfully
read custom games to get non-event related information including summary game
information as well as a general profile of the players.

For one off configuration jobs though, sometimes its easier to pass the options
in as keyword arguments to the read_ and read_file_ functions. This will leave
the current sc2reader options untouched and won't affect future calls.

::

    >>> import sc2reader
    >>> sc2reader.read(path, **options)
    >>> sc2reader.read_file(fileobj, **options)


Advanced Use
--------------

In addition to making the read_, read_file_, and configure_ methods available on
the module, they are also available as part of an SC2Reader class with the same
call signature. This can let you move easily between several different
configurations as needed for different tasks.

::

    >>> from sc2reader import SC2Reader
    >>> reader = SC2Reader(**options)
    >>> reader.read_file('test_replays/1.4.0.19679/36663.SC2Replay')
    <sc2reader.objects.Replay object at 0x944822c>


Options
------------------

.. attribute:: directory

    *Default: ""*

    Specifies the directory in which the files to be read reside (defaults to
    None). Does a basic `os.path.join` with the file names as passed in.

.. attribute:: processors

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

.. attribute:: debug

    pass

.. attribute:: verbose

    *Default: False*

    The verbose option can be used to get a detailed readout of the replay
    parsing progress. **Experimental option**

.. attribute:: parse_events

    pass

.. attribute:: include_regex

    pass

.. attribute:: exclude_dirs

    pass

.. attribute:: recursive

    pass

.. attribute:: depth

    pass

.. attribute:: follow_symlinks

    pass

.. attribute:: parse

    *Default: sc2reader.config.files.all*

    TODO: Fill this in

.. attribute:: apply

    pass


Structures
======================

The outline of the key structures in the replay object.

Replay
-----------

The Replay class is the container class for all the information about the
replay. Depending on the level of parsing performed, different attributes
here will have values. They will always be set.



.. attribute:: release_str

    The release of the replay. i.e. ``1.4.0.19679``

.. attribute:: build

    The build number for the replay. i.e. ``19679``. This attribute directly
    determines which data sets and parsers are used to handle the replay
    during the read process

.. attribute:: length

    An instance of the Length_ class representing the total length of the
    replay in game seconds at 16 frames per second.

.. attribute:: filename

    The path to the .SC2Replay file that this replay represents. When using
    file-like objects without support for the ``name`` attribute this
    attribute stores 'Unavailable'.

.. attribute:: opt

    An AttributeDict representing the options used to process this replay
    object.

.. attribute:: gateway

    A short lowercase code representing the gateway on which the replay was
    played. i.e. sea, us, kr, eu, xx (Public Test)

.. attribute:: map

    Map the game was played on. Currently localized to the recording player.

.. attribute:: date

    A datetime object representing the time (local to the recorder) that the
    replay was played on.

.. attribute:: utc_date

    A utc equivalent of the replay.date object.

.. attribute:: speed

    The game speed of the replay: Slower, Slow, Normal, Fast, Faster.

.. attribute:: category

    The category of game being played: Private, Public, Ladder, or Single
    (for single player vs AI games).

.. attribute:: type

    The type of game being played: FFA, 1v1, 2v2, 3v3, etc.

.. attribute:: is_ladder

    A flag shortcut for filtering out ladder replays.

.. attribute:: is_private

    A flag shortcut for filtering out private replays.

.. attribute:: players

    A list of Player_ objects representing the people actively playing (not
    those observing) the game. This can include computer players.

.. attribute:: observers

    A list of Observer_ objects representing the people watching the game
    from the sidelines.

.. attribute:: people

    A combined list of both the Player_ and Observer_ objects representing
    all the people and computers in the game.

.. attribute:: person

    A dual-key dictionary in which Player_ and Observer_ objects can be
    looked up by either name or pid.

.. attribute:: humans

    A list representing all the non-computer player people in the game, both
    players and observers included.

.. attribute:: teams

    A list of Team_ objects representing the teams in the game.

.. attribute:: team

    A dictionary of Team_ objects mapping team number to Team object.

.. attribute:: packets

    A list of Packet_ objects from the replay.message.events file.

.. attribute:: messages

    A list of Message_ objects representing all the messages sent by all the
    people in the game.

.. attribute:: recorder

    A Person_ object representing the person that recorded the game. Packets
    are currently used to determine the recording player (who won't recieve
    packets from themselves).

.. attribute:: events

    A list Event_ objects representing all the game events generated by all
    the humans in the game. Computer players do not have their actions
    recorded since they are deterministically generated by the game engine
    at run time.


Team
-------------

.. attribute:: number

    The team number. Counts up starting from 1.

.. attribute:: players

    A list of Player objects representing the players on that team.

.. attribute:: result

    Either 'Win' or 'Loss'. This is inherited by each player on the team.

Person
---------------


.. attribute:: pid

    The player id. i.e. 1, 2 3.

.. attribute:: name

    The players battle.net account name

.. attribute:: is_observer

    A flag indicating the play status of the player.

.. attribute:: type

    Either 'Human' or 'Computer'.

.. attribute:: messages

    A list of Message objects representing the messages sent by the person.

.. attribute:: events

    A list of events triggered by this person during game play. For observers
    this can include most kinds of events but not ability events as they
    cannot effect game play.

.. attribute:: recorder

    A flag indicating the person's status as recorder

.. attribute:: replay

    A pointer back to the parent replay structure.


Observer
~~~~~~~~~~~

No additional attributes


Player
~~~~~~~~~~~

.. attribute:: aps

    A dict with a key for every second of the game and a value representing
    the number of actions the player has made in that second at 16 frames
    per second.

.. attribute:: apm

    A dict with a key for every minute of the game and a value representing
    the number of actions that player has made in that minute at 16 frames
    per second.

.. attribute:: avg_apm

    The average of all the avlues in the APM dict up until the point that
    the player has died.

.. attribute:: result

    The result of the game for that player. 'Win' or 'Loss'.

.. attribute:: url

    The bnet url for this player's battle.net profile.

.. attribute:: difficulty

    For Human players this will always be Medium. For computers this is the
    chosen difficulty level.

.. attribute:: pick_race

    The race choosen at the beginning of the game. This includes Random.

.. attribute:: play_race

    The race that was actually played. This does not include random.

.. attribute:: subregion

    Battle.net gateways are split into different geographic regions. This
    number indicates which region the player falls into.

.. attribute:: handicap

    The player handicap if set. Generally 100 for normal matches.

.. attribute:: team

    A pointer to the Team object that the player is a part of.

.. attribute:: region

    The name of the region that the player is in. i.e. South East Asia.

.. attribute:: color

    An instance of the Color class representing the player's color. Contains
    components of r, g, b, and a as well as hex for a hexadecimal
    representation. str(color) will produce the color name as a string.


Message
------------------


.. attribute:: framestamp

    An integer representing the frame number at which this message was sent.

.. attribute:: sender

    A reference to the Player object that sent the message

.. attribute:: to_all

    A flag indicating if the message was sent to all

.. attribute:: to_allies

    An opposite flag as a convenience for indicating if the message was sent
    to allies.

Length
--------------------

::

    length = Length(seconds=4230)
    length.seconds  #4230
    length.hours    #1
    length.mins     #10
    length.secs     #30


.. attribute:: seconds

    The total number of seconds represented

.. attribute:: secs

    The number of seconds in excess of the minutes.

.. attribute:: mins

    The number of minutes in excess of the hours.

.. attribute:: hours

    The number of hours in represented.

Event
------------------

Events are not yet documented...


Packet
------------------

Packets are not yet documented



Indices and tables
==================

* :ref:`genindex`
