import aiomysql
from os import getenv

class Start:
    """
    Start class containing the `.start()` method for
    connecting to the database and creating the
    necessary tables if needed.
    """
    async def start(self) -> bool:
        """
        Loads the LiveLaunch database.
        """
        self.started = True
        # Connect
        self.pool = await aiomysql.create_pool(
            host=self._host,
            user=self._user,
            password=getenv('DB_PWD'),
            db=self._database,
            autocommit=True
        )
        with await self.pool as con:
            async with con.cursor() as cur:
                # Create table for storing guild settings
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS enabled_guilds (
                    guild_id BIGINT UNSIGNED PRIMARY KEY,
                    channel_id BIGINT UNSIGNED DEFAULT NULL,
                    webhook_url TEXT DEFAULT NULL,
                    scheduled_events TINYINT UNSIGNED DEFAULT 0,
                    se_launch TINYINT UNSIGNED DEFAULT 1,
                    se_event TINYINT UNSIGNED DEFAULT 1,
                    se_no_url TINYINT UNSIGNED DEFAULT 0,
                    news_channel_id BIGINT UNSIGNED DEFAULT NULL,
                    news_webhook_url TEXT DEFAULT NULL,
                    notification_channel_id BIGINT UNSIGNED DEFAULT NULL,
                    notification_webhook_url TEXT DEFAULT NULL,
                    notification_launch TINYINT UNSIGNED DEFAULT 0,
                    notification_event TINYINT UNSIGNED DEFAULT 0,
                    notification_t0_change TINYINT UNSIGNED DEFAULT 0,
                    notification_tbd TINYINT UNSIGNED DEFAULT 0,
                    notification_tbc TINYINT UNSIGNED DEFAULT 0,
                    notification_go TINYINT UNSIGNED DEFAULT 0,
                    notification_liftoff TINYINT UNSIGNED DEFAULT 0,
                    notification_hold TINYINT UNSIGNED DEFAULT 0,
                    notification_end_status TINYINT UNSIGNED DEFAULT 0,
                    notification_scheduled_event TINYINT UNSIGNED DEFAULT 0,
                    notification_button_fc TINYINT UNSIGNED DEFAULT 1,
                    notification_button_g4l TINYINT UNSIGNED DEFAULT 1,
                    notification_button_sln TINYINT UNSIGNED DEFAULT 1
                    )
                    """
                )
                # Create table for storing agencies
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ll2_agencies (
                    agency_id SMALLINT UNSIGNED PRIMARY KEY,
                    name TEXT DEFAULT NULL,
                    logo_url TEXT DEFAULT NULL
                    )
                    """
                )
                # Create table for storing filtered agencies per guild
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ll2_agencies_filter (
                    guild_id BIGINT UNSIGNED,
                    agency_id SMALLINT UNSIGNED,
                    PRIMARY KEY (guild_id, agency_id),
                    FOREIGN KEY (guild_id) REFERENCES enabled_guilds(guild_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (agency_id) REFERENCES ll2_agencies(agency_id)
                    )
                    """
                )
                # Create table for storing LL2 events their details
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ll2_events (
                    ll2_id VARCHAR(36) PRIMARY KEY,
                    agency_id SMALLINT UNSIGNED DEFAULT NULL,
                    name TEXT DEFAULT NULL,
                    status TINYINT DEFAULT NULL,
                    description TEXT DEFAULT NULL,
                    url TEXT DEFAULT NULL,
                    image_url TEXT DEFAULT NULL,
                    start DATETIME DEFAULT NULL,
                    end DATETIME DEFAULT NULL,
                    webcast_live TINYINT DEFAULT 0,
                    slug TEXT DEFAULT NULL,
                    flightclub TINYINT UNSIGNED DEFAULT 0,
                    FOREIGN KEY (agency_id) REFERENCES ll2_agencies(agency_id)
                    )
                    """
                )
                # Create table for storing news sites
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS news_sites (
                    news_site_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    news_site_name TEXT
                    )
                    """
                )
                # Create table for storing filtered news sites per guild
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS news_filter (
                    guild_id BIGINT UNSIGNED,
                    news_site_id SMALLINT UNSIGNED,
                    PRIMARY KEY (guild_id, news_site_id),
                    FOREIGN KEY (guild_id) REFERENCES enabled_guilds(guild_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (news_site_id) REFERENCES news_sites(news_site_id)
                    )
                    """
                )
                # Create table for storing the amount of minutes countdown notifications
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notification_countdown (
                    guild_id BIGINT UNSIGNED,
                    minutes SMALLINT UNSIGNED,
                    PRIMARY KEY (guild_id, minutes),
                    FOREIGN KEY (guild_id) REFERENCES enabled_guilds(guild_id)
                        ON DELETE CASCADE
                    )
                    """
                )
                # Create table for storing Discord scheduled event IDs
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scheduled_events (
                    scheduled_event_id BIGINT UNSIGNED PRIMARY KEY,
                    guild_id BIGINT UNSIGNED DEFAULT NULL,
                    ll2_id VARCHAR(36) DEFAULT NULL,
                    FOREIGN KEY (guild_id) REFERENCES enabled_guilds(guild_id),
                    FOREIGN KEY (ll2_id) REFERENCES ll2_events(ll2_id)
                        ON DELETE CASCADE
                    )
                    """
                )
                # Create table for storing sent news articles
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sent_news (
                    snapi_id MEDIUMINT UNSIGNED PRIMARY KEY,
                    datetime DATETIME DEFAULT NULL
                    )
                    """
                )
                # Create table for storing sent live streams
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sent_streams (
                    yt_vid_id TEXT,
                    datetime DATETIME DEFAULT NULL
                    )
                    """
                )
