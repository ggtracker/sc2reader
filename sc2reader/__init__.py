# -*- coding: utf-8 -*-
"""
    sc2reader
    ----------

    A Starcraft II replay parsing library intended to promote innovation in
    Starcraft tools and communities. Eventually, it will cover all official
    releases and dump easily to JSON for inter-language portability.

    sc2reader has been carefully written for clarity to serve as a starting
    point for those who want to write their own parsers, potentially in other
    languages for native access.

    Enjoy.

    :copyright: (c) 2011 Graylin Kim
    :license: MIT, See LICENSE.txt for details
"""
from __future__ import absolute_import

__version__ = '0.3.2'


#System imports
import os

#PyPi imports
import mpyq

#Package imports
from sc2reader import config, objects, utils, processors, exceptions


class Reader(object):
    """ The SC2Reader class acts as a factory class for replay objects. The
        class accepts a key=value list of options to override defaults (see
        config.py) and exposes a very simple read/configure interface and
        orchestrates the replay build process.
    """

    def __init__(self, **user_options):
        """ The constructor makes a copy of the default_options to make sure the
            option configuration doesn't propagate back to the default_options.
            It should support any arbitrary number of different Reader objects.
        """
        self.options = config.default_options.copy()
        self.configure(**user_options)

    def configure(self, **options):
        self.options.update(options)

    def read(self, location, **user_options):
        """ Read indicated file or recursively read matching files from the
            specified directory. Returns a replay or a list of replays depending
            on the context.
        """

        # Base the options off a copy to leave the Reader options uneffected.
        options = self.options.copy()
        options.update(user_options)

        # The directory option allows users to specify file locations relative
        # to a location other than the present working directory by joining the
        # location with the directory of their choice.
        if options.directory:
            location = os.path.join(options.directory, location)

        # When passed a directory as the location, the Reader recursively builds
        # a list of replays to return using the utils.get_files function. This
        # function respects the following arguments:
        #   * depth: The maximum depth to traverse. Defaults to unlimited (-1)
        #   * follow_symlinks: Boolean for following symlinks. Defaults to True
        #   * exclude_dirs: A list of directory names to skip while recursing
        #   * incldue_regex: A regular expression rule which all returned file
        #       names must match. Defaults to None
        #
        replays, files = list(), utils.get_files(location, **options)

        # If no files are found, it could be for a variety of reasons
        # raise a NoMatchingFilesError to alert them to the situation
        if not files:
            raise exceptions.NoMatchingFilesError()

        for location in files:
            if options.verbose: print "Reading: %s" % location

            with open(location, 'rb') as replay_file:
                replays.append(self.make_replay(replay_file, **options))

        return replays

    def make_replay(self, replay_file, **options):
        options = utils.AttributeDict(options)

        # The Replay constructor scans the header of the replay file for
        # the build number and stores the options for later use. The
        # options are copied so subsequent option changes are isolated.
        replay_file.seek(0)
        replay = objects.Replay(replay_file, **options.copy())

        # .SC2Replay files are written in Blizzard's MPQ Archive format.
        # The format stores a header which contains a block table that
        # specifies the location of each encrypted file.
        #
        # Unfortunately, some replay sites modify the replay contents to
        # add messages promoting their sites without updating the header
        # correctly. The listfile option(hack) lets us bypass this issue
        # by specifying the files we want instead of generating a list.
        #
        # In order to wrap mpyq exceptions we have to do this try hack.
        try:
            replay_file.seek(0)
            archive = mpyq.MPQArchive(replay_file, listfile=False)
        except KeyboardInterrupt: raise
        except:
            raise exceptions.MPQError("Unable to construct the MPQArchive")

        # These files are configured for either full or partial parsing
        for file in options.files:

            # To wrap mpyq exceptions we have to do this try hack.
            try:
                # Handle the tampering with the message.events file that some sites do
                if file == 'replay.message.events':
                    try:
                        filedata = archive.read_file(file, force_decompress=True)
                    except IndexError as e:
                        # Catch decompression errors
                        if str(e) == "string index out of range":
                            filedata = archive.read_file(file, force_decompress=False)
                        else:
                            raise
                else:
                    filedata = archive.read_file(file)
            except KeyboardInterrupt: raise
            except:
                raise exceptions.MPQError("Unable to extract file: {0}".format(file))

            # For each file, we build a smart buffer object from the
            # utf-8 encoded bitstream that mpyq extracts.
            buffer = utils.ReplayBuffer(filedata)

            # Each version of Starcraft slightly modifies some portions
            # of the format for some files. To work with this, the
            # config file has a nested lookup structure of
            # [build][file]=>reader which returns the appropriate reader
            #
            # TODO: Different versions also have different data mappings
            #       sc2reader doesn't yet handle this difficulty.
            #
            # Readers use the type agnostic __call__ interface so that
            # they can be implemented as functions or classes as needed.
            #
            # Readers return the extracted information from the buffer
            # object which gets stored into the raw data dict for later
            # use in post processing because correct interpretation of
            # the information often requires data from other files.
            reader = config.readers[replay.build][file]
            reference_name = '_'.join(file.split('.')[1:])
            replay.raw[reference_name] = reader(buffer, replay)

        # Now that the replay has been loaded with the "raw" data from
        # the archive files we run the system level post processors to
        # organize the data into a cross referenced data structure.
        #
        # After system level processors have run, call each of the post
        # processors provided by the user. This would be a good place to
        # convert the object to a serialized json string for cross
        # language processes or add custom attributes.
        #
        # TODO: Maybe we should switch this to a hook based architecture
        #       Needs to be able to load "contrib" type processors..
        for process in [processors.Full]+options.processors:
            replay = process(replay)

        return replay

    def read_file(self, file_in, **user_options):
        # Support file-like objects (with a read method)
        if hasattr(file_in, 'read') and hasattr(file_in, 'seek'):

            # Base the options off a copy to leave the Reader options unaffected.
            options = self.options.copy()
            options.update(user_options)

            return self.make_replay(file_in, **options)

        # Also support filepath strings
        else:
            replays = self.read(file_in, **user_options)

            # While normal usage would suggest passing in only filenames, it is
            # possible that directories could be passed in. Don't fail silently!
            if len(replays) > 1:
                raise exceptions.MultipleMatchingFilesError(replays)

            # Propogate the replay in a singular context
            return replays[0] if len(replays) > 0 else None


"""sc2reader uses a default SC2Reader class instance to provide a package level
interface to its functionality. The package level interface presents the same
functional interface, it just saves the hassle of creating the class object.
"""
__defaultReader = Reader()

def read_file(location, **user_options):
    return __defaultReader.read_file(location, **user_options)

def read(location, **user_options):
    return __defaultReader.read(location, **user_options)

def configure(**options):
    config.default_options.update(options)

def reset():
    __defaultReader = Reader()
