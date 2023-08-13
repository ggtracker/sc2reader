from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sc2reader.events import Event
    from sc2reader.resources import Replay


class EventSecondCorrector:
    """
    In Lotv, the game fps is 22.4, which means that the game time is not
    accurate to the second. But the event.seconds is hardcoded as the fps
    is 16. Since currently the replay build is not passed into the event,
    the safest way to correct the event.seconds is use plugin.
    """

    name = "EventSecondCorrector"

    def handleEvent(self, e: "Event", replay: "Replay"):
        if 34784 <= replay.build:  # lotv replay, adjust time
            e.second = int(e.second * 16 / 22.4)
