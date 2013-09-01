.. currentmodule:: sc2reader

PrettyPrinter by Example
===========================

To walk through the sc2reader's basic interfaces we're going to step through the process of writing a pretty printer that will work like this:

::

    $ python prettyPrinter.py "test_replays/1.4.0.19679/The Boneyard (10).SC2Replay"

    test_replays/1.4.0.19679/The Boneyard (10).SC2Replay
    --------------------------------------------
    SC2 Version 1.4.0.19679
    Ladder Game, 2011-09-20 21:08:08
    2v2 on The Boneyard
    Length:17.12

    Team 1  (Z) Remedy
            (Z) ShadesofGray

    Team 2  (P) KingTroy
            (R) Jamir


Getting Started
---------------------

The first step is to get a script up to accept a path from the command line.

::

    import sys

    def main():
        path = sys.argv[1]

    if __name__ == '__main__':
        main()

Now we need to use sc2reader to read that file into a :class:`~sc2reader.resources.Replay` object that contains all the information that we are looking for.

::

    from sc2reader.factories import SC2Factory

    def main():
        path = sys.argv[1]
        sc2 = SC2Factory()
        replay = sc2.load_replay(path)

In the code above, we imported the :class:`~sc2reader.factories.SC2Factory` class from the ``sc2reader.factories`` package. This class is a factory class that is used to load replays. This factory is configurable in a variety of ways but sane defaults are provided so that most users probably won't need to do any substantial configuration. In fact, because many users will never need to configure the SC2Factory the package provides a default factory that can be used by operating directly on the sc2reader package.

::

    import sc2reader

    def main():
        path = sys.argv[1]
        replay = sc2reader.load_replay(path)

We'll use this short hand method for the rest of this tutorial.

The replay object itself is a dumb data structure; there are no access methods only attributes. For our script we will need the following set of attributes, a full list of attributes can be found on the :class:`~sc2reader.resources.Replay` reference page.

::

    >>> replay.filename
    'test_replays/1.4.0.19679/The Boneyard (10).SC2Replay'
    >>> replay.release_string
    '1.4.0.19679'
    >>> replay.category
    'Ladder'
    >>> replay.end_time
    datetime.datetime(2011, 9, 20, 21, 8, 8)
    >>> replay.type
    '2v2'
    >>> replay.map_name
    'The Boneyard'
    >>> replay.game_length # string format is MM.SS
    Length(0, 1032)
    >>> replay.teams
    [<sc2reader.objects.Team object at 0x2b5e410>, <sc2reader.objects.Team object at 0x2b5e4d0>]

Many of the replay attributes are nested data structures which are generally all pretty dumb as well. The idea being that you should be able to access almost anything with a mixture of indexes and dot notation. Clean and simple accessibility is one of the primary design goals for sc2reader.

::

    >>> replay.teams[0].players[0].color.hex
    'B4141E'
    >>> replay.player.name('Remedy').url
    'http://us.battle.net/sc2/en/profile/2198663/1/Remedy/'

Each of these nested structures can be found either on its own reference page or lumped together with the other minor structures on the Misc Structures page.

So now all we need to do is build the ouput using the available replay attributes. Lets start with the header portion. We'll use a block string formatting method that makes this clean and easy:

::

    def formatReplay(replay):
        return """

    {filename}
    --------------------------------------------
    SC2 Version {release_string}
    {category} Game, {start_time}
    {type} on {map_name}
    Length: {game_length}

    """.format(**replay.__dict__)

In the code above we are taking advantage of the dump data structure design of the :class:`~sc2reader.resources.Replay` objects and unpacking its internal dictionary into the ``string.format`` method. If you aren't familiar with some of these concepts they are well worth reading up on; string templates are awesome!

Similar formatting written in a more verbose and less pythonic way:

::

    def formatReplay(replay):
        output  = replay.filename+'\n'
        output += "--------------------------------------------\n"
        output += "SC2 Version "+replay.release_string+'\n'
        output += replay.category+" Game, "+str(replay.start_time)+'\n'
        output += replay.type+" on "+replay.map_name+'\n'
        output += "Length: "+str(replay.game_length)
        return output

Next we need to format the teams for display. The :class:`~sc2reader.objects.Team` and :class:`~sc2reader.objects.Player` data structures are pretty straightforward as well so we can apply a bit of string formatting and produce this:

::

    def formatTeams(replay):
        teams = list()
        for team in replay.teams:
            players = list()
            for player in team:
                players.append("({0}) {1}".format(player.pick_race[0], player.name))
            formattedPlayers = '\n         '.join(players)
            teams.append("Team {0}:  {1}".format(team.number, formattedPlayers))
        return '\n\n'.join(teams)


So lets put it all together into the final script, ``prettyPrinter.py``:

::

    import sys

    import sc2reader

    def formatTeams(replay):
        teams = list()
        for team in replay.teams:
            players = list()
            for player in team:
                players.append("({0}) {1}".format(player.pick_race[0], player.name))
            formattedPlayers = '\n         '.join(players)
            teams.append("Team {0}:  {1}".format(team.number, formattedPlayers))
        return '\n\n'.join(teams)

    def formatReplay(replay):
        return """
    {filename}
    --------------------------------------------
    SC2 Version {release_string}
    {category} Game, {start_time}
    {type} on {map_name}
    Length: {game_length}

    {formattedTeams}
    """.format(formattedTeams=formatTeams(replay), **replay.__dict__)


    def main():
        path = sys.argv[1]
        replay = sc2reader.load_replay(path)
        print formatReplay(replay)

    if __name__ == '__main__':
        main()


Making Improvements
---------------------------

So our script works fine for single files, but what if you want to handle  multiple files or directories? sc2reader provides two functions for loading replays: :meth:`~sc2reader.factories.SC2Factory.load_replay` and :meth:`~sc2reader.factories.SC2Factory.load_replays` which return a single replay and  a list respectively. :meth:`~sc2reader.factories.SC2Factory.load_replay` was used above for convenience but :meth:`~sc2reader.factories.SC2Factory.load_replays` is much more versitile. Here's the difference:

* :meth:`~sc2reader.factories.SC2Factory.load_replay`: accepts a file path or an opened file object.
* :meth:`~sc2reader.factories.SC2Factory.load_replays`: accepts a collection of opened file objects or file paths. Can also accept a single path to a directory; files will be pulled from the directory using :func:`~sc2reader.utils.get_files` and the given options.

With this in mind, lets make a slight change to our main function to support any number of paths to any combination of files and directories:

::

    def main():
        paths = sys.argv[1:]
        for replay in sc2reader.load_replays(paths):
            print formatReplay(replay)

Any time that you start dealing with directories or collections of files you run into dangers with recursion and annoyances of tedium. sc2reader provides options to mitigate these concerns.

* directory: Default ''. The directory string when supplied, becomes the base of all the file paths sent into sc2reader and can save you the hassle of fully qualifying your file paths each time.
* depth: Default -1. When handling directory inputs, sc2reader searches the directory recursively until all .SC2Replay files have been loaded. By setting the maxium depth value this behavior can be mitigated.
* exclude: Default []. When recursing directories you can choose to exclude  directories from the file search by directory name (not full path).
* followlinks: Default false. When recursing directories, enables or disables the follow symlinks behavior.

Remember above that the short hand notation that we have been using works with a default instance of the SC2Factory class. :class:`sc2reader.factories.SC2Factory` objects can be customized either on construction or with the :meth:`~sc2reader.factories.SC2Factory.configure` method.

::

    from sc2reader.factories import SC2Factory

    sc2 = SC2Factory(
        directory='~/Documents/Starcraft II/Multiplayer/Replays',
        exclude=['Customs','Pros'],
        followlinks=True
    )

    sc2.configure(depth=1)

Recognizing that most users will only ever need one active configuration at a time, the default factory the package makes available is configurable as well.

::

    import sc2reader

    sc2reader.configure(
        directory='~/Documents/Starcraft II/Multiplayer/Replays',
        exclude=['Customs','Pros'],
        depth=1,
        followlinks=True
    )

Many of your replay files might be custom games for which events cannot be parsed. Since the pretty printer doesn't use game event information in its output we can limit the parse level of the replay to stop after loading the basic details. This will make the pretty printer work for custom games as well.

::

    import sc2reader

    sc2reader.load_replay(path, load_level=1)

There are 4 available load levels:

* 0: Parses the replay header for version, build, and length information
* 1: Also parses the replay.details, replay.attribute.events and replay.initData files for game settings, map, and time information
* 2: Also parses the replay.message.events file and constructs game teams and players.
* 3: Also parses the replay.tracker.events file
* 4: Also parses the replay.game.events file for player action events.

So that's it! An ideal prettyPrinter script might let the user configure these options as arguments using the ``argparse`` library. Such an expansion is beyond the scope of sc2reader though, so we'll leave it that one to you.
