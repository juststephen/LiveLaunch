import aiomysql

from ._missing import MISSING

class EnabledGuilds:
    """
    Enabled & settings table.
    """
    async def enabled_guilds_add(
        self,
        guild_id: int,
        channel_id: int = None,
        webhook_url: str = None,
        scheduled_events: int = 0,
        news_channel_id: int = None,
        news_webhook_url: str = None,
        notification_channel_id: int = None,
        notification_webhook_url: str = None
    ) -> None:
        """
        Adds an entry in the `enabled_guilds`
        table of the LiveLaunch database.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        channel_id : int, default: None
            Discord channel ID.
        webhook_url : str, default: None
            Discord webhook URL.
        scheduled_events : int, default: 0
            Maximum amount of events.
        news_channel_id : int, default: None
            Discord channel ID
            for sending news.
        news_webhook_url : str, default: None
            Discord webhook URL
            for sending news.
        notification_channel_id : int, default: None
            Discord channel ID for
            sending notifications.
        notification_webhook_url : str, default: None
            Discord webhook URL for
            sending notifications.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
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
        with await self.pool as con:
            async with con.cursor() as cur:
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
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM enabled_guilds
                    WHERE guild_id=%s
                    """,
                    (guild_id,)
                )
                return (await cur.fetchone())[0] != 0

    async def enabled_guilds_news_iter(self) -> tuple[int, str]:
        """
        Iterates over the guilds
        that enabled news.

        Yields
        ------
        tuple[
            guild_id : int,
            news_webhook_url : str
        ]
            Yields the guild_id,
            news_webhook_url.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT guild_id, news_webhook_url
                    FROM enabled_guilds
                    WHERE news_webhook_url IS NOT NULL
                    """
                )
                async for row in cur:
                    yield row

    async def enabled_guilds_scheduled_events_iter(self) -> tuple[int]:
        """
        Go over every row in the
        `enabled_guilds` table and
        yield the guild's ID if
        scheduled events are enabled
        and the maximum amount isn't
        reached yet.

        Yields
        ------
        tuple[
            guild_id : int,
            amount : int
        ]
            Yields Discord Guild ID
            when it scheduled events
            are enabled and the amount
            of events that can be
            created before reaching
            the guild's maximum amount.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT guild_id, scheduled_events
                    FROM enabled_guilds WHERE
                    scheduled_events > 0
                    """
                )
                async for row in cur:
                    yield row

    async def enabled_guilds_webhook_iter(self) -> tuple[int, str]:
        """
        Go over every row in the
        `enabled_guilds` table and
        yield the guild's webhook if it exist.

        Yields
        ------
        tuple[
            guild_id : int,
            webhook_url : str
        ]
            Yields Discord Guild ID and
            webhook url when it exists.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
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
    ) -> dict[str, int or str] or None:
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
            news_channel_id : int,
            news_webhook_url : str,
            notification_channel_id : int,
            notification_webhook_url : str
            ] or None
            Returns a row with the guild's data
            if it exists, otherwise None.
        """
        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
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
        channel_id: int = MISSING,
        webhook_url: str = MISSING,
        scheduled_events: int = None,
        news_channel_id: int = MISSING,
        news_webhook_url: str = MISSING,
        notification_channel_id: int = MISSING,
        notification_webhook_url: str = MISSING
    ) -> None:
        """
        Modifies an entry in the `enabled_guilds`
        table of the LiveLaunch database.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        channel_id : int, default: `MISSING`
            Discord channel ID.
        webhook_url : str, default: `MISSING`
            Discord webhook URL.
        scheduled_events : int, default: None
            Maximum amount of scheduled events.
        news_channel_id : int, default: `MISSING`
            Discord channel ID
            for sending news.
        news_webhook_url : str, default: `MISSING`
            Discord webhook URL
            for sending news.
        notification_channel_id : int, default: `MISSING`
            Discord channel ID for
            sending notifications.
        notification_webhook_url : str, default: `MISSING`
            Discord webhook URL for
            sending notifications.
        """
        cols, args = [], []
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
        with await self.pool as con:
            async with con.cursor() as cur:
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
        with await self.pool as con:
            async with con.cursor() as cur:
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
                        eg.scheduled_events = 0
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
