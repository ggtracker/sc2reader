class InitGameEvent:
    name = "InitGame"


class EndGameEvent:
    name = "EndGame"


class PluginExit:
    name = "PluginExit"

    def __init__(self, plugin, code=0, details=None):
        self.plugin = plugin
        self.code = code
        self.details = details or {}
