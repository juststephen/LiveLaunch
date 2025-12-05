import aiomysql
import logging
from os import getenv
from types import TracebackType
from typing import Literal, Self

logger = logging.getLogger(__name__)

class Start:
    """
    Class containing the database pool connect and disconnect logic.
    """
    async def start(self) -> bool:
        """
        Creates the LiveLaunch database connection pool
        and required tables if they don't exist yet.

        Examples
        --------
        >>> async with db:
        ...    await db.start()
        """
        # Connect
        self.pool = await aiomysql.create_pool(
            host=self._host,
            user=self._user,
            password=getenv('DB_PWD'),
            db=self._database,
            autocommit=True
        )
        async with self.pool.acquire() as con, con.cursor() as cur:
            # Create table for storing guilds
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS guilds (
                guild_id BIGINT UNSIGNED PRIMARY KEY
                )
                """
            )
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
                agencies_include_exclude TINYINT UNSIGNED DEFAULT 0,
                news_channel_id BIGINT UNSIGNED DEFAULT NULL,
                news_webhook_url TEXT DEFAULT NULL,
                news_include_exclude TINYINT UNSIGNED DEFAULT 0,
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
                notification_deploy TINYINT UNSIGNED DEFAULT 0,
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
                news_site_name TEXT,
                logo_url TEXT DEFAULT NULL
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

    async def __aenter__(self) -> Self:
        """
        Enter asynchronous context manager.

        Returns
        -------
        self : Database
            Returns self.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc_value: Exception | None,
        traceback: TracebackType | None
    ) -> Literal[True] | None:
        """
        Exit asynchronous context manager.
        Closes the database connection pool.

        Parameters
        ----------
        exc_type : type[Exception] or None
            Exception type.
        exc_value : Exception or None
            Exception value.
        traceback : TracebackType or None
            Exception traceback.

        Returns
        -------
        exc_handled : Literal[True] or None
            True when exception handled, otherwise None.
        """
        # Close pool
        if hasattr(self, 'pool'):
            self.pool.close()
            await self.pool.wait_closed()
        # Surpress exception if the database is down and log it
        if exc_type is aiomysql.OperationalError:
            logger.critical(
                f'Cannot connect to the database, exiting: {exc_value}'
            )
            return True
