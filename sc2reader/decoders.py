# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

from io import BytesIO

import struct
import functools

try:
    from collections import OrderedDict
except ImportError as e:
    from ordereddict import OrderedDict


class ByteDecoder(object):
    """
    :param contents: The string or file-like object to decode
    :param endian: Either > or <. Indicates the endian the bytes are stored in.

    Used to unpack parse byte aligned files.
    """

    #: The Bytes object used internally for reading from the
    #: decoder contents. cStringIO is faster than managing our
    #: own string access in python. For PyPy installations a
    #: managed string implementation might be faster.
    _buffer = None

    #: The string buffer being decoded. A direct reference
    #: is kept around to make read_range and peek faster.
    _contents = ""

    def __init__(self, contents, endian):
        """
        Accepts both strings and files implementing ``read()`` and
        decodes them in the specified endian format.
        """
        if hasattr(contents, "read"):
            self._contents = contents.read()
        else:
            self._contents = contents

        self._buffer = BytesIO(self._contents)
        self.length = len(self._contents)

        # Expose the basic BytesIO interface
        self.read = self._buffer.read
        self.seek = self._buffer.seek
        self.tell = self._buffer.tell

        # decode the endian value if necessary
        self.endian = endian.lower()
        if self.endian.lower() == "little":
            self.endian = "<"
        elif self.endian.lower() == "big":
            self.endian = ">"
        elif self.endian not in ("<", ">"):
            raise ValueError(
                "Endian must be one of 'little', '<', 'big', or '>' but was: "
                + self.endian
            )

        # Pre-compiling
        self._unpack_int = struct.Struct(str(self.endian + "I")).unpack
        self._unpack_short = struct.Struct(str(self.endian + "H")).unpack
        self._unpack_longlong = struct.Struct(str(self.endian + "Q")).unpack
        self._unpack_bytes = lambda bytes: bytes if self.endian == ">" else bytes[::-1]

    def done(self):
        """
        Returns true when all bytes have been decoded
        """
        return self.tell() == self.length

    def read_range(self, start, end):
        """
        Returns the raw byte string from the indicated address range
        """
        return self._contents[start:end]

    def peek(self, count):
        """
        Returns the raw byte string for the next ``count`` bytes
        """
        start = self.tell()
        return self._contents[start : start + count]

    def read_uint8(self):
        """
        Returns the next byte as an unsigned integer
        """
        return ord(self.read(1))

    def read_uint16(self):
        """
        Returns the next two bytes as an unsigned integer
        """
        return self._unpack_short(self.read(2))[0]

    def read_uint32(self):
        """
        Returns the next four bytes as an unsigned integer
        """
        return self._unpack_int(self.read(4))[0]

    def read_uint64(self):
        """
        Returns the next eight bytes as an unsigned integer
        """
        return self._unpack_longlong(self.read(8))[0]

    def read_bytes(self, count):
        """
        Returns the next ``count`` bytes as a byte string
        """
        return self._unpack_bytes(self.read(count))

    def read_uint(self, count):
        """
        Returns the next ``count`` bytes as an unsigned integer
        """
        unpack = struct.Struct(str(self.endian + "B" * count)).unpack
        uint = 0
        for byte in unpack(self.read(count)):
            uint = uint << 8 | byte
        return uint

    def read_string(self, count, encoding="utf8"):
        """
        Read a string in given encoding (default utf8) that is ``count`` bytes long
        """
        return self.read_bytes(count).decode(encoding)

    def read_cstring(self, encoding="utf8"):
        """
        Read a NULL byte terminated character string decoded with given encoding (default utf8). Ignores endian.
        """
        cstring = BytesIO()
        while True:
            c = self.read(1)
            if ord(c) == 0:
                return cstring.getvalue().decode(encoding)
            else:
                cstring.write(c)


class BitPackedDecoder(object):
    """
    :param contents: The string of file-like object to decode

    Extends :class:`ByteDecoder`. Always packed BIG_ENDIAN

    Adds capabilities for parsing files that Blizzard has packed in
    bits and not in bytes.

    """

    #: The ByteDecoder used internally to read byte
    #: aligned values.
    _buffer = None

    #: Tracks the how many bits have already been used
    #: from the current byte.
    _bit_shift = 0

    #: Holds the byte, if any, that hasn't had its bits
    #: fully used yet.
    _next_byte = None

    #: Maps bit shifts to low bit masks used for grabbing
    #: the first bits off of the next byte.
    _lo_masks = [0x00, 0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF]

    #: Maps bit shifts to high bit masks used for grabbing
    #: the remaining bits off of the previous byte.
    _hi_masks = [0xFF ^ mask for mask in _lo_masks]

    #: Maps bit shifts to high and low bit masks. Used for
    #: joining bytes when we are not byte aligned.
    _bit_masks = list(zip(_lo_masks, _hi_masks))

    def __init__(self, contents):
        self._buffer = ByteDecoder(contents, endian="BIG")

        # Partially expose the ByteBuffer interface
        self.length = self._buffer.length
        self.tell = self._buffer.tell
        self.peek = self._buffer.peek
        self.read_range = self._buffer.read_range

        # Reduce the number of lookups required to read
        self._read = self._buffer.read
        self.read_bool = functools.partial(self.read_bits, 1)

    def done(self):
        """
        Returns true when all bytes in the buffer have been used
        """
        return self.tell() == self.length

    def byte_align(self):
        """
        Moves cursor to the beginning of the next byte
        """
        self._next_byte = None
        self._bit_shift = 0

    def read_uint8(self):
        """
        Returns the next 8 bits as an unsigned integer
        """
        data = ord(self._buffer.read(1))

        if self._bit_shift != 0:
            lo_mask, hi_mask = self._bit_masks[self._bit_shift]
            hi_bits = self._next_byte & hi_mask
            lo_bits = data & lo_mask
            self._next_byte = data
            data = hi_bits | lo_bits

        return data

    def read_uint16(self):
        """
        Returns the next 16 bits as an unsigned integer
        """
        data = self._buffer.read_uint16()

        if self._bit_shift != 0:
            lo_mask, hi_mask = self._bit_masks[self._bit_shift]
            hi_bits = (self._next_byte & hi_mask) << 8
            mi_bits = (data & 0xFF00) >> (8 - self._bit_shift)
            lo_bits = data & lo_mask
            self._next_byte = data & 0xFF
            data = hi_bits | mi_bits | lo_bits

        return data

    def read_uint32(self):
        """
        Returns the next 32 bits as an unsigned integer
        """
        data = self._buffer.read_uint32()

        if self._bit_shift != 0:
            lo_mask, hi_mask = self._bit_masks[self._bit_shift]
            hi_bits = (self._next_byte & hi_mask) << 24
            mi_bits = (data & 0xFFFFFF00) >> (8 - self._bit_shift)
            lo_bits = data & lo_mask
            self._next_byte = data & 0xFF
            data = hi_bits | mi_bits | lo_bits

        return data

    def read_uint64(self):
        """Returns
        the next 64 bits as an unsigned integer
        """
        data = self._buffer.read_uint64()

        if self._bit_shift != 0:
            lo_mask, hi_mask = self._bit_masks[self._bit_shift]
            hi_bits = (self._next_byte & hi_mask) << 56
            mi_bits = (data & 0xFFFFFFFFFFFFFF00) >> (8 - self._bit_shift)
            lo_bits = data & lo_mask
            self._next_byte = data & 0xFF
            data = hi_bits | mi_bits | lo_bits

        return data

    def read_vint(self):
        """
        Reads a signed integer of variable length
        """
        byte = ord(self._buffer.read(1))
        negative = byte & 0x01
        result = (byte & 0x7F) >> 1
        bits = 6
        while byte & 0x80:
            byte = self.read_uint8()
            result |= (byte & 0x7F) << bits
            bits += 7
        return -result if negative else result

    def read_aligned_bytes(self, count):
        """
        Skips to the beginning of the next byte and returns the next ``count`` bytes as a byte string
        """
        self.byte_align()
        return self._buffer.read_bytes(count)

    def read_aligned_string(self, count, encoding="utf8"):
        """
        Skips to the beginning of the next byte and returns the next ``count`` bytes decoded with encoding (default utf8)
        """
        self.byte_align()
        return self._buffer.read_string(count, encoding)

    def read_bytes(self, count):
        """
        Returns the next ``count*8`` bits as a byte string
        """
        data = self._buffer.read_bytes(count)

        if self._bit_shift != 0:
            temp_buffer = BytesIO()
            prev_byte = self._next_byte
            lo_mask, hi_mask = self._bit_masks[self._bit_shift]
            for next_byte in struct.unpack(str("B") * count, data):
                temp_buffer.write(
                    struct.pack(str("B"), prev_byte & hi_mask | next_byte & lo_mask)
                )
                prev_byte = next_byte

            self._next_byte = prev_byte
            data = temp_buffer.getvalue()
            temp_buffer.truncate(0)

        return data

    def read_bits(self, count):
        """Returns
        the next ``count`` bits as an unsigned integer
        """
        result = 0
        bits = count
        bit_shift = self._bit_shift

        # If we've got a byte in progress use it first
        if bit_shift != 0:
            bits_left = 8 - bit_shift

            if bits_left < bits:
                bits -= bits_left
                result = (self._next_byte >> bit_shift) << bits
            elif bits_left > bits:
                self._bit_shift += bits
                return (self._next_byte >> bit_shift) & self._lo_masks[bits]
            else:
                self._bit_shift = 0
                return self._next_byte >> bit_shift

        # Then grab any additional whole bytes as needed
        if bits >= 8:
            bytes = int(bits / 8)

            if bytes == 1:
                bits -= 8
                result |= self._buffer.read_uint8() << bits

            elif bytes == 2:
                bits -= 16
                result |= self._buffer.read_uint16() << bits

            elif bytes == 4:
                bits -= 32
                result |= self._buffer.read_uint32() << bits

            else:
                for byte in struct.unpack(str("B") * bytes, self._read(bytes)):
                    bits -= 8
                    result |= byte << bits

        # Grab any trailing bits from the next byte
        if bits != 0:
            self._next_byte = ord(self._read(1))
            result |= self._next_byte & self._lo_masks[bits]

        self._bit_shift = bits
        return result

    def read_frames(self):
        """
        Reads a frame count as an unsigned integer
        """
        byte = self.read_uint8()
        time, additional_bytes = byte >> 2, byte & 0x03
        if additional_bytes == 0:
            return time
        elif additional_bytes == 1:
            return time << 8 | self.read_uint8()
        elif additional_bytes == 2:
            return time << 16 | self.read_uint16()
        elif additional_bytes == 3:
            return time << 24 | self.read_uint16() << 8 | self.read_uint8()

    def read_struct(self, datatype=None):
        """
        Reads a nested data structure. If the type is not specified
        the first byte is used as the type identifier.
        """
        self.byte_align()
        datatype = ord(self._buffer.read(1)) if datatype is None else datatype

        if datatype == 0x00:  # array
            data = [self.read_struct() for i in range(self.read_vint())]

        elif datatype == 0x01:  # bitarray, weird alignment requirements
            bits = self.read_vint()
            data = self.read_bits(bits)

        elif datatype == 0x02:  # blob
            length = self.read_vint()
            data = self._buffer.read_bytes(length)

        elif datatype == 0x03:  # choice
            flag = self.read_vint()
            data = self.read_struct()

        elif datatype == 0x04:  # optional
            exists = self._buffer.read_uint8() != 0
            data = self.read_struct() if exists else None

        elif datatype == 0x05:  # Struct
            entries = self.read_vint()
            data = dict(
                [(self.read_vint(), self.read_struct()) for i in range(entries)]
            )

        elif datatype == 0x06:  # u8
            data = ord(self._buffer.read(1))

        elif datatype == 0x07:  # u32
            data = self._buffer.read_bytes(4)  # self.read_uint32()

        elif datatype == 0x08:  # u64
            data = self._buffer.read_uint64()

        elif datatype == 0x09:  # vint
            data = self.read_vint()

        else:
            raise TypeError("Unknown Data Structure: '{0}'".format(datatype))

        return data
