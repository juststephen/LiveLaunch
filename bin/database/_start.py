import aiomysql
from os import getenv

class Start:
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
                # Create table for storing guild settings and webhook if needed
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS enabled_guilds (
                    guild_id BIGINT UNSIGNED PRIMARY KEY,
                    channel_id BIGINT UNSIGNED DEFAULT NULL,
                    webhook_url TEXT DEFAULT NULL,
                    scheduled_events TINYINT UNSIGNED DEFAULT 0,
                    news_channel_id BIGINT UNSIGNED DEFAULT NULL,
                    news_webhook_url TEXT DEFAULT NULL
                    )
                    """
                )
                # Create table for storing LL2 events their details
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ll2_events (
                    ll2_id VARCHAR(36) PRIMARY KEY,
                    name TEXT DEFAULT NULL,
                    description TEXT DEFAULT NULL,
                    url TEXT DEFAULT NULL,
                    image_url TEXT DEFAULT NULL,
                    start TEXT DEFAULT NULL,
                    end TEXT DEFAULT NULL,
                    webcast_live TINYINT DEFAULT 0
                    )
                    """
                )
                # Create table for storing filtered news sites per Guild
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
                # Create table for storing news sites
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS news_sites (
                    news_site_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    news_site_name TEXT
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
                    )
                    """
                )
                # Create table for storing sent news articles
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sent_news (
                    snapi_id MEDIUMINT UNSIGNED PRIMARY KEY,
                    datetime TEXT DEFAULT NULL
                    )
                    """
                )
                # Create table for storing sent live streams
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sent_streams (
                    yt_vid_id TEXT,
                    datetime TEXT DEFAULT NULL
                    )
                    """
                )
