from ._enabled_guilds import EnabledGuilds
from ._ll2_agencies import LL2Agencies
from ._ll2_events import LL2Events
from ._news_sites import News
from ._notification_countdown import NotificationCountdown
from ._notification_settings import NotificationSettings
from ._notification_status import NotificationStatus
from ._scheduled_events import ScheduledEvents
from ._sent_media import SentMedia
from ._start import Start

class Database(
    EnabledGuilds,
    LL2Agencies,
    LL2Events,
    News,
    NotificationCountdown,
    NotificationSettings,
    NotificationStatus,
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
