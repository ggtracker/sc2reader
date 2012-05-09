from __future__ import absolute_import

import cStringIO
import fnmatch
import os
import re
import struct
import textwrap
import sys
import mpyq
from itertools import groupby
from datetime import timedelta
from collections import deque

from sc2reader import exceptions
from sc2reader.constants import COLOR_CODES, BUILD_ORDER_UPGRADES
from sc2reader.data.build19595 import Data_19595 as Data

LITTLE_ENDIAN,BIG_ENDIAN = '<','>'

class ReplayBuffer(object):
    """ The ReplayBuffer is a wrapper over the cStringIO object and provides
        convenience functions for reading structured data from Starcraft II
        replay files. These convenience functions can be sorted into several
        different categories providing an interface as follows:

        Stream Manipulation::
            tell(self)
            skip(self, amount)
            reset(self)
            align(self)
            seek(self, position, mode=SEEK_CUR)

        Data Retrieval::
            read_variable_int(self)
            read_string(self,additional)
            read_timestamp(self)
            read_count(self)
            read_data_structure(self)
            read_object_type(self, read_modifier=False)
            read_object_id(self)
            read_coordinate(self)
            read_bitmask(self)
            read_range(self, start, end)

        Basic Reading::
            read_byte(self)
            read_int(self, endian=LITTLE_ENDIAN)
            read_short(self, endian=LITTLE_ENDIAN)
            read_chars(self,length)
            read_hex(self,length)

        Core Reading::
            shift(self,bits)
            read(bytes,bits)

        The ReplayBuffer additionally defines the following properties:
            left
            length
            cursor
    """

    def __init__(self, file):
        #Accept file like objects and string objects
        if hasattr(file,'read'):
            self.io = cStringIO.StringIO(file.read())
        else:
            self.io = cStringIO.StringIO(file)

        # get length of stream
        self.io.seek(0, os.SEEK_END)
        self.length = self.io.tell()
        self.io.seek(0)

        # setup shift defaults
        self.bit_shift = 0
        self.last_byte = None

        #Extra optimization stuff
        self.lo_masks = [0x00, 0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF]
        self.lo_masks_inv = [0x00, 0x80, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC, 0xFE, 0xFF]
        self.hi_masks = [0xFF ^ mask for mask in self.lo_masks]
        self.hi_masks_inv = [0xFF ^ mask for mask in self.lo_masks_inv]
        self.coord_convert = [(2**(12 - i),1.0/2**i) for i in range(1,13)]

        self.read_basic = self.io.read
        self.char_buffer = cStringIO.StringIO()

        # Pre-generate the state for all reads, marginal time savings
        self.read_state = dict()
        for old in range(0,8):
            for new in range(0,8):
                self.read_state[(old,new)] = self.load_state(old, new)

    def load_state(self, old_bit_shift, new_bit_shift):
        old_bit_shift_inv = 8-old_bit_shift

        # Masks
        lo_mask = 2**old_bit_shift-1
        lo_mask_inv = 0xFF - 2**(8-old_bit_shift)+1
        hi_mask = 0xFF ^ lo_mask
        hi_mask_inv = 0xFF ^ lo_mask_inv

        #last byte parameters
        if new_bit_shift == 0: #this means we filled the last byte (8)
            last_mask = 0xFF
            adjustment = 8-old_bit_shift
            adjustment_mask = 2**adjustment-1
        else:
            last_mask = 2**new_bit_shift-1
            adjustment = new_bit_shift-old_bit_shift
            adjustment_mask = 2**adjustment-1

        return (old_bit_shift_inv, lo_mask, lo_mask_inv, hi_mask,
                hi_mask_inv, last_mask, adjustment, adjustment_mask)

    '''
        Additional Properties
    '''
    @property
    def left(self): return self.length - self.io.tell()
    @property
    def empty(self): return self.left==0
    @property
    def cursor(self): return self.io.tell()

    '''
        Stream manipulation functions
    '''
    def tell(self): return self.io.tell()
    def skip(self, amount): self.seek(amount, os.SEEK_CUR)
    def reset(self): self.io.seek(0); self.bit_shift = 0
    def align(self): self.bit_shift=0
    def seek(self, position, mode=os.SEEK_SET):
        self.io.seek(position, mode)
        if self.io.tell()!=0 and self.bit_shift!=0:
            self.io.seek(-1, os.SEEK_CUR)
            self.last_byte = ord(self.read_basic(1))

    def peek(self, length):
        start,last,ret = self.cursor,self.last_byte,self.read_hex(length)
        self.seek(start, os.SEEK_SET)
        self.last_byte = last
        return ret

    '''
        Read "basic" structures
    '''
    def read_byte(self):
        """ Basic byte read """
        if self.bit_shift==0:
            return ord(self.read_basic(1))
        else:
            extra_bits = self.bit_shift
            hi_bits = self.last_byte >> extra_bits
            last_byte = ord(self.read_basic(1))
            lo_bits = last_byte & self.lo_masks[extra_bits]
            self.last_byte = last_byte
            return hi_bits << extra_bits | lo_bits


    def read_int(self, endian=LITTLE_ENDIAN):
        if self.bit_shift == 0:
            return struct.unpack(endian+'I', self.read_basic(4))[0]

        else:
            old_bit_shift = self.bit_shift

            # Get all the bytes at once
            hi_bits = self.shift(8 - old_bit_shift)
            block = struct.unpack('>I', self.read_basic(4))[0]

            # Reformat them according to the rules
            number = (block >> 8) << old_bit_shift | (block & self.lo_masks[old_bit_shift])
            number += hi_bits << (24 + old_bit_shift)

            # If the number is little endian, repack it
            if endian == LITTLE_ENDIAN:
                number = (number & 0xFF000000) >> 24 | (number & 0xFF0000) >> 8 | (number & 0xFF00) << 8 | (number & 0xFF) << 24

            # Reset the shift
            self.last_byte = block & 0xFF
            self.bit_shift = old_bit_shift

            return number

    def read_short(self, endian=LITTLE_ENDIAN):
        """ short16 read """
        if self.bit_shift == 0:
            return struct.unpack(endian+'H', self.read_basic(2))[0]

        else:
            old_bit_shift = self.bit_shift

            # Get all the bytes at once
            hi_bits = self.shift(8 - old_bit_shift)
            block = struct.unpack('>H', self.read_basic(2))[0]

            # Reformat them according to the rules
            number = (block >> 8) << old_bit_shift | (block & self.lo_masks[old_bit_shift])
            number += hi_bits << (8 + old_bit_shift)

            # If the number is little endian, repack it
            if endian == LITTLE_ENDIAN:
                number = (number & 0xFF00) >> 8 | (number & 0xFF) << 8

            # Reset the shift
            self.last_byte = block & 0xFF
            self.bit_shift = old_bit_shift

            return number

    def read_chars(self, length=0):
        if self.bit_shift==0:
            return self.read_basic(length)
        else:
            self.char_buffer.truncate(0)
            self.char_buffer.writelines(map(chr,self.read(length)))
            return self.char_buffer.getvalue()

    def read_hex(self, length=0):
        return self.read_chars(length).encode("hex")

    '''
        Read replay-specific structures
    '''
    def read_count(self):
        return self.read_byte()/2

    def read_variable_int(self):
        """ Blizzard VL integer """
        byte = self.read_byte()
        shift, value = 1,byte & 0x7F
        while byte & 0x80 != 0:
            byte = self.read_byte()
            value = ((byte & 0x7F) << shift * 7) | value
            shift += 1

        #The last bit of the result is a sign flag
        return pow(-1, value & 0x1) * (value >> 1)

    def read_string(self, length=None):
        """<length> ( <char>, .. ) as unicode"""
        return self.read_chars(length if length!=None else self.read_byte())

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
            return time << 16 | self.read_short()
        elif count == 3:
            return time << 24 | self.read_short() << 8 | self.read_byte()
        else:
            raise ValueError()

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
            self.read_chars(2).encode("hex")
            entries = self.read_variable_int()
            prefix+=" ({0})".format(entries)
            if debug: print prefix
            data = [self.read_data_struct(indent+1,i) for i in range(entries)]

        elif datatype == 0x02:
            #0x02 is a byte string with the first byte indicating
            #the length of the byte string to follow
            entries = self.read_count()
            data = self.read_string(entries)
            prefix+=" ({0}) - {1}".format(entries,data)
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
            entries = self.read_count()
            prefix+=" ({0})".format(entries)
            if debug: print prefix
            for i in range(entries):
                key = self.read_count()
                data[key] = self.read_data_struct(indent+1,key) #Done like this to keep correct parse order

        elif datatype == 0x06:
            data = self.read_byte()
            prefix+=" - {0}".format(data)
            if debug: print prefix
        elif datatype == 0x07:
            data = self.read_chars(4)
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


    def read_object_type(self, read_modifier=False):
        """ Object type is big-endian short16 """
        type = self.read_short(endian=BIG_ENDIAN)
        if read_modifier:
            type = (type << 8) | self.read_byte()
        return type

    def read_object_id(self):
        """ Object ID is big-endian int32 """
        return self.read_int(endian=BIG_ENDIAN)

    def read_coordinate(self):
        # TODO: This seems unreasonably percise....
        # Read an x or y coordinate dimension
        def _coord_dimension():
            if self.bit_shift == 0:
                return (self.read_short() << 4 | self.shift(4))/4096.0

            else:
                old_bit_shift = self.bit_shift
                new_bit_shift = (20 + old_bit_shift) % 8

                # Get all the bytes at once
                hi_bits = self.shift(8 - old_bit_shift)
                block = struct.unpack('>H', self.read_basic(2))[0]

                if old_bit_shift > 4:
                    block = block << 8 | ord(self.read_basic(1))

                    number = (block >> 8) << old_bit_shift | (block & self.lo_masks[new_bit_shift])
                    number += hi_bits << (16 + new_bit_shift)
                else:
                    number = (block >> 8) << old_bit_shift | (block & self.lo_masks[new_bit_shift])
                    number += hi_bits << (8 + new_bit_shift)

                # Reset the shift
                self.last_byte = block & 0xFF
                self.bit_shift = new_bit_shift

                return number/4096.0

        # TODO?: Handle optional z dimension
        return (_coord_dimension(), _coord_dimension())

    def read_bitmask(self):
        """ Reads a bitmask given the current bitoffset """
        length = self.read_byte()
        bytes = reversed(self.read(bits=length))
        mask = 0
        for byte in bytes:
            mask = (mask << 8) | byte

        # Turn things like 10010011 into [True, False, False, True,...]
        def _make_mask(byte, bit_length, current=1):
            if current < bit_length:
                byte_mask = (2**(bit_length-current))
                bytes = [(byte & byte_mask) > 0,]
                return bytes + _make_mask(byte, bit_length, current+1)
            else:
                return [byte & 0x1 == 0x01,]

        return list(reversed(_make_mask(mask, length)))

    def read_range(self, start, end):
        current = self.cursor
        self.io.seek(start)
        ret = self.read_basic(end-start)
        self.io.seek(current)
        return ret


    '''
        Base read functions
    '''
    def shift(self, bits):
        """
        The only valid use of Buffer.shift is when you know that there are
        enough bits left in the loaded byte to accommodate your request.

        If there is no loaded byte, or the loaded byte has been exhausted,
        then Buffer.shift(8) could technically be used to read a single
        byte-aligned byte.
        """
        try:
            #declaring locals instead of accessing dict on multiple use seems faster
            bit_shift = self.bit_shift
            new_shift = bit_shift+bits

            #make sure there are enough bits left in the byte
            if new_shift <= 8:
                if not bit_shift:
                    self.last_byte = ord(self.read_basic(1))

                #using a bit_mask_array tested out to be 20% faster, go figure
                ret = (self.last_byte >> bit_shift) & self.lo_masks[bits]
                #using an if for the special case tested out to be faster, hrm
                self.bit_shift = 0 if new_shift == 8 else new_shift
                return ret

            else:
                msg = "Cannot shift off %s bits. Only %s bits remaining."
                raise ValueError(msg % (bits, 8-self.bit_shift))

        except TypeError:
            raise EOFError("Cannot shift requested bits. End of buffer reached")

    def read(self, bytes=0, bits=0):
        try:
            bytes, bits = bytes+bits/8, bits%8
            bit_count = bytes*8+bits

            #check special case of not having to do any work
            if bit_count == 0: return []

            #check sepcial case of intra-byte read
            if bit_count <= (8-self.bit_shift):
                return [self.shift(bit_count)]

            #check special case of byte-aligned reads, performance booster
            if self.bit_shift == 0:
                base = map(ord, map(self.read_basic, [1]*bytes))
                if bits != 0:
                    return base+[self.shift(bits)]
                return base

            # Calculated shifts as our keys
            old_bit_shift = self.bit_shift
            new_bit_shift = (self.bit_shift+bits) % 8

            # Load the precalculated state variables
            (old_bit_shift_inv, lo_mask, lo_mask_inv,
             hi_mask, hi_mask_inv, last_mask, adjustment,
             adjustment_mask) = self.read_state[(old_bit_shift,new_bit_shift)]

            #Set up for the looping with a list, the bytes, and an initial part
            raw_bytes = list()
            prev, next = self.last_byte, ord(self.read_basic(1))
            first = prev & hi_mask
            bit_count -= old_bit_shift_inv

            while bit_count > 0:

                if bit_count <= 8: #this is the last byte
                    #The bits in the last byte are included in order starting at
                    #the new_bit_shift boundary with extra bits bumped back a byte
                    #because we can have odd bit requests, the bit shift can change
                    last = (next & last_mask)

                    # we need to bring the first byte closer
                    # if the adjustment is lower than 0
                    if adjustment < 0:
                        first = first >> abs(adjustment)
                        raw_bytes.append(first | last)
                    elif adjustment > 0:
                        raw_bytes.append(first | (last >> adjustment))
                        raw_bytes.append(last & adjustment_mask)
                    else:
                        raw_bytes.append(first | last)

                    bit_count = 0

                if bit_count > 8: #We can do simple wrapping for middle bytes
                    second = (next & lo_mask_inv) >> old_bit_shift_inv
                    raw_bytes.append(first | second)

                    #To remain consistent, always shfit these bits into the hi_mask
                    first = (next & hi_mask_inv) << old_bit_shift
                    bit_count -= 8

                    #Cycle down to the next byte
                    prev,next = next,ord(self.read_basic(1))

            self.last_byte = next
            self.bit_shift = new_bit_shift
            return raw_bytes

        except TypeError:
            raise EOFError("Cannot read requested bits/bytes. End of buffer reached")

class PersonDict(dict):
    """
    Supports lookup on both the player name and player id

    ::

        person = PersonDict()
        person[1] = Player(1,"ShadesofGray")
        me = person["ShadesofGray"]
        del person[me.pid]

    Delete is supported on the player id only
    """
    def __init__(self, *args, **kwargs):
        self._key_map = dict()

        if args:
            for arg in args[0]:
                self[arg[0]] = arg[1]

        if kwargs:
            for key, value in kwargs.iteritems():
                self[key] = value

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self._key_map[key]

        return super(PersonDict, self).__getitem__(key)

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
        return tuple(self.r,self.g,self.b,self.a)

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
    # due  to tampering by 3rd parties.
    #
    # In order to wrap mpyq in exceptions we have to do this try hack.
    try:
        replay_file.seek(0)
        return  mpyq.MPQArchive(replay_file, listfile=False)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        trace = sys.exc_info()[2]
        raise exceptions.MPQError("Unable to construct the MPQArchive",e), None, trace

def extract_data_file(data_file, archive):
    # To wrap mpyq exceptions we have to do this try hack again.
    try:
        # Some sites tamper with the message events file so
        # Catch decompression errors and try again before giving up
        if data_file == 'replay.message.events':
            try:
                file_data = archive.read_file(data_file, force_decompress=True)
            except IndexError as e:
                if str(e) == "string index out of range":
                    file_data = archive.read_file(data_file, force_decompress=False)
                else:
                    raise
        else:
            file_data = archive.read_file(data_file)

        return file_data

    except KeyboardInterrupt:
        raise
    except Exception as e:
        trace = sys.exc_info()[2]
        raise exceptions.MPQError("Unable to extract file: {0}".format(data_file),e), None, trace

def read_header(replay_file):
    # Extract useful header information from the MPQ files. This information
    # can be used to configure the rest of the program to correctly parse
    # the archived data files.
    replay_file.seek(0)
    buffer = ReplayBuffer(replay_file)

    #Sanity check that the input is in fact an MPQ file
    if buffer.empty or buffer.read_hex(4).upper() != "4D50511B":
        msg = "File '{0}' is not an MPQ file";
        raise exceptions.FileError(msg.format(replay_file.name))

    max_data_size = buffer.read_int(LITTLE_ENDIAN)
    header_offset = buffer.read_int(LITTLE_ENDIAN)
    data_size = buffer.read_int(LITTLE_ENDIAN)

    #array [unknown,version,major,minor,build,unknown] and frame count
    header_data = buffer.read_data_struct()
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


#Monster function used to parse lobby properties in GameSummary
def get_lobby_properties(data):
    ###
    # The definition of each lobby property is in data[0][5] with the structure
    #
    # id = def[0][1] # The unique property id
    # vals = def[1]  # A list with the values the property can be
    # reqs = def[3]  # A list of requirements the property has
    # dflt = def[8]  # The default value(s) of the property
    #                this is a single entry for a global property
    #                and a list() of entries for a player property

    # The def-values is structured like this
    #
    # id = `the index in the vals list`
    # name = v[0]    # The name of the value

    # The requirement structure looks like this
    #
    # id = r[0][1][1] # The property id of this requirement
    # vals = r[1]     # A list of names of valid values for this requirement

    ###
    # The values of each property is in data[0][6][6] with the structure
    #
    # id = v[0][1]  # The property id of this value
    # vals = v[1]   # The value(s) of this property
    #                this is a single entry for a global property
    #                and a list() of entries for a player property

    ###
    # A value-entry looks like this
    #
    # index = v[0]  # The index in the def.vals array representing the value
    # unknown = v[1]

    # First get the definitions in data[0][5]
    defs = dict()
    for d in data[0][5]:
        k = d[0][1]
        defs[k] = {
            'id':k,
            'vals':d[1],
            'reqs':d[3],
            'dflt':d[8],
            'lobby_prop':type(d[8]) == type(dict())
            }
    vals = dict()

    # Get the values in data[0][6][6]
    for v in data[0][6][6]:
        k = v[0][1]
        vals[k] = {
            'id':k,
            'vals':v[1]
            }

    lobby_ids = [k for k in defs if defs[k]['lobby_prop']]
    lobby_ids.sort()
    player_ids = [k for k in defs if not defs[k]['lobby_prop']]
    player_ids.sort()

    left_lobby = deque([k for k in defs if defs[k]['lobby_prop']])

    lobby_props = dict()
    # We cycle through all property values 'til we're done
    while len(left_lobby) > 0:
        propid = left_lobby.popleft()
        can_be_parsed = True
        active = True
        # Check the requirements
        for req in defs[propid]['reqs']:
            can_be_parsed = can_be_parsed and (req[0][1][1] in lobby_props)
            # Have we parsed all req-fields?
            if not can_be_parsed:
                break
            # Is this requirement fullfilled?
            active = active and (lobby_props[req[0][1][1]] in req[1])

        if not can_be_parsed:
            # Try parse this later
            left_lobby.append(propid)
            continue
        if not active:
            # Ok, so the reqs weren't fullfilled, don't use this property
            continue
        # Nice! We've parsed a property
        lobby_props[propid] = defs[propid]['vals'][vals[propid]['vals'][0]][0]

    player_props = [dict() for pid in range(16)]
    # Parse each player separately (this is required :( )
    for pid in range(16):
        left_players = deque([a for a in player_ids])
        player = dict()

        # Use this to avoid an infinite loop
        last_success = 0
        max = len(left_players)
        while len(left_players) > 0 and not (last_success > max+1):
            last_success += 1
            propid = left_players.popleft()
            can_be_parsed = True
            active = True
            for req in defs[propid]['reqs']:
                #req is a lobby prop
                if req[0][1][1] in lobby_ids:
                    active = active and (req[0][1][1] in lobby_props) and (lobby_props[req[0][1][1]] in req[1])
                #req is a player prop
                else:
                    can_be_parsed = can_be_parsed and (req[0][1][1] in player)
                    if not can_be_parsed:
                        break
                    active = active and (player[req[0][1][1]] in req[1])

            if not can_be_parsed:
                left_players.append(propid)
                continue
            last_success = 0
            if not active:
                continue
            player[propid] = defs[propid]['vals'][vals[propid]['vals'][pid][0]][0]

        player_props[pid] = player

    return (lobby_props, player_props)

def get_unit(type_int):
    """
    Takes an int, i, with (i & 0xff000000) = 0x01000000
    and returns the corresponding unit/structure
    """
    # Try to parse a unit
    unit_code = ((type_int & 0xff) << 8) | 0x01
    if unit_code in Data.types:
        unit_name = Data.type(unit_code).name
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
        "Unknown upgrade ({0:X})".format(research_code)

    return dict(name=research_name, type_int=hex(type_int))

def parse_hash(hash_string):
    """Parse a hash to useful data"""
    # TODO: this could be used when processing replays.initData as well
    return {
        'server': hash_string[4:8].strip(),
        'hash' : hash_string[8:].encode('hex'),
        'type' : hash_string[0:4]
        }
