class ParseError(Exception):
    def __init__(self, message, replay, event, bytes):
        self.message = message
        self.replay = replay
        self.event = event
        self.bytes = bytes