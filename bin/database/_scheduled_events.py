import aiomysql

class ScheduledEvents:
    """
    Discord scheduled events table.
    """
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
            guild_id : int,
            scheduled_event_id : int,
            create_remove : bool = False
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
                            WHERE
                                le.`end` > NOW()
                                AND
                                (
                                    le.`status` IS NULL
                                    OR
                                    le.`status` NOT IN (3, 4, 7)
                                )
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
            guild_id : int,
            ll2_id : str,
            create_remove : bool = True
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
                            WHERE
                                le.`end` > NOW()
                                AND
                                (
                                    le.`status` IS NULL
                                    OR
                                    le.`status` NOT IN (3, 4, 7)
                                )
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
            guild_id : int,
            scheduled_event_id : int or ll2_id : str,
            create_remove : bool
        ]
        """
        async for row in self.scheduled_events_remove_iter():
            yield row
        async for row in self.scheduled_events_create_iter():
            yield row
