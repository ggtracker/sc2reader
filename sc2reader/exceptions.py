class SC2ReaderError(Exception):
    pass

class NoMatchingFilesError(SC2ReaderError):
    pass

class MutipleMatchingFilesError(SC2ReaderError):
    pass

class ReadError(SC2ReaderError):
    def __init__(self, msg, type, code, location, replay=None,  game_events=[], buffer=None):
        self.__dict__.update(locals())
        super(ReadError, self).__init__(msg)

class ProcessError(SC2ReaderError):
    pass

class FileError(SC2ReaderError):
    pass
