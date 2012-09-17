from __future__ import absolute_import

from cStringIO import StringIO
import fnmatch
import os
import re
import struct
import textwrap
import sys
import mpyq
import functools
from itertools import groupby
from datetime import timedelta
from collections import deque

from sc2reader import exceptions
from sc2reader.constants import COLOR_CODES, BUILD_ORDER_UPGRADES
from sc2reader.data import build22612 as Data

LITTLE_ENDIAN,BIG_ENDIAN = '<','>'

class ReplayBuffer(object):
    """ The ReplayBuffer is a wrapper over the a StringIO object and provides
        convenience functions for reading structured data from Starcraft II
        replay files.
    """

    def __init__(self, source):
        #Accept file like objects and string objects
        if hasattr(source,'read'):
            source = source.read()
        self.istream = StringIO(source)

        # Expose part of the interface
        self.read = self.istream.read
        self.seek = self.istream.seek
        self.tell = self.istream.tell

        # get length of stream
        self.seek(0, os.SEEK_END)
        self.length = self.istream.tell()
        self.seek(0, os.SEEK_SET)

        # helpers to deal with bit reads
        self.bit_shift = 0
        self.bit_buffer = None

        # Extra optimization stuff
        self.lo_masks = [0x00, 0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF]
        self.hi_masks = [0xFF ^ mask for mask in self.lo_masks]
        self.masks = zip(self.lo_masks, self.hi_masks)
        self.temp_buffer = StringIO()

    '''
        Helper Functions
    '''
    @property
    def is_empty(self):
        return self.tell() == self.length

    def bytes_left(self):
        return self.length - self.tell()

    def byte_align(self):
        self.bit_shift=0

    def reset(self):
        self.bit_shift=0
        self.seek(0, os.SEEK_SET)

    def skip(self, bytes):
        self.seek(bytes-1, os.SEEK_CUR)
        self.bit_buffer = ord(self.read(1))

    def read_range(self, start, end):
        cur = self.tell()
        self.seek(start, os.SEEK_SET)
        bytes = self.read(end-start)
        self.seek(cur, os.SEEK_SET)
        return bytes

    def peek(self, length):
        cur = self.tell()
        bytes = self.read(length)
        self.istream.seek(cur, os.SEEK_SET)
        return bytes

    '''
        Optimized bit-shift aware read methods
    '''
    def read_byte(self):
        #if self.bytes_left() == 0:
        #    raise EOFError("Cannot read byte; no bytes remaining")

        if self.bit_shift==0:
            return ord(self.read(1))
        else:
            lo_mask, hi_mask = self.masks[self.bit_shift]
            hi_bits = self.bit_buffer & hi_mask
            self.bit_buffer = ord(self.read(1))
            lo_bits = self.bit_buffer & lo_mask
            return hi_bits | lo_bits

    def read_short(self, endian=LITTLE_ENDIAN):
        #if self.bytes_left() < 2:
        #    raise EOFError("Cannot read short; only {} bytes left in buffer".format(self.left))

        if self.bit_shift == 0:
            return struct.unpack(endian+'H', self.read(2))[0]

        else:
            lo_mask, hi_mask = self.masks[self.bit_shift]
            block = struct.unpack('>H', self.read(2))[0]
            number = (self.bit_buffer & hi_mask) << 8 | (block & 0xFF00) >> (8-self.bit_shift) | (block & lo_mask)
            self.bit_buffer = block & 0xFF
            if endian == LITTLE_ENDIAN:
                number = (number & 0xFF00) >> 8 | (number & 0xFF) << 8

            return number

    def read_int(self, endian=LITTLE_ENDIAN):
        #if self.bytes_left() < 4:
        #    raise EOFError("Cannot read int; only {} bytes left in buffer".format(self.left))

        if self.bit_shift == 0:
            return struct.unpack(endian+'I', self.read(4))[0]

        else:
            lo_mask, hi_mask = self.masks[self.bit_shift]
            block = struct.unpack('>I', self.read(4))[0]
            number = (self.bit_buffer & hi_mask) << 24 | (block & 0xFFFFFF00) >> (8-self.bit_shift) | (block & lo_mask)
            self.bit_buffer = block & 0xFF
            if endian == LITTLE_ENDIAN:
                number = (number & 0xFF000000) >> 24 | (number & 0xFF0000) >> 8 | (number & 0xFF00) << 8 | (number & 0xFF) << 24

            return number

    def read_bits(self, bits):
        #if self.bytes_left()*8 < bits-(8-self.bit_shift):
        #    raise EOFError("Cannot read {} bits. only {} bits left in buffer.".format(bits, (self.length-self.tell()+1)*8-self.bit_shift))
        bit_shift = self.bit_shift
        if bit_shift!=0:
            bits_left = 8-bit_shift

            # Read it all and continue
            if bits_left < bits:
                bits -= bits_left
                result = (self.bit_buffer >> bit_shift) << bits

            # Read part and return
            elif bits_left > bits:
                self.bit_shift+=bits
                return (self.bit_buffer >> bit_shift) & self.lo_masks[bits]

            # Read all and return
            else:
                self.bit_shift = 0
                return self.bit_buffer >> bit_shift

        else:
            result = 0

        if bits >= 8:
            bytes = bits/8

            if bytes == 1:
                bits -= 8
                result |= ord(self.read(1)) << bits

            elif bytes == 2:
                bits -= 16
                result |= struct.unpack(">H",self.read(2))[0] << bits

            elif bytes == 4:
                bits -= 32
                result |= struct.unpack(">I",self.read(4))[0] << bits

            else:
                for byte in struct.unpack("B"*bytes, self.read(bytes)):
                    bits -= 8
                    result |= byte << bits

        if bits != 0:
            self.bit_buffer = ord(self.read(1))
            result |= self.bit_buffer & self.lo_masks[bits]

        self.bit_shift = bits
        return result

    def read_bytes(self, bytes):
        #if self.bytes_left() < bytes:
        #    raise EOFError("Cannot read {} bytes. only {} bytes left in buffer.".format(bytes, self.length-self.tell()))

        if self.bit_shift==0:
            return self.read(bytes)

        else:
            temp_buffer = self.temp_buffer
            prev_byte = self.bit_buffer
            lo_mask, hi_mask = self.masks[self.bit_shift]
            for next_byte in struct.unpack("B"*bytes, self.read(bytes)):
                temp_buffer.write(chr(prev_byte & hi_mask | next_byte & lo_mask))
                prev_byte = next_byte

            self.bit_buffer = prev_byte
            final_bytes = temp_buffer.getvalue()
            temp_buffer.truncate(0)
            return final_bytes


    '''
        Common read patterns
    '''
    def read_variable_int(self):
        """ Blizzard Variable Length integer """
        value, bit_shift, more = 0, 0, True
        while more:
            byte = self.read_byte()
            value = ((byte & 0x7F) << bit_shift) | value
            more = byte & 0x80
            bit_shift += 7

        #The last bit of the result is a sign flag
        return pow(-1, value & 0x1) * (value >> 1)

    def read_string(self, length=None, endian=BIG_ENDIAN):
        if length == None:
            length = self.read_byte() # Counts are always doubled?

        bytes = self.read_bytes(length)
        if endian==LITTLE_ENDIAN:
            bytes = bytes[::-1]

        return bytes

    def read_timestamp(self):
        """
        Timestamps are 1-4 bytes long and represent a number of frames. Usually
        it is time elapsed since the last event. A frame is 1/16th of a second.
        The least significant 2 bits of the first byte specify how many extra
        bytes the timestamp has.
        """
        first = self.read_byte()
        time,count = first >> 2, first & 0x03
        if count == 0:
            return time
        elif count == 1:
            return time << 8 | self.read_byte()
        elif count == 2:
            return time << 16 | self.read_short(BIG_ENDIAN)
        elif count == 3:
            return time << 24 | self.read_short(BIG_ENDIAN) << 8 | self.read_byte()

    def read_data_struct(self, indent=0, key=None):
        """
        Read a Blizzard data-structure. Structure can contain strings, lists,
        dictionaries and custom integer types.
        """
        debug = False

        #The first byte serves as a flag for the type of data to follow
        datatype = self.read_byte()
        prefix = hex(self.tell())+"\t"*indent
        if key != None:
            prefix+="{0}:".format(key)
        prefix+=" {0}".format(datatype)

        if datatype == 0x00:
            #0x00 is an array where the first X bytes mark the number of entries in
            #the array. See variable int documentation for details.
            entries = self.read_variable_int()
            prefix+=" ({0})".format(entries)
            if debug: print prefix
            data = [self.read_data_struct(indent+1,i) for i in range(entries)]

        elif datatype == 0x01:
            #0x01 is an array where the first X bytes mark the number of entries in
            #the array. See variable int documentation for details.
            #print self.peek(10)
            self.read_bytes(2).encode("hex")
            entries = self.read_variable_int()
            prefix+=" ({0})".format(entries)
            if debug: print prefix
            data = [self.read_data_struct(indent+1,i) for i in range(entries)]

        elif datatype == 0x02:
            #0x02 is a byte string with the first byte indicating
            #the length of the byte string to follow
            byte = self.read_byte()
            data = self.read_string(byte/2)
            prefix+=" ({0}) - {1}".format(len(data),data)
            if debug: print prefix

        elif datatype == 0x03:
            #0x03 is an unknown data type where the first byte appears
            #to have no effect and kicks back the next instruction
            flag = self.read_byte()
            if debug: print prefix
            data = self.read_data_struct(indent,key)

        elif datatype == 0x04:
            #0x04 is an unknown data type where the first byte of information
            #is a switch (1 or 0) that can trigger another structure to be
            #read.
            flag = self.read_byte()
            if flag:
                if debug: print prefix
                data = self.read_data_struct(indent,key)
            else:
                data = 0
                prefix+=" - {0}".format(data)
                if debug: print prefix

        elif datatype == 0x05:
            #0x05 is a serialized key,value structure with the first byte
            #indicating the number of key,value pairs to follow
            #When looping through the pairs, the first byte is the key,
            #followed by the serialized data object value
            data = dict()
            entries = self.read_byte()/2
            prefix+=" ({0})".format(entries)
            if debug: print prefix
            for i in range(entries):
                key = self.read_byte()/2
                data[key] = self.read_data_struct(indent+1,key) #Done like this to keep correct parse order

        elif datatype == 0x06:
            data = self.read_byte()
            prefix+=" - {0}".format(data)
            if debug: print prefix
        elif datatype == 0x07:
            data = self.read(4)
            prefix+=" - {0}".format(data)
            if debug: print prefix
        elif datatype == 0x09:
            data = self.read_variable_int()
            prefix+=" - {0}".format(data)
            if debug: print prefix
        else:
            if debug: print prefix
            raise TypeError("Unknown Data Structure: '%s'" % datatype)

        return data


class PersonDict(dict):
    """
    Supports lookup on both the player name and player id

    ::

        person = PersonDict()
        person[1] = Player(1,"ShadesofGray")
        me = person.name("ShadesofGray")
        del person[me.pid]

    Delete is supported on the player id only
    """
    def __init__(self, players=[]):
        super(PersonDict, self).__init__()
        self._key_map = dict()

        # Support creation from iterables
        for player in players:
            self[player.pid] = player

    def name(self, player_name):
        return self._key_map[player_name]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._key_map[key] = value.pid
            key = value.pid
        elif isinstance(key, int):
            self._key_map[value.name] = key

        super(PersonDict, self).__setitem__(value.pid, value)


def windows_to_unix(windows_time):
    # This windows timestamp measures the number of 100 nanosecond periods since
    # January 1st, 1601. First we subtract the number of nanosecond periods from
    # 1601-1970, then we divide by 10^7 to bring it back to seconds.
    return (windows_time-116444735995904000)/10**7

class AttributeDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('No such attribute {0}'.format(name))

    def __setattr__(self, name, value):
        self[name] = value

    def copy(self):
        return AttributeDict(super(AttributeDict,self).copy())

class Color(AttributeDict):
    """
    Stores the string and rgba representation of a color. Individual components
    of the color can be retrieved with the dot operator::

        color = Color(r=255, g=0, b=0, a=75)
        tuple(color.r,color.g, color.b, color.a) = color.rgba

    Because Color is an implementation of an AttributeDict you must specify
    each component by name in the constructor.

    Can print the string representation with str(Color)
    """

    @property
    def rgba(self):
        """Tuple containing the (r,g,b,a) representation of the color"""
        return (self.r,self.g,self.b,self.a)

    @property
    def hex(self):
        """The hexadecimal representation of the color"""
        return "{0.r:02X}{0.g:02X}{0.b:02X}".format(self)

    def __str__(self):
        if not hasattr(self,'name'):
            self.name = COLOR_CODES[self.hex]
        return self.name

def open_archive(replay_file):
    # Don't read the listfile because some replays have corrupted listfiles
    # from tampering by 3rd parties.
    #
    # In order to catch mpyq exceptions we have to do this hack because
    # mypq could throw pretty much anything.
    try:
        replay_file.seek(0)
        return  mpyq.MPQArchive(replay_file, listfile=False)
    except Exception as e:
        trace = sys.exc_info()[2]
        raise exceptions.MPQError("Unable to construct the MPQArchive",e), None, trace

def extract_data_file(data_file, archive):
    # To wrap mpyq exceptions we have to do this try hack again.
    try:
        # Some sites tamper with the replay archive files so
        # Catch decompression errors and try again before giving up
        if data_file == 'replay.message.events':
            try:
                file_data = archive.read_file(data_file, force_decompress=True)
            except Exception as e:
                if str(e) in ("string index out of range", "Unsupported compression type."):
                    file_data = archive.read_file(data_file, force_decompress=False)
                else:
                    raise
        else:
            file_data = archive.read_file(data_file)

        return file_data

    except Exception as e:
        trace = sys.exc_info()[2]
        raise exceptions.MPQError("Unable to extract file: {}".format(data_file),e), None, trace

def read_header(replay_file):
    # Extract useful header information from the MPQ files. This information
    # can be used to configure the rest of the program to correctly parse
    # the archived data files.
    replay_file.seek(0)
    data = ReplayBuffer(replay_file)

    # Sanity check that the input is in fact an MPQ file
    if data.length==0 or data.read(4) != "MPQ\x1b":
        msg = "File '{}' is not an MPQ file";
        raise exceptions.FileError(msg.format(getattr(replay_file, 'name', '<NOT AVAILABLE>')))

    max_data_size = data.read_int(LITTLE_ENDIAN)
    header_offset = data.read_int(LITTLE_ENDIAN)
    data_size = data.read_int(LITTLE_ENDIAN)

    #array [unknown,version,major,minor,build,unknown] and frame count
    header_data = data.read_data_struct()
    versions = header_data[1].values()
    frames = header_data[3]
    build = versions[4]
    release_string = "%s.%s.%s.%s" % tuple(versions[1:5])
    length = Length(seconds=frames/16)

    keys = ('versions', 'frames', 'build', 'release_string', 'length')
    return filter(lambda item: item[0] in keys, locals().iteritems())

def merged_dict(a, b):
    c = a.copy()
    c.update(b)
    return c

def extension_filter(filename, extension):
    name, ext = os.path.splitext(filename)
    return ext.lower()[1:] == extension.lower()

def get_files(path, exclude=list(), depth=-1, followlinks=False, extension=None, **extras):
    # os.walk and os.path.isfile fail silently. We want to be loud!
    if not os.path.exists(path):
        raise ValueError("Location `{0}` does not exist".format(path))

    # If an extension is supplied, use it to do a type check
    if extension == None:
        type_check = lambda n: True
    else:
        type_check = functools.partial(extension_filter, extension=extension)

    # os.walk can't handle file paths, only directories
    if os.path.isfile(path):
        if type_check(path):
            yield path
        else:
            pass # return and halt the generator

    else:
        for root, directories, filenames in os.walk(path, followlinks=followlinks):
            # Exclude the indicated directories by removing them from `directories`
            for directory in list(directories):
                if directory in exclude or depth == 0:
                    directories.remove(directory)

            # Extend our return value only with the allowed file type and regex
            for filename in filter(type_check, filenames):
                yield os.path.join(root, filename)

            depth -= 1


class Length(timedelta):
    """
        Extends the builtin timedelta class. See python docs for more info on
        what capabilities this gives you.
    """

    @property
    def hours(self):
        """The number of hours in represented."""
        return self.seconds/3600

    @property
    def mins(self):
        """The number of minutes in excess of the hours."""
        return (self.seconds/60)%60

    @property
    def secs(self):
        """The number of seconds in excess of the minutes."""
        return self.seconds%60

    def __str__(self):
        if self.hours:
            return "{0:0>2}.{1:0>2}.{2:0>2}".format(self.hours,self.mins,self.secs)
        else:
            return "{0:0>2}.{1:0>2}".format(self.mins,self.secs)


def get_unit(type_int):
    """
    Takes an int, i, with (i & 0xff000000) = 0x01000000
    and returns the corresponding unit/structure
    """
    # Try to parse a unit
    unit_code = ((type_int & 0xff) << 8) | 0x01
    if unit_code in Data.units:
        unit_name = Data.units[unit_code].name
    else:
        unit_name = "Unknown Unit ({0:X})".format(type_int)

    return dict(name=unit_name, type_int=hex(type_int))


def get_research(type_int):
    """
    Takes an int, i, with (i & 0xff000000) = 0x02000000
    and returns the corresponding research/upgrade
    """
    research_code = ((type_int & 0xff) << 8) | 0x02
    if research_code in BUILD_ORDER_UPGRADES:
        research_name = BUILD_ORDER_UPGRADES[research_code]
    else:
        research_name = "Unknown upgrade ({0:X})".format(research_code)

    return dict(name=research_name, type_int=hex(type_int))

def parse_hash(hash_string):
    """Parse a hash to useful data"""
    # TODO: this could be used when processing replays.initData as well
    return {
        'server': hash_string[4:8].strip(),
        'hash' : hash_string[8:].encode('hex'),
        'type' : hash_string[0:4]
        }
