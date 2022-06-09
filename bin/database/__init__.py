from ._enabled_guilds import EnabledGuilds
from ._ll2_agencies import LL2Agencies
from ._ll2_agencies_filter import LL2AgenciesFilter
from ._ll2_events import LL2Events
from ._ll2_events_next import LL2EventsNext
from ._news_sites import News
from ._news_sites_filter import NewsFilter
from ._notification_countdown import NotificationCountdown
from ._notification_iter import NotificationIter
from ._notification_settings import NotificationSettings
from ._scheduled_events import ScheduledEvents
from ._scheduled_events_settings import ScheduledEventsSettings
from ._sent_media import SentMedia
from ._start import Start

class Database(
    EnabledGuilds,
    LL2Agencies,
    LL2AgenciesFilter,
    LL2Events,
    LL2EventsNext,
    News,
    NewsFilter,
    NotificationCountdown,
    NotificationIter,
    NotificationSettings,
    ScheduledEvents,
    ScheduledEventsSettings,
    SentMedia,
    Start
):
    """
    Database methods for LiveLaunch.
    """
    def __init__(self) -> None:
        self._host = 'server.juststephen.com'
        self._user = 'root'
        self._database = 'LiveLaunch'
        self.started = False
        # Initialize filter classes
        LL2AgenciesFilter.__init__(self)
        NewsFilter.__init__(self)
