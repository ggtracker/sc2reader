class SC2ReaderError(Exception):
    pass


class SC2ReaderLocalizationError(SC2ReaderError):
    pass


class CorruptTrackerFileError(SC2ReaderError):
    pass


class MPQError(SC2ReaderError):
    pass


class NoMatchingFilesError(SC2ReaderError):
    pass


class MultipleMatchingFilesError(SC2ReaderError):
    pass


class ReadError(SC2ReaderError):
    def __init__(self, msg, type, location, replay=None, game_events=[], buffer=None):
        self.__dict__.update(locals())
        super().__init__(msg)

    def __str__(self):
        return f"{self.msg}, Type: {self.type}"


class ParseError(SC2ReaderError):
    pass


class ProcessError(SC2ReaderError):
    pass


class FileError(SC2ReaderError):
    pass
