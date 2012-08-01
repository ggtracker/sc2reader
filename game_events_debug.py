""" Game Event Parsing Debugger
    ===============================

    Recursively searches for unique replays specified by command line argument
    and attempts a parse in order to catch the ReadError. The ReadError will
    contain all the context information we need to inspect the error.

    Outputs the following information in the following format:

        ggtracker/ggtracker_replay_202597.SC2Replay
          ....... 00:04 P2 AbilityEvent        - 00 22 0b 01 08 34 07 00 31 00 00 01 1f 0d 21 f8 00 8c c0 80 00 05 ff 00
          ....... 00:05 P1 SelectionEvent      - 38 21 ac 00 06 00 01 05 15 01 03 03 05 18 00 01 05 20 00 01 05 28 00 01
          0x000F5 00:05 P2 SelectionEvent      - 00 22 ac 00 02 f4 00 00  | 00 0c a1 89 00 10 00 00 00 21 0b 01 00 01 5c 01 00 0c 22 0b
                                                 01 08 34 07 00 23 80 00 01 1f 0d 41 18 00 8a c0 80 00 05 ff 00 08 21 ac 00 02 11 01 02

    The first line is the full path to the file, followed by an
    indented list of the last 3 events that were parsed before an
    Error was thrown.

    The last line shows the last event that was parsed without
    throwing an Error, and the bytes that follow it.  The pipe
    character delimits where the parser ended the event.

    Often an Error is thrown because our code consumes the wrong
    number of bytes for the immediately previous Event.

    In the example above:

        00 22 ac 00 02 f4 00 00  | 00 0c a1 89 00 10 00 00 00 21 0b 01 00 01 5c 01 00 0c 22 0b

    The boundaries should be here:

        00 22 ac 00 02 f4 00 00 00 | 0c a1 89 00 10 00 00 | 00 21 0b 01 00 01 5c 01 00 | 0c 22 0b

    So the correct bytes for the failed event are these:

        00 22 ac 00 02 f4 00 00 00


    The general workflow is something like this:

        1) Run the debugger over a set of replays
        2) Figure out where the failed event boundry should have been
        3) Alter the reader code to make it happen
        4) Repeat


    To figure out how to alter the reader code you'll probably need to compile
    lists of failed events with these correct bytes and look for patterns that
    would help you read them the right way.

    Sometimes it also helps to think about what that event represents and what
    would make its content length vary. Cross checking against a replay can
    also be useful.

    When altering the reader code, NEVER change code in an older game events
    reader unless you really really know what you are doing. Instead copy the
    function you'd like to change into the GameEventsReader_22612 class and
    make your changes there.


    Pointers for finding boundaries
    ==================================

    The easiest way to find the right boundary is to scan the following bytes
    until you see a clear marker for a different event and then work your way
    backwards until you can't anymore.

    The first part of a new event is always a timestamp and usually, maybe
    9/10 times, the timestamp will only be 1 bye long and therefore a multiple
    of 4 (including 0).

    Immediately following the timestamp is a byte with bits split 3-5 for
    event_type and player_id. The event type is never more than 5 and the
    player_id is generally less than 4 for ladder games.

    The next byte after that is the event code. Common event codes include:
    AC, XD, 61, and XB where X is any number. You can find a list of event
    codes in the sc2reader.readers.GameEventsReader_Base class.
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
            print " Location  Time P# EventType             Bytes"
            for event in e.game_events[-3:-1]:
                print "  ....... {:0>2}:{:0>2} P{} {: <19} - {}".format(event.second/60, event.second%60, event.pid, get_name(event), format_bytes(event.bytes))
            last_event = e.game_events[-1]
            line1_end = e.location+BYTES_WIDTH-len(last_event.bytes)-1
            line1 = e.buffer.read_range(e.location, line1_end)
            line2 = e.buffer.read_range(line1_end,line1_end+BYTES_WIDTH)
            print "  0x{:0>5X} {:0>2}:{:0>2} P{} {: <19} - {} | {}".format(e.location, last_event.second/60, last_event.second%60, last_event.pid, get_name(last_event), format_bytes(last_event.bytes), format_bytes(line1))
            print " "*41+format_bytes(line2)
            print e
        else:
            print "  0x{:0>5X} {: <19} - {}".format(0, "None", format_bytes(e.buffer.read_range(0,BYTES_WIDTH+1)))
        print
