#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''sc2autosave is a utility for reorganizing and renaming Starcraft II files.

Overview
==============

sc2autosave provides a simple mechanism for renaming replay files as they are
copied or moved from a source directory to a destination directory. In between
runs the state is stored in the sc2autosave.dat file saved to the destination
folder. In this way, multiple destination folders with different organizations
and formats can be maintained independently.

General Operation
-------------------

When first run for a given destination directory, sc2autosave scans for all
files since the epoch. Each subsequent run scans only for files new files
since the previous scan time. This behavior can be modified on a run by run
basis by with the --since DATETIME option. By default the source directory
is scanned recursively. The --depth DEPTH option can limit and/or eliminate
this is recursion.

Files identified as new are then copied to the destination directory. The
--move option can override this behavior. The default behavior is a good idea
because it ensures that there is a backup copy and allows for several different
file structures to be constructed with different sc2autosave configurations for
easy replay navigation. You might keep your replay files redundantly stored
sorted by format, by map, and by matchup for easy lookup later on.

While normally run as a batch process, the --period SECONDS option can be used
to run sc2autosave as a background process, scanning the directory for changes
every SECONDS seconds. This is useful for creating background processes on
operating system start up.

Renaming Replays
--------------------

The --rename option allows you to specify a renaming format string. The string
is constructed the pythonic (3.0) way with {:field} indicating the substition
of a field. The forward slash (/) is a special character here which terminates
a folder name and allows for organization into subdirectories. All other string
characters form the template into which the fields are inserted.

Fields related to dates and times (:date, :datetime, :length fields) can be
formatted through their respective directives (--date, --datetime, --length)
according to python date formatting conventions. Additionally, the player
display format can be refined with the --player-format FORMAT directive which
is interpreted similarly to the --rename FORMAT directive detailed above.

Once content has been defined to your tastes you may wish to get specific about
the ordering of the teams and players on those teams in the replay name. The
--team-order-by and --player-order-by directives can be used for this purpose.
A common preference is to favor specific players (like yourself and friends)
and their teams in the ordering by placing them first in the listing. The
--favor PLAYER1 [PLAYER2] directive supports this preference.

Filtering Replays
---------------------

Once a replay has been scanned and parsed you have an opportunity to filter it
for inclusion in the destination directory. This is useful when constructing
various different types of replay packs for distribution and review. Replays
are small and Battle.net has a terrible filesystem based replay locator; why
not make your life easier with a little duplication.

--filter-players PLAYER [PLAYER ...]
--filter-matchup MATCHUP [MATCHUP ...]
--filter-map NAME [NAME ...]
--filter-length LOW HIGH
--filter-date START END

Example Configurations
------------------------

This first basic configuration sets up a background process to copy new replays
without renaming to a 'Saved' subdirectory every 10 seconds. The depth 0 option
keeps the script from looking into the 'Saved' subdirectory.

    sc2autosave                                                             \
        --source ~/My\ Documents/Starcraft\ II/Accounts/.../Mutliplayer     \
        --dest ~/My\ Documents/Starcraft\ II/Accounts/.../Multiplater/Saved \
        --period 10                                                         \
        --depth 0

This next configuration runs in batch mode using the default renaming format.

    sc2autosave                                                             \
        --source ~/My\ Documents/Starcraft\ II/Accounts/.../Mutliplayer     \
        --dest ~/My\ Documents/Starcraft\ II/Accounts/.../Multiplater/Saved \
        --rename

    (ZvP) Lost Temple: ShadesofGray(Z) vs Trisfall(P).SC2Replay
    (ZZvPP) Shattered Temple: ShadesofGray(Z), Remedy(Z) vs ProfProbe(P), Trisfall(P).SC2Replay

Here is a heavily customized format that organizes replays into subdirectories
by replay format and favors ShadesofGray in the player and team orderings.

    sc2autosave                                                             \
        --source ~/My\ Documents/Starcraft\ II/Accounts/.../Mutliplayer     \
        --dest ~/My\ Documents/Starcraft\ II/Accounts/.../Multiplater/Saved \
        --rename "{:format}/{:matchup} on {:map}: {:teams}"                 \
        --player-format "{:name}({:play_race})"                             \
        --team-order-by number                                              \
        --player-order-by name                                              \
        --favored ShadesofGray

    1v1/ZvP on Lost Temple: ShadesofGray(Z) vs Trisfall(P).SC2Replay
    2v2/ZZvPP on Shattered Temple: ShadesofGray(Z), Remedy(Z) vs ProfProbe(P), Trisfall(P).SC2Replay

Next is another customized format which organizes replays by matchup. It uses
strict player and team ordering by number with no exceptions and formats game
length to show both minutes and seconds.

    sc2autosave                                                             \
        --source ~/My\ Documents/Starcraft\ II/Accounts/.../Mutliplayer     \
        --dest ~/My\ Documents/Starcraft\ II/Accounts/.../Multiplater/Saved \
        --rename "{:matchup}/({:length}) {:map}: {:teams}"                  \
        --player-format "{:name}({:play_race})"                             \
        --team-order-by number                                              \
        --player-order-by number                                            \
        --length "%M:%S"

    PvZ/(20:14) Lost Temple: Trisfall(P) vs ShadesofGray(Z).SC2Replay
    ZZvPP/(35:40) Shattered Temple: Remedy(Z), ShadesofGray(Z) vs Trisfall(P), ProfProbe(P).SC2Replay

Complete Reference Guide
---------------------------

    --source SOURCE_FOLDER
        The source folder to scan for replays. Uses recursive scan by default.
    --dest DESTINATION_FOLDER
        The destination folder to place replays into.
    --depth DEPTH
        Allows recursion to be limited and/or disabled (with DEPTH=0).
    --period SECONDS
        Puts sc2autosave into continuous mode, scanning the directory for new
        files every SECONDS seconds.
    --rename FORMAT
        :map - Inserts the map name.
        :date - Inserts a string formated datetime object using --date-format.
        :length - Inserts a string formatted time object using --length-format.
        :teams - Inserts a comma separated player list. Teams are separated
            with a ' vs ' string. Format the player with --player-format.
        :format - Inserts the map format (1v1, 2v2, 3v3, etc)
        :matchup - Inserts the matchup (ZvZ, PTvTZ, etc). The matchup is
            in team order with races ordered alphabetically; not by player!
            This makes matchups more consistent and useful for sorting.

    --length-format FORMAT
    --player-format FORMAT
    --date-format   FORMAT

    --team-order-by   FIELD
    --player-order-by FIELD
    --favored NAME [NAME,...]


POST-Parse filtering vs preparse filtering?
POST-Parse, how to do it?!?!?!?!
'''
import argparse
import cPickle
import os
import shutil
import sys
import time

import sc2reader


def run(args):
    #Reset wipes the destination clean so we can start over.
    if args.reset:
        reset(args)

    #Set up validates the destination and source directories.
    #It also loads the previous state or creates one as necessary.
    state = setup(args)

    #We break out of this loop in batch mode and on KeyboardInterrupt
    while True:

        #The file scan uses the arguments and the state to filter down to
        #only new (since the last sync time) files.
        for path in scan(args, state):
            try:
                #Read the file and expose useful aspects for renaming/filtering
                replay = sc2reader.load_replay(path, load_level=2)
            except KeyboardInterrupt:
                raise
            except:
                #Failure to parse
                file_name = os.path.basename(path)
                directory = make_directory(args, ('parse_error',))
                new_path = os.path.join(directory, file_name)
                source_path = path[len(args.source):]
                args.log.write("Error parsing replay: {0}".format(source_path))
                if not args.dryrun:
                    args.action.run(path, new_path)

                #Skip to the next replay
                continue

            aspects = generate_aspects(args, replay)

            #Use the filter args to select files based on replay attributes
            if filter_out_replay(args, replay):
                continue

            #Apply the aspects to the rename formatting.
            #'/' is a special character for creation of subdirectories.
            #TODO: Handle duplicate replay names, its possible..
            path_parts = args.rename.format(**aspects).split('/')
            filename = path_parts.pop()+'.SC2Replay'

            #Construct the directory and file paths; create needed directories
            directory = make_directory(args, path_parts)
            new_path = os.path.join(directory, filename)

            #Find the source relative to the source directory for reporting
            dest_path = new_path[len(args.dest):]
            source_path = path[len(args.source):]

            #Log the action and run it if we are live
            msg = "{0}:\n\tSource: {1}\n\tDest: {2}\n"
            args.log.write(msg.format(args.action.type, source_path, dest_path))
            if not args.dryrun:
                args.action.run(path, new_path)

        #After every batch completes, save the state and flush the log
        #TODO: modify the state to include a list of remaining files
        args.log.flush()
        save_state(state, args)

        #We only run once in batch mode!
        if args.mode == 'BATCH':
            break

        #Since new replays come in fairly infrequently, reduce system load
        #by sleeping for an acceptable response time before the next scan.
        time.sleep(args.period)

    args.log.write('Batch Completed')


def filter_out_replay(args, replay):
    player_names = set([player.name for player in replay.players])
    filter_out_player = not set(args.filter_player) & player_names

    if args.filter_rule == 'ALLOW':
        return filter_out_player
    else:
        return not filter_out_player


# We need to create these compare functions at runtime because the ordering
# hinges on the --favored PLAYER options passed in from the command line.
def create_compare_funcs(args):
    favored_set = set(name.lower() for name in args.favored)

    def player_compare(player1, player2):
        # Normalize the player names and generate our key metrics
        player1_name = player1.name.lower()
        player2_name = player2.name.lower()
        player1_favored = (player1_name in favored_set)
        player2_favored = (player2_name in favored_set)

        # The favored player always comes first in the ordering
        if player1_favored and not player2_favored:
            return -1
        elif player2_favored and not player1_favored:
            return 1

        # The most favored person will always be listed first
        elif player1_favored and player2_favored:
            player1_index = args.favored.index(player1_name)
            player2_index = args.favored.index(player2_name)
            return player1_index - player2_index

        # If neither is favored, we'll order by number for now
        # TODO: Allow command line specification of other orderings (maybe?)
        else:
            return player1.pid-player2.pid

    def team_compare(team1, team2):
        # Normalize the team name lists and generate our key metrics
        team1_names = set(p.name.lower() for p in team1.players)
        team2_names = set(p.name.lower() for p in team2.players)
        team1_favored = team1_names & favored_set
        team2_favored = team2_names & favored_set

        # The team with the favored players will always be listed first
        if team1_favored and not team2_favored:
            return -1
        elif team2_favored and not team1_favored:
            return 1

        # The team with the most favored person will always come first
        elif team1_favored and team2_favored:
            team1_best = sorted(args.favored.index(n) for n in team1_favored)
            team2_best = sorted(args.favored.index(n) for n in team2_favored)
            return team1_best[-1] - team2_best[-1]

        # If neither is favored, we'll order by number for now
        # TODO: Allow command line specification of other orderings (maybe?)
        else:
            return team1.number-team2.number

    return team_compare, player_compare


def generate_aspects(args, replay):
    teams = sorted(replay.teams, args.team_compare)
    matchups, team_strings = list(), list()
    for team in teams:
        team.players = sorted(team.players, args.player_compare)
        composition = sorted(p.play_race[0].upper() for p in team.players)
        matchups.append(''.join(composition))
        string = ', '.join(p.format(args.player_format) for p in team.players)
        team_strings.append(string)

    return sc2reader.utils.AttributeDict(
        result=teams[0].result,
        length=replay.length,
        map=replay.map,
        type=replay.type,
        date=replay.date.strftime(args.date_format),
        matchup='v'.join(matchups),
        teams=' vs '.join(team_strings)
    )


def make_directory(args, path_parts):
    directory = args.dest
    for part in path_parts:
        directory = os.path.join(directory, part)
        if not os.path.exists(directory):
            args.log.write('Creating subfolder: {0}\n'.format(directory))
            if not args.dryrun:
                os.mkdir(directory)
        elif not os.path.isdir(directory):
            exit('Cannot create subfolder. Path is occupied: {0}', directory)

    return directory


def scan(args, state):
    args.log.write("SCANNING: {0}\n".format(args.source))
    files = sc2reader.utils.get_files(
        path=args.source,
        regex=args.exclude_files,
        allow=False,
        exclude=args.exclude_dirs,
        depth=args.depth,
        followlinks=args.follow_links)
    return filter(lambda f: os.path.getctime(f) > state.last_sync, files)


def exit(msg, *args, **kwargs):
    sys.exit(msg.format(*args, **kwargs)+"\n\nScript Aborted.")


def reset(args):
    if not os.path.exists(args.dest):
        exit("Cannot reset, destination does not exist: {0}", args.dest)
    elif not os.path.isdir(args.dest):
        exit("Cannot reset, destination must be directory: {0}", args.dest)

    print 'About to reset directory: {0}\nAll files and subdirectories will be removed.'.format(args.dest)
    choice = raw_input('Proceed anyway? (y/n) ')
    if choice.lower() == 'y':
        args.log.write('Removing old directory: {0}\n'.format(args.dest))
        if not args.dryrun:
            print args.dest
            shutil.rmtree(args.dest)
    else:
        sys.exit("Script Aborted")


def setup(args):
    args.team_compare, args.player_compare = create_compare_funcs(args)
    args.action = sc2reader.utils.AttributeDict(type=args.action, run=shutil.copy if args.action == 'COPY' else shutil.move)
    if not os.path.exists(args.source):
        msg = 'Source does not exist: {0}.\n\nScript Aborted.'
        sys.exit(msg.format(args.source))
    elif not os.path.isdir(args.source):
        msg = 'Source is not a directory: {0}.\n\nScript Aborted.'
        sys.exit(msg.format(args.source))

    if not os.path.exists(args.dest):
        if not args.dryrun:
            os.mkdir(args.dest)
        else:
            args.log.write('Creating destination: {0}\n'.format(args.dest))
    elif not os.path.isdir(args.dest):
        sys.exit('Destination must be a directory.\n\nScript Aborted')

    data_file = os.path.join(args.dest, 'sc2autosave.dat')

    args.log.write('Loading state from file: {0}\n'.format(data_file))
    if os.path.isfile(data_file) and not args.reset:
        with open(data_file) as file:
            return cPickle.load(file)
    else:
        return sc2reader.utils.AttributeDict(last_sync=0)


def save_state(state, args):
    state.last_sync = time.time()
    data_file = os.path.join(args.dest, 'sc2autosave.dat')
    if not args.dryrun:
        with open(data_file, 'w') as file:
            cPickle.dump(state, file)
    else:
        args.log.write('Writing state to file: {0}\n'.format(data_file))


def main():
    parser = argparse.ArgumentParser(
        description='Automatically copy new replays to directory',
        fromfile_prefix_chars='@',
        formatter_class=sc2reader.scripts.utils.Formatter.new(max_help_position=35),
        epilog="And that's all folks")

    required = parser.add_argument_group('Required Arguments')
    required.add_argument('source', type=str,
        help='The source directory to poll')
    required.add_argument('dest', type=str,
        help='The destination directory to copy to')

    general = parser.add_argument_group('General Options')
    general.add_argument('--mode', dest='mode',
        type=str, choices=['BATCH', 'CYCLE'], default='BATCH',
        help='The operating mode for the organizer')

    general.add_argument('--action', dest='action',
        choices=['COPY', 'MOVE'], default="COPY", type=str,
        help='Have the organizer move your files instead of copying')
    general.add_argument('--period',
        dest='period', type=int, default=0,
        help='The period of time to wait between scans.')
    general.add_argument('--log', dest='log', metavar='LOGFILE',
        type=argparse.FileType('w'), default=sys.stdout,
        help='Destination file for log information')
    general.add_argument('--dryrun',
        dest='dryrun', action="store_true",
        help="Don't do anything. Only simulate the output")
    general.add_argument('--reset',
        dest='reset', action='store_true', default=False,
        help='Wipe the destination directory clean and start over.')

    fileargs = parser.add_argument_group('File Options')
    fileargs.add_argument('--depth',
        dest='depth', type=int, default=-1,
        help='Maximum recussion depth. -1 (default) is unlimited.')
    fileargs.add_argument('--exclude-dirs', dest='exclude_dirs',
        type=str, metavar='NAME', nargs='+', default=[],
        help='A list of directory names to exclude during recursion')
    fileargs.add_argument('--exclude-files', dest='exclude_files',
        type=str, metavar='REGEX', default="",
        help='An expression to match excluded files')
    fileargs.add_argument('--follow-links',
        dest='follow_links', action="store_true", default=False,
        help="Enable following of symbolic links while scanning")

    renaming = parser.add_argument_group('Renaming Options')
    renaming.add_argument('--rename',
        dest='rename', type=str, metavar='FORMAT', nargs='?',
        default="{length} {type} on {map}",
        help='''\
            The renaming format string. can have the following values:

                * {length} - The length of the replay ([H:]MM:SS)
                * {type} - The type of the replay (1v1,2v2,4v4,etc)
                * {map} - The map that was played on.
                * {match} - Race matchup in team order, alphabetically by race.
                * {date} - The date the replay was played on
                * {teams} - The player line up
        ''')

    renaming.add_argument('--length-format',
        dest='length_format', type=str, metavar='FORMAT', default='%M.%S',
        help='The length format string. See the python time module for details')
    renaming.add_argument('--player-format',
        dest='player_format', type=str, metavar='FORMAT', default='{name} ({play_race})',
        help='The player format string used to render the :teams content item.')
    renaming.add_argument('--date-format',
        dest='date_format', type=str, metavar='FORMAT', default='%m-%d-%Y',
        help='The date format string used to render the :date content item.')
    '''
    renaming.add_argument('--team-order-by',
        dest='team_order', type=str, metavar='FIELD', default='NUMBER',
        help='The field by which teams are ordered.')
    renaming.add_argument('--player-order-by',
        dest='player_order', type=str, metavar='FIELD', default='NAME',
        help='The field by which players are ordered on teams.')
    '''
    renaming.add_argument('--favored', dest='favored',
        type=str, default=[], metavar='NAME', nargs='+',
        help='A list of the players to favor in ordering teams and players')

    filterargs = parser.add_argument_group('Filtering Options')
    filterargs.add_argument('--filter-rule', dest='filter_rule',
        choices=["ALLOW","DENY"],
        help="The filters can either be used as a white list or a black list")
    filterargs.add_argument('--filter-player', metavar='NAME',
        dest='filter_player', nargs='+', type=str, default=[],
        help="A list of players to filter on")

    try:
        run(parser.parse_args())
    except KeyboardInterrupt:
        print "\n\nScript Interupted. Process Aborting"

if __name__ == '__main__':
    main()
