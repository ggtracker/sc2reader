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

Now we need to use sc2reader to read that file into a :class:`Replay` object that contains all the information that we are looking for.

::

    from sc2reader import SC2Reader

    def main():
        path = sys.argv[1]
        sc2 = SC2Reader()
        replay = sc2.load_replay(path)

In the code above, we imported the :class:`SC2Reader` class from the sc2reader package. This class is a factory class that is used to load replays. This factory is configurable in a variety of ways but sane defaults are provided so that most users probably won't need to do any substantial configuration. In fact, because many users will never need to configure the SC2Reader factory the package provides a default factory that can be used by operating directly on the sc2reader package.

::

    import sc2reader

    def main():
        path = sys.argv[1]
        replay = sc2reader.load_replay(path)

We'll use this short hand method for the rest of this tutorial.

The replay object itself is a dumb data structure; there are no access methods only attributes. For our script we will need the following set of attributes, a full list of attributes can be found on the :class:`Replay` reference page.

::

    >>> replay.filename
    'test_replays/1.4.0.19679/The Boneyard (10).SC2Replay'
    >>> replay.release_string
    '1.4.0.19679'
    >>> replay.category
    'Ladder'
    >>> replay.date
    datetime.datetime(2011, 9, 20, 21, 8, 8)
    >>> replay.type
    '2v2'
    >>> replay.map
    'The Boneyard'
    >>> replay.length # string format is MM.SS
    Length(0, 1032)
    >>> replay.teams
    [<sc2reader.objects.Team object at 0x2b5e410>, <sc2reader.objects.Team object at 0x2b5e4d0>]

Many of the replay attributes are nested data structures which are generally all pretty dumb as well. The idea being that you should be able to access almost anything with a mixture of indexes and dot notation. Clean and simple accessibility is one of the primary design goals for sc2reader. 

::

    >>> replay.teams[0].players[0].color.hex
    'B4141E'
    >>> replay.player['Remedy'].url
    'http://us.battle.net/sc2/en/profile/2198663/1/Remedy/'

Each of these nested structures can be found either on its own reference page or lumped together with the other minor structures on the Misc Structures page.

So now all we need to do is build the ouput using the available replay attributes. Lets start with the header portion. We'll use a block string formatting method that makes this clean and easy:

::

    def formatReplay(replay):
        return """

    {filename}
    --------------------------------------------
    SC2 Version {release_string}
    {category} Game, {date}
    {type} on {map}
    Length: {length}

    """.format(**replay.__dict__)

In the code above we are taking advantage of the dump data structure design of the :class:`Replay` objects and unpacking its internal dictionary into the string.format method. If you aren't familiar with some of these concepts they are well worth reading up on; string templates are awesome!

Similar formatting written in a more verbose and less pythonic way:

::

    def formatReplay(replay):
        output  = replay.filename+'\n'
        output += "--------------------------------------------\n"
        output += "SC2 Version "+replay.release_string+'\n'
        output += replay.category+" Game, "+str(replay.date)+'\n'
        output += replay.type+" on "+replay.map+'\n'
        output += "Length: "+str(replay.length)
        return output

Next we need to format the teams for display. The :class:`Team` and :class:`Player` data structures are pretty straightforward as well so we can apply a bit of string formatting and produce this:
    
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
    {category} Game, {date}
    {type} on {map}
    Length: {length}

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

So our script works fine for single files, but what if you want to handle  multiple files or directories? sc2reader provides two functions for loading replays: :meth:`~SC2Reader.load_replay` and :meth:`~SC2Reader.load_replays` which return a single replay and  a list respectively. :meth:`~SC2Reader.load_replay` was used above for convenience but :meth:`~SC2Reader.load_replays` is much more versitile. Here's the difference:

* :meth:`~SC2Reader.load_replay`: accepts a file path or an opened file object.
* :meth:`~SC2Reader.load_replays`: accepts a collection of opened file objects or a path (both directory and file paths acceptable) or a collection of paths. You could even pass in a collection of mixed paths and opened file objects.

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

Remember above that the short hand notation that we have been using works with a default instance of the SC2Reader class. :class:`SC2Reader` factories can be customized either on construction or with the :meth:`~SC2Reader.configure` method.

::

    from sc2reader import SC2Reader

    sc2 = SC2Reader(
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

An ideal prettyPrinter script would let the user configure these options as arguments using the argparse library. Such an expansion is beyond the scope of sc2reader though, so we'll leave it as an exercise to the reader.