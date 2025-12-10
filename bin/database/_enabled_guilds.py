import aiomysql
from discord.utils import MISSING
from typing import AsyncGenerator

class EnabledGuilds:
    """
    Enabled & settings table.
    """
    async def enabled_guilds_add(
        self,
        guild_id: int,
        channel_id: int | None = None,
        webhook_url: str | None = None,
        scheduled_events: int = 0,
        news_channel_id: int | None = None,
        news_webhook_url: str | None = None,
        notification_channel_id: int | None = None,
        notification_webhook_url: str | None = None
    ) -> None:
        """
        Adds an entry in the `enabled_guilds`
        table of the LiveLaunch database.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        channel_id : int or None, default: None
            Discord channel ID.
        webhook_url : str or None, default: None
            Discord webhook URL.
        scheduled_events : int, default: 0
            Maximum amount of events.
        news_channel_id : int or None, default: None
            Discord channel ID
            for sending news.
        news_webhook_url : str or None, default: None
            Discord webhook URL
            for sending news.
        notification_channel_id : int or None, default: None
            Discord channel ID for
            sending notifications.
        notification_webhook_url : str or None, default: None
            Discord webhook URL for
            sending notifications.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO enabled_guilds
                (
                    guild_id,
                    channel_id,
                    webhook_url,
                    scheduled_events,
                    news_channel_id,
                    news_webhook_url,
                    notification_channel_id,
                    notification_webhook_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    guild_id,
                    channel_id,
                    webhook_url,
                    scheduled_events,
                    news_channel_id,
                    news_webhook_url,
                    notification_channel_id,
                    notification_webhook_url
                )
            )

    async def enabled_guilds_remove(self, guild_id: int) -> None:
        """
        Removes an entry in the `enabled_guilds`
        table of the LiveLaunch database.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM enabled_guilds
                WHERE guild_id=%s
                """,
                (guild_id,)
            )

    async def enabled_guilds_check(self, guild_id: int) -> bool:
        """
        Check if a guild has any settings.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.

        Returns
        -------
        exists : bool
            Whether or not the
            guild has any settings.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*)
                FROM enabled_guilds
                WHERE guild_id=%s
                """,
                (guild_id,)
            )
            return (await cur.fetchone())[0] != 0

    async def enabled_guilds_news_iter(
        self
    ) -> AsyncGenerator[tuple[int, str]]:
        """
        Iterates over the guilds
        that enabled news.

        Yields
        ------
        AsyncGenerator[tuple[
            guild_id : int,
            news_webhook_url : str
        ]]
            Yields the guild_id,
            news_webhook_url.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT guild_id, news_webhook_url
                FROM enabled_guilds
                WHERE news_webhook_url IS NOT NULL
                """
            )
            async for row in cur:
                yield row

    async def enabled_guilds_scheduled_events_iter(
        self
    ) -> AsyncGenerator[tuple[int]]:
        """
        Go over every row in the
        `enabled_guilds` table and
        yield the guild's ID if
        scheduled events are enabled
        and the maximum amount isn't
        reached yet.

        Yields
        ------
        AsyncGenerator[tuple[
            guild_id : int,
            amount : int
        ]]
            Yields Discord Guild ID
            when it scheduled events
            are enabled and the amount
            of events that can be
            created before reaching
            the guild's maximum amount.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT guild_id, scheduled_events
                FROM enabled_guilds WHERE
                scheduled_events > 0
                """
            )
            async for row in cur:
                yield row

    async def enabled_guilds_webhook_iter(
        self
    ) -> AsyncGenerator[tuple[int, str]]:
        """
        Go over every row in the
        `enabled_guilds` table and
        yield the guild's webhook if it exist.

        Yields
        ------
        AsyncGenerator[tuple[
            guild_id : int,
            webhook_url : str
        ]]
            Yields Discord Guild ID and
            webhook url when it exists.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT guild_id, webhook_url
                FROM enabled_guilds
                WHERE webhook_url IS NOT NULL
                """
            )
            async for row in cur:
                yield row

    async def enabled_guilds_get(
        self,
        guild_id: int
    ) -> dict[str, int | str] | None:
        """
        Retrieves an entry from the `enabled_guilds`
        table of the LiveLaunch database.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.

        Returns
        -------
        dict[
            channel_id : int,
            webhook_url : str,
            scheduled_events : int,
            se_launch : int,
            se_event : int,
            se_no_url : int,
            news_channel_id : int,
            news_webhook_url : str,
            news_include_exclude : int,
            notification_channel_id : int,
            notification_webhook_url : str,
            notification_launch : int,
            notification_event : int,
            notification_liftoff : int,
            notification_hold : int,
            notification_deploy : int,
            notification_end_status : int,
            notification_scheduled_event : int
            ] or None
            Returns a row with the guild's data
            if it exists, otherwise None.
        """
        async with (
            self.pool.acquire() as con,
            con.cursor(aiomysql.DictCursor) as cur
        ):
            await cur.execute(
                """
                SELECT *
                FROM enabled_guilds
                WHERE guild_id=%s
                """,
                (guild_id,)
            )
            return await cur.fetchone()

    async def enabled_guilds_edit(
        self, guild_id: int,
        channel_id: int | None = MISSING,
        webhook_url: str | None = MISSING,
        scheduled_events: int | None = None,
        news_channel_id: int | None = MISSING,
        news_webhook_url: str | None = MISSING,
        notification_channel_id: int | None = MISSING,
        notification_webhook_url: str | None = MISSING
    ) -> None:
        """
        Modifies an entry in the `enabled_guilds`
        table of the LiveLaunch database.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        channel_id : int or None, default: `MISSING`
            Discord channel ID.
        webhook_url : str or None, default: `MISSING`
            Discord webhook URL.
        scheduled_events : int or None, default: None
            Maximum amount of scheduled events.
        news_channel_id : int or None, default: `MISSING`
            Discord channel ID
            for sending news.
        news_webhook_url : str or None, default: `MISSING`
            Discord webhook URL
            for sending news.
        notification_channel_id : int or None, default: `MISSING`
            Discord channel ID for
            sending notifications.
        notification_webhook_url : str or None, default: `MISSING`
            Discord webhook URL for
            sending notifications.
        """
        cols: list[str] = []
        args: list[int | str | None] = []
        # Update channel ID and webhook URL if given
        if (channel_id and webhook_url) is not MISSING:
            cols.append('channel_id=%s')
            args.append(channel_id)
            cols.append('webhook_url=%s')
            args.append(webhook_url)
        # Update scheduled_events if given
        if scheduled_events is not None:
            cols.append('scheduled_events=%s')  
            args.append(scheduled_events)
        # Update news channel ID and news webhook URL if given
        if (news_channel_id and news_webhook_url) is not MISSING:
            cols.append('news_channel_id=%s')
            args.append(news_channel_id)
            cols.append('news_webhook_url=%s')
            args.append(news_webhook_url)
        # Update notification channel ID and news webhook URL if given
        if (
            notification_channel_id and notification_webhook_url
        ) is not MISSING:
            cols.append('notification_channel_id=%s')
            args.append(notification_channel_id)
            cols.append('notification_webhook_url=%s')
            args.append(notification_webhook_url)
        # Add guild ID to the arguments
        args.append(guild_id)
        # Update
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE enabled_guilds
                SET {', '.join(cols)}
                WHERE guild_id=%s
                """,
                args
            )

    async def enabled_guilds_clean(self) -> None:
        """
        Cleans up empty Guild entries in
        the `enabled_guilds` table of the
        LiveLaunch database.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                DELETE
                    eg
                FROM
                    enabled_guilds AS eg
                LEFT JOIN
                    scheduled_events AS se
                    ON se.guild_id = eg.guild_id
                WHERE
                    se.guild_id IS NULL
                    AND
                    eg.channel_id IS NULL
                    AND
                    eg.webhook_url IS NULL
                    AND
                    (
                        eg.scheduled_events = 0
                        OR
                        (eg.se_launch = 0 AND eg.se_event = 0)
                    )
                    AND
                    eg.news_channel_id IS NULL
                    AND
                    eg.news_webhook_url IS NULL
                    AND
                    eg.notification_channel_id IS NULL
                    AND
                    eg.notification_webhook_url IS NULL
                """
            )

    async def enabled_guilds_unused_notification_iter(
        self
    ) -> AsyncGenerator[tuple[int, str]]:
        """
        Get all Guilds with unused
        notification webhooks.

        Yields
        ------
        AsyncGenerator[tuple[
            guild_id : int,
            notification_webhook_url : str
        ]]
            Yields the Guild ID and
            notification webhook URL.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    eg.guild_id,
                    eg.notification_webhook_url
                FROM
                    enabled_guilds AS eg
                WHERE
                    eg.notification_channel_id IS NOT NULL
                    AND
                    eg.notification_webhook_url IS NOT NULL
                    AND NOT
                    (
                        (
                            (
                                eg.notification_launch
                                OR
                                eg.notification_event
                            )
                            AND
                            (
                                eg.notification_t0_change
                                OR
                                (
                                    SELECT
                                        COUNT(*) > 0
                                    FROM
                                        notification_countdown AS nc
                                    WHERE
                                        nc.guild_id = eg.guild_id
                                )
                            )
                        )
                        OR
                        (
                            eg.notification_tbd
                            OR
                            eg.notification_tbc
                            OR
                            eg.notification_go
                            OR
                            eg.notification_liftoff
                            OR
                            eg.notification_hold
                            OR
                            eg.notification_deploy
                            OR
                            eg.notification_end_status
                        )
                    )
                """
            )
            async for row in cur:
                yield row
