from ._enabled_guilds import EnabledGuilds
from ._ll2_events import LL2Events
from ._news_sites import News
from ._scheduled_events import ScheduledEvents
from ._sent_media import SentMedia
from ._start import Start

class Database(
    EnabledGuilds,
    LL2Events,
    News,
    ScheduledEvents,
    SentMedia,
    Start
):
    """
    Database methods for LiveLaunch.
    """
    def __init__(self):
        self._host = 'server.juststephen.com'
        self._user = 'root'
        self._database = 'LiveLaunch'
        self.started = False
