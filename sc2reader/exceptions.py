class SC2ReaderError(Exception):
    pass

class MPQError(SC2ReaderError):
    pass

class NoMatchingFilesError(SC2ReaderError):
    pass

class MultipleMatchingFilesError(SC2ReaderError):
    pass

class ReadError(SC2ReaderError):
    def __init__(self, msg, type, code, location, replay=None,  game_events=[], buffer=None):
        self.__dict__.update(locals())
        super(ReadError, self).__init__(msg)

    def __str__(self):
        return "{0}, Type: {1}, Code: {2}".format(self.msg, self.type, self.code)

class ParseError(SC2ReaderError):
    pass

class ProcessError(SC2ReaderError):
    pass

class FileError(SC2ReaderError):
    pass
