# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import binascii
import os
import json
from datetime import timedelta, datetime

from sc2reader.log_utils import loggable
from sc2reader.exceptions import MPQError
from sc2reader.constants import COLOR_CODES, COLOR_CODES_INV


class DepotFile(object):
    """
    :param bytes: The raw bytes representing the depot file

    The DepotFile object parses bytes for a dependency into their components
    and assembles them into a URL so that the dependency can be fetched.
    """

    #: The url template for all DepotFiles
    url_template = "https://{0}-s2-depot.classic.blizzard.com/{1}.{2}"

    def __init__(self, bytes):
        #: The server the file is hosted on
        self.server = bytes[4:8].decode("utf-8").strip("\x00 ")

        # There is no SEA depot, use US instead
        if self.server == "SEA":
            self.server = "US"

        #: The unique content based hash of the file
        self.hash = binascii.b2a_hex(bytes[8:]).decode("utf8")

        #: The extension of the file on the server
        self.type = bytes[0:4].decode("utf8")

    @property
    def url(self):
        """Returns url of the depot file."""
        return self.url_template.format(self.server, self.hash, self.type)

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url


def windows_to_unix(windows_time):
    # This windows timestamp measures the number of 100 nanosecond periods since
    # January 1st, 1601. First we subtract the number of nanosecond periods from
    # 1601-1970, then we divide by 10^7 to bring it back to seconds.
    return int((windows_time - 116444735995904000) / 10 ** 7)


@loggable
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
                self.logger.warn("Invalid color name: " + name)
            hexstr = COLOR_CODES_INV.get(name, "000000")
            self.r = int(hexstr[0:2], 16)
            self.g = int(hexstr[2:4], 16)
            self.b = int(hexstr[4:6], 16)
            self.a = 255
            self.name = name
        else:
            self.r = r
            self.g = g
            self.b = b
            self.a = a
            if self.hex not in COLOR_CODES:
                self.logger.warn("Invalid color hex value: " + self.hex)
            self.name = COLOR_CODES.get(self.hex, self.hex)

    @property
    def rgba(self):
        """
        Returns a tuple containing the color's (r,g,b,a)
        """
        return (self.r, self.g, self.b, self.a)

    @property
    def hex(self):
        """
        The hexadecimal representation of the color
        """
        return "{0.r:02X}{0.g:02X}{0.b:02X}".format(self)

    def __str__(self):
        return self.name


def get_real_type(teams):
    # Special case FFA games and sort outmatched games in ascending order
    team_sizes = [len(team.players) for team in teams]
    if len(team_sizes) > 2 and sum(team_sizes) == len(team_sizes):
        return "FFA"
    else:
        return "v".join(str(size) for size in sorted(team_sizes))


def extract_data_file(data_file, archive):
    def recovery_attempt():
        try:
            return archive.read_file(data_file)
        except Exception:
            return None

    # Wrap all mpyq related exceptions so they can be distinguished
    # from other sc2reader issues later on.
    try:
        # Some replays tampered with by 3rd party software report
        # block sizes wrong. They can either over report or under
        # report. If they over report a non-compressed file might
        # attempt decompression. If they under report a compressed
        # file might bypass decompression. So do this:
        #
        # * Force a decompression to catch under reporting
        # * If that fails, try to process normally
        # * mpyq doesn't allow you to skip decompression, so fail
        #
        # Refs: arkx/mpyq#12, GraylinKim/sc2reader#102
        try:
            file_data = archive.read_file(data_file, force_decompress=True)
        except Exception as e:
            file_data = recovery_attempt()
            if file_data is None:
                raise

        return file_data

    except Exception as e:
        # Python2 and Python3 handle wrapped exceptions with old tracebacks in incompatible ways
        # Python3 handles it by default and Python2's method won't compile in python3
        # Since the underlying traceback isn't important to most people, don't expose it anymore
        raise MPQError("Unable to extract file: {0}".format(data_file), e)


def get_files(
    path, exclude=list(), depth=-1, followlinks=False, extension=None, **extras
):
    """
    Retrieves files from the given path with configurable behavior.

    :param path: Path to search for files
    :param depth: Limits the depth of the search. -1 = Unlimited
    :param followLinks: Enables the search to follow links.
    :param exclude: Excludes subdirectories with names in this list.
    :param extension: Restricts results to files matching the given extension."
    """
    # os.walk and os.path.isfile fail silently. We want to be loud!
    if not os.path.exists(path):
        raise ValueError("Location `{0}` does not exist".format(path))

    # If an extension is supplied, use it to do a type check
    if extension:
        type_check = (
            lambda path: os.path.splitext(path)[1][1:].lower() == extension.lower()
        )
    else:
        type_check = lambda n: True

    # os.walk can't handle file paths, only directories
    if os.path.isfile(path):
        if type_check(path):
            yield path
        else:
            pass  # return and halt the generator

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
        """
        The number of hours in represented.
        """
        return self.seconds // 3600

    @property
    def mins(self):
        """
        The number of minutes in excess of the hours.
        """
        return self.seconds // 60 % 60

    @property
    def secs(self):
        """
        The number of seconds in excess of the minutes.
        """
        return self.seconds % 60

    def __str__(self):
        if self.hours:
            return "{0:0>2}.{1:0>2}.{2:0>2}".format(self.hours, self.mins, self.secs)
        else:
            return "{0:0>2}.{1:0>2}".format(self.mins, self.secs)


class JSONDateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return json.JSONEncoder.default(self, obj)


def toJSON(replay, **user_options):
    options = dict(cls=JSONDateEncoder)
    options.update(user_options)
    return json.dumps(toDict(replay), **options)


def toDict(replay):
    # Build observers into dictionary
    observers = list()
    for observer in replay.observers:
        messages = list()
        for message in getattr(observer, "messages", list()):
            messages.append(
                {
                    "time": message.time.seconds,
                    "text": message.text,
                    "is_public": message.to_all,
                }
            )
        observers.append(
            {
                "name": getattr(observer, "name", None),
                "pid": getattr(observer, "pid", None),
                "messages": messages,
            }
        )

    # Build players into dictionary
    players = list()
    for player in replay.players:
        messages = list()
        for message in player.messages:
            messages.append(
                {
                    "time": message.time.seconds,
                    "text": message.text,
                    "is_public": message.to_all,
                }
            )
        players.append(
            {
                "avg_apm": getattr(player, "avg_apm", None),
                "color": player.color.__dict__ if hasattr(player, "color") else None,
                "handicap": getattr(player, "handicap", None),
                "name": getattr(player, "name", None),
                "pick_race": getattr(player, "pick_race", None),
                "pid": getattr(player, "pid", None),
                "play_race": getattr(player, "play_race", None),
                "result": getattr(player, "result", None),
                "type": getattr(player, "type", None),
                "uid": getattr(player, "uid", None),
                "url": getattr(player, "url", None),
                "messages": messages,
            }
        )

    # Consolidate replay metadata into dictionary
    return {
        "region": getattr(replay, "region", None),
        "map_name": getattr(replay, "map_name", None),
        "file_time": getattr(replay, "file_time", None),
        "filehash": getattr(replay, "filehash", None),
        "unix_timestamp": getattr(replay, "unix_timestamp", None),
        "date": getattr(replay, "date", None),
        "utc_date": getattr(replay, "utc_date", None),
        "speed": getattr(replay, "speed", None),
        "category": getattr(replay, "category", None),
        "type": getattr(replay, "type", None),
        "is_ladder": getattr(replay, "is_ladder", False),
        "is_private": getattr(replay, "is_private", False),
        "filename": getattr(replay, "filename", None),
        "file_time": getattr(replay, "file_time", None),
        "frames": getattr(replay, "frames", None),
        "build": getattr(replay, "build", None),
        "release": getattr(replay, "release_string", None),
        "game_fps": getattr(replay, "game_fps", None),
        "game_length": getattr(getattr(replay, "game_length", None), "seconds", None),
        "players": players,
        "observers": observers,
        "real_length": getattr(getattr(replay, "real_length", None), "seconds", None),
        "real_type": getattr(replay, "real_type", None),
        "time_zone": getattr(replay, "time_zone", None),
        "versions": getattr(replay, "versions", None),
    }
