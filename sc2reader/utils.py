# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys
from datetime import timedelta

from sc2reader.exceptions import MPQError
from sc2reader.constants import COLOR_CODES, COLOR_CODES_INV

class DepotFile(object):
    """
    :param bytes: The raw bytes representing the depot file

    The DepotFile object parses bytes for a dependency into their components
    and assembles them into a URL so that the dependency can be fetched.
    """

    #: The url template for all DepotFiles
    url_template = 'http://{0}.depot.battle.net:1119/{1}.{2}'

    def __init__(self, bytes):
        #: The server the file is hosted on
        self.server = bytes[4:8].strip('\x00 ')

        #: The unique content based hash of the file
        self.hash = bytes[8:].encode('hex')

        #: The extension of the file on the server
        self.type = bytes[0:4]

    @property
    def url(self):
        """ Returns url of the depot file. """
        return self.url_template.format(self.server, self.hash, self.type)

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url


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
        return self[self._key_map[player_name]]

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
        return AttributeDict(self.items())

class Color(object):
    """
    Stores a color name and rgba representation of a color. Individual
    color components can be retrieved with the dot operator::

        color = Color(r=255, g=0, b=0, a=75)
        tuple(color.r,color.g, color.b, color.a) == color.rgba

    You can also create a color by name.

        color = Color('Red')

    Only standard Starcraft colors are supported. ValueErrors will be thrown
    on invalid names or hex values.
    """
    def __init__(self, name=None, r=0, g=0, b=0, a=255):
        if name:
            if name not in COLOR_CODES_INV:
                raise ValueError("Invalid color name: "+name)
            hexstr = COLOR_CODES_INV[name]
            self.r = int(hexstr[0:2],16)
            self.g = int(hexstr[2:4],16)
            self.b = int(hexstr[4:6],16)
            self.a = 255
            self.name = name
        else:
            self.r = r
            self.g = g
            self.b = b
            self.a = a
            if self.hex in COLOR_CODES:
                self.name = COLOR_CODES[self.hex]
            else:
                raise ValueError("Invalid color hex code: "+self.hex)

    @property
    def rgba(self):
        """ Returns a tuple containing the color's (r,g,b,a) """
        return (self.r,self.g,self.b,self.a)

    @property
    def hex(self):
        """The hexadecimal representation of the color"""
        return "{0.r:02X}{0.g:02X}{0.b:02X}".format(self)

    def __str__(self):
        return self.name

def extract_data_file(data_file, archive):
    # Wrap all mpyq related exceptions so they can be distinguished
    # from other sc2reader issues later on.
    try:
        # Some replays tampered with by 3rd party software report
        # block sizes wrong. They can either over report or under
        # report. If they over report a non-compressed file might
        # attempt decompression. If they under report a compressed
        # file might bypass decompression. So do this:
        #
        #  * Force a decompression to catch under reporting
        #  * If that fails, try to process normally
        #  * mpyq doesn't allow you to skip decompression, so fail
        #
        # Refs: arkx/mpyq#12, GraylinKim/sc2reader#102
        try:
            file_data = archive.read_file(data_file, force_decompress=True)
        except Exception as e:
            exc_info = sys.exc_info()
            try:
                file_data = archive.read_file(data_file)
            except Exception as e:
                # raise the original exception
                raise exc_info[1], None, exc_info[2]

        return file_data

    except Exception as e:
        trace = sys.exc_info()[2]
        raise MPQError("Unable to extract file: {0}".format(data_file),e), None, trace

def merged_dict(a, b):
    c = a.copy()
    c.update(b)
    return c

def get_files(path, exclude=list(), depth=-1, followlinks=False, extension=None, **extras):
    # os.walk and os.path.isfile fail silently. We want to be loud!
    if not os.path.exists(path):
        raise ValueError("Location `{0}` does not exist".format(path))

    # If an extension is supplied, use it to do a type check
    if extension:
        type_check = lambda path: os.path.splitext(path)[1][1:].lower() == extension.lower()
    else:
        type_check = lambda n: True

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
    """ Extends the builtin timedelta class. See python docs for more info on
        what capabilities this gives you.
    """

    @property
    def hours(self):
        """ The number of hours in represented. """
        return self.seconds/3600

    @property
    def mins(self):
        """ The number of minutes in excess of the hours. """
        return (self.seconds/60)%60

    @property
    def secs(self):
        """ The number of seconds in excess of the minutes. """
        return self.seconds%60

    def __str__(self):
        if self.hours:
            return "{0:0>2}.{1:0>2}.{2:0>2}".format(self.hours,self.mins,self.secs)
        else:
            return "{0:0>2}.{1:0>2}".format(self.mins,self.secs)
