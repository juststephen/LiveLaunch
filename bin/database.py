import aiomysql
from datetime import datetime, timezone
from os import getenv

class _MISSING:
    """
    Database None, used for
    columns that can be set to
    None / NULL.
    """
    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    def __repr__(self):
        return 'MISSING'

MISSING = _MISSING()

class Database:
    """
    Database methods for livelaunch.
    """
    def __init__(self):
        self.__host = 'server.juststephen.com'
        self.__user = 'root'
        self.__database = 'LiveLaunch'
        self.started = False

    async def start(self) -> bool:
        """
        Loads the LiveLaunch database.
        """
        self.started = True
        # Connect
        self.pool = await aiomysql.create_pool(
            host=self.__host,
            user=self.__user,
            password=getenv('DB_PWD'),
            db=self.__database,
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
                    scheduled_events TINYINT UNSIGNED DEFAULT 0
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
                # Create table for storing sent live streams
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sent_streams (
                    yt_vid_id TEXT,
                    datetime TEXT DEFAULT NULL
                    )
                    """
                )

    # Enabled & settings table

    async def enabled_guilds_add(
        self,
        guild_id: int,
        channel_id: int = None,
        webhook_url: str = None,
        scheduled_events: int = 0
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
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO enabled_guilds
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        guild_id,
                        channel_id,
                        webhook_url,
                        scheduled_events
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
        guild_id : int
            Yields Discord Guild ID
            when it scheduled events
            are enabled.
        amount : int
            Amount of events that can
            be created before reaching
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
                    WHERE NOT webhook_url IS NULL
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
            channel_id: int,
            webhook_url: str,
            scheduled_events: int
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
        scheduled_events: int = None
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
                    """
                )

    # LL2 events table

    async def ll2_events_add(
        self,
        ll2_id: str,
        name: str,
        description: str,
        url: str,
        image_url: str,
        start: datetime,
        end: datetime,
        webcast_live: bool = False
    ) -> None:
        """
        Adds an entry in the `ll2_events`
        table of the LiveLaunch database.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.
        name : str
            Name of the event.
        description : str
            Event description.
        url : str
            Event live stream URL.
        image_url : str
            Event cover image URL.
        start : datetime
            Event start datetime object.
        end : datetime
            Event end datetime object.
        webcast_live : bool, default: False
            Event is live or not.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO ll2_events
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ll2_id, name,
                        description, url,
                        image_url,
                        start.isoformat(),
                        end.isoformat(),
                        webcast_live
                    )
                )

    async def ll2_events_remove(
        self,
        ll2_id: str
    ) -> None:
        """
        Removes an entry in the corresponding `ll2_events`
        table of the LiveLaunch database.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM ll2_events
                    WHERE ll2_id=%s
                    """,
                    (ll2_id,)
                )

    async def ll2_events_iter(
        self,
        asc_desc: str = 'asc'
    ) -> dict[str, bool and str and datetime]:
        """
        Go over every row in the `ll2_events`
        table of the LiveLaunch database by
        the order of the start datetime.

        Parameters
        ----------
        asc_desc : str, default: 'asc'
            Order of the results:
                ` 'asc' `:
                    Ascending
                ` 'desc' `:
                    Descending

        Yields
        ------
        dict[
            ll2_id: str,
            name: str,
            description: str
            url: str,
            image_url: str,
            start: datetime,
            end: datetime,
            webcast_live: bool
        ]
            Yields row with of an LL2
            event with the relevant data.
        """
        if asc_desc.lower() == 'asc':
            order = 'ASC'
        elif asc_desc.lower() == 'desc':
            order = 'DESC'
        else:
            raise Exception('Wrong `asc_desc` value given.')

        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT *
                    FROM ll2_events
                    ORDER BY start {order}
                    """
                )
                async for row in cur:
                    # Convert strings back into datetime objects
                    row['start'] = datetime.fromisoformat(row['start'])
                    row['end'] = datetime.fromisoformat(row['end'])
                    row['webcast_live'] = bool(row['webcast_live'])
                    yield row

    async def ll2_events_get(
        self,
        ll2_id: str
    ) -> dict[str, str and datetime] or None:
        """
        Retrieves an entry from the `ll2_events`
        table of the LiveLaunch database.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.

        Returns
        -------
        dict[
            name: str
            description: str
            url: str,
            image_url: str,
            start: datetime,
            end: datetime,
            webcast_live: bool
        ] or None
            Returns a row with the ll2_event's data
            if it exists, otherwise None.
        """
        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM ll2_events
                    WHERE ll2_id=%s
                    """,
                    (ll2_id,)
                )
                row = await cur.fetchone()
        if row:
            # Convert strings back into datetime objects
            row['start'] = datetime.fromisoformat(row['start'])
            row['end'] = datetime.fromisoformat(row['end'])
            row['webcast_live'] = bool(row['webcast_live'])
        return row

    async def ll2_events_edit(
        self,
        ll2_id: str,
        name: str = None,
        description: str = None,
        url: str = None,
        image_url: str = MISSING,
        start: datetime = None,
        end: datetime = None,
        webcast_live: bool = None
    ) -> None:
        """
        Modifies an entry in the `ll2_events`
        table of the LiveLaunch database.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.
        name : str, default: None
            Name of the event.
        description : str, default: None
            Event description.
        url : str, default: None
            Event live stream URL.
        image_url : str, default: MISSING
            Event cover image URL.
        start : datetime, default: None
            Event start datetime object.
        end : datetime, default: None
            Event end datetime object.
        webcast_live : bool, default: None
            Event is live or not.
        """
        cols, args = [], []
        # Update variables in the row if given
        if name is not None:
            cols.append('name=%s')
            args.append(name)
        if description is not None:
            cols.append('description=%s')
            args.append(description)
        if url is not None:
            cols.append('url=%s')
            args.append(url)
        if image_url is not MISSING:
            cols.append('image_url=%s')
            args.append(image_url)
        if start is not None:
            cols.append('start=%s')
            args.append(start.isoformat())
        if end is not None:
            cols.append('end=%s')
            args.append(end.isoformat())
        if webcast_live is not None:
            cols.append('webcast_live=%s')
            args.append(webcast_live)
        # Add ll2_id to the arguments
        args.append(ll2_id)
        # Update
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE ll2_events
                    SET {', '.join(cols)}
                    WHERE ll2_id=%s
                    """,
                    args
                )

    # Discord scheduled events table

    async def scheduled_events_add(
        self,
        scheduled_event_id: int,
        guild_id: int,
        ll2_id: str
    ) -> None:
        """
        Add a Discord scheduled event
        entry to the `scheduled_events`
        table of the LiveLaunch database.

        Parameters
        ----------
        scheduled_event_id : int
            Discord scheduled event ID.
        guild_id : int
            Discord guild ID corresponding
            to the scheduled event.
        ll2_id : str
            Launch Library 2 ID indicating
            scheduled event content.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO scheduled_events
                    VALUES (%s, %s, %s)
                    """,
                    (
                        scheduled_event_id,
                        guild_id,
                        ll2_id
                    )
                )

    async def scheduled_events_remove(
        self,
        scheduled_event_id: int
    ) -> None:
        """
        Removes an entry in the corresponding
        `scheduled_events` table of the
        LiveLaunch database.

        Parameters
        ----------
        scheduled_event_id : int
            Discord scheduled event ID.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM scheduled_events
                    WHERE scheduled_event_id=%s
                    """,
                    (scheduled_event_id,)
                )

    async def scheduled_events_guild_id_iter(
        self,
        guild_id: int
    ) -> int or None:
        """
        Iterate over the scheduled events
        of the Discord guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID corresponding
            to the scheduled events.

        Yields
        ------
        scheduled_event_id : int
            Discord scheduled event ID.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT scheduled_event_id
                    FROM scheduled_events
                    WHERE guild_id=%s
                    """,
                    (guild_id,)
                )
                async for row in cur:
                    yield row[0]

    async def scheduled_events_ll2_id_iter(
        self,
        ll2_id: str
    ) -> tuple[int] or None:
        """
        Iterate over the scheduled events
        of the LL2 event, can be used
        to update or remove them from
        Discord before removing from the
        database.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.

        Yields
        ------
        tuple[
            scheduled_event_id: int
            guild_id: int
        ] or None
            Yields row with of a scheduled
            event linked to the LL2 event.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT scheduled_event_id, guild_id
                    FROM scheduled_events
                    WHERE ll2_id=%s
                    """,
                    (ll2_id,)
                )
                async for row in cur:
                    yield row

    async def scheduled_events_remove_iter(self) -> dict[str, int and bool]:
        """
        Asynchronous iterator that goes over
        Discord scheduled events that need
        to be removed.

        Yields
        ------
        dict[
            guild_id: int,
            scheduled_event_id: int,
            create_remove: bool = False
        ]
        """
        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        eg.guild_id,
                        se.scheduled_event_id,
                        0 as create_remove
                    FROM
                        enabled_guilds AS eg
                    JOIN
                        scheduled_events AS se
                        ON se.guild_id = eg.guild_id
                    JOIN
                        (
                            SELECT
                                le.ll2_id,
                                ROW_NUMBER() OVER
                                (
                                    ORDER BY
                                        le.`start`
                                        ASC
                                ) row_nr
                            FROM
                                ll2_events AS le
                        ) AS le
                        ON
                        (
                            le.ll2_id = se.ll2_id
                            AND
                            le.row_nr > eg.scheduled_events
                        )
                    """
                )
                async for row in cur:
                    row['create_remove'] = bool(row['create_remove'])
                    yield row

    async def scheduled_events_create_iter(self) -> dict[str, int and str and bool]:
        """
        Asynchronous iterator that goes over
        Launch Library 2 events that need
        to be created.

        Yields
        ------
        dict[
            guild_id: int,
            ll2_id: str,
            create_remove: bool = True
        ]
        """
        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        eg.guild_id,
                        le.ll2_id,
                        1 as create_remove
                    FROM
                        enabled_guilds AS eg
                    JOIN
                        (
                            SELECT
                                le.ll2_id,
                                le.`start`,
                                ROW_NUMBER() OVER
                                (
                                    ORDER BY
                                        le.`start`
                                        ASC
                                ) row_nr
                            FROM
                                ll2_events AS le
                        ) AS le
                    WHERE
                        le.`start` > DATE_ADD(NOW(), INTERVAL 2 MINUTE)
                    GROUP BY
                        eg.guild_id,
                        le.ll2_id,
                        le.row_nr,
                        eg.scheduled_events
                    HAVING
                        le.ll2_id NOT IN (
                            SELECT
                                se.ll2_id
                            FROM
                                scheduled_events AS se
                            WHERE
                                se.guild_id = eg.guild_id
                        )
                        AND
                        le.row_nr <= eg.scheduled_events
                    """
                )
                async for row in cur:
                    row['create_remove'] = bool(row['create_remove'])
                    yield row

    async def scheduled_events_remove_create_iter(
        self
    ) -> dict[str, int and str and bool]:
        """
        Yields
        ------
        dict[
            guild_id: int,
            scheduled_event_id: int or ll2_id: str,
            create_remove: bool
        ]
        """
        async for row in self.scheduled_events_remove_iter():
            yield row
        async for row in self.scheduled_events_create_iter():
            yield row

    # Sent streams table

    async def sent_streams_add(
        self, yt_vid_id: str,
        datetime: datetime = datetime.now(timezone.utc)
    ) -> None:
        """
        Adds an entry in the `sent_streams`
        table of the LiveLaunch database.

        Parameters
        ----------
        yt_vid_id : str
            YouTube video ID.
        datetime : datetime, default: datetime.now(timezone.utc)
            Datetime object, default is the current UTC datetime.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO sent_streams
                    VALUES (%s, %s)
                    """,
                    (yt_vid_id, datetime.isoformat())
                )

    async def sent_streams_clean(self) -> None:
        """
        Removes old entries in the `sent_streams`
        table of the LiveLaunch database.

        Notes
        -----
        Removes entries older than one year.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM sent_streams
                    WHERE datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR)
                    """
                )

    async def sent_streams_exists(self, yt_vid_id: str) -> bool:
        """
        Checks if an entry exists in the `sent_streams`
        table of the LiveLaunch database.

        Parameters
        ----------
        yt_vid_id : str
            YouTube video ID.

        Returns
        -------
        check : bool
            Returns a boolean wheter an entry
            exists with the given yt_vid_id.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT count(*)
                    FROM sent_streams
                    WHERE yt_vid_id=%s
                    """,
                    (yt_vid_id,)
                )
                return (await cur.fetchone())[0] != 0
