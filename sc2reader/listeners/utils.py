from sc2reader import log_utils

class ListenerBase(object):
    def __init__(self):
        self.logger = log_utils.get_logger(self.__class__)

    def setup(self, replay):
        pass

    def accepts(self, event):
        return true

    def __call__(self, event, replay):
        raise NotImplementedError()

    def finish(self, replay):
        pass
