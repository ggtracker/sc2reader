""" Game Event Parsing Debugger

    Recursively searches for unique replays specified by command line argument
    and attempts a parse in order to catch the ReadError. The ReadError will
    contain all the context information we need to inspect the error.

    Outputs the following information in the following format:

        ggtracker/ggtracker_replay_202597.SC2Replay
          ....... 00:04 P2 AbilityEvent        - 00 22 0b 01 08 34 07 00 31 00 00 01 1f 0d 21 f8 00 8c c0 80 00 05 ff 00
          ....... 00:05 P1 SelectionEvent      - 38 21 ac 00 06 00 01 05 15 01 03 03 05 18 00 01 05 20 00 01 05 28 00 01
          0x000F5 00:05 P2 SelectionEvent      - 00 22 ac 00 02 f4 00 00  | 00 0c a1 89 00 10 00 00 00 21 0b 01 00 01 5c 01 00 0c 22 0b
                                                 01 08 34 07 00 23 80 00 01 1f 0d 41 18 00 8a c0 80 00 05 ff 00 08 21 ac 00 02 11 01 02

    The first line is the full path to the file followed by an indented list
    of the last 2 events to be parsed with their associated bytes.

    The 3rd line for the event the parser failed on is in the following format:

        cursor event_type - event_bytes | following bytes
                            and the next bytes after that

    With a pipe character delimiting where the parser ended the event.

    The general workflow is something like this:

        1) Run the debugger over a set of replays
        2) Figure out where the failed event boundry should have been
        3) Alter the reader code to make it happen
        4) Repeat

    To figure out how to alter the reader code you'll probably need to compile
    lists of failed events with the correct bytes and look for patterns that
    would help you read them the right way. Sometimes it also helps to think
    about what that event represents and what would make its content length
    vary. Cross checking against a replay can also be useful.

    When altering the reader code, NEVER change code in an older game events
    reader unless you really really know what you are doing. Instead copy the
    function you'd like to change into the GameEventsReader_22612 class and
    make your changes there.
"""
import sys
import sc2reader
from sc2reader.exceptions import ReadError
from sc2reader.utils import get_files

BYTES_WIDTH = 45

def format_bytes(bytes):
    """I find it easier to read hex when spaced by byte"""
    bytes = bytes.encode("hex")
    ret = ""
    for i in range(len(bytes)):
        if i%2:
            ret += " "
        else:
            ret += bytes[i:i+2]
    return ret

def get_name(obj):
    return obj.__class__.__name__

for filename in set(sum((list(get_files(arg)) for arg in sys.argv[1:]),list())):
    try:
        replay = sc2reader.load_replay(filename, debug=True)
    except ReadError as e:
        print filename
        if len(e.game_events):
            for event in e.game_events[-3:-1]:
                print "  ....... {:0>2}:{:0>2} P{} {: <19} - {}".format(event.second/60, event.second%60, event.pid, get_name(event), format_bytes(event.bytes))
            last_event = e.game_events[-1]
            line1_end = e.location+BYTES_WIDTH-len(last_event.bytes)-1
            line1 = e.buffer.read_range(e.location, line1_end)
            line2 = e.buffer.read_range(line1_end,line1_end+BYTES_WIDTH)
            print "  0x{:0>5X} {:0>2}:{:0>2} P{} {: <19} - {} | {}".format(e.location, last_event.second/60, last_event.second%60, last_event.pid, get_name(last_event), format_bytes(last_event.bytes), format_bytes(line1))
            print " "*41+format_bytes(line2)
        else:
            print "  0x{:0>5X} {: <19} - {}".format(0, "None", format_bytes(e.buffer.read_range(0,BYTES_WIDTH+1)))
        print