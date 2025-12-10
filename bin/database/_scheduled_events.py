import aiomysql
from typing import AsyncGenerator

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
        async with self.pool.acquire() as con, con.cursor() as cur:
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
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM scheduled_events
                WHERE scheduled_event_id=%s
                """,
                (scheduled_event_id,)
            )

    async def scheduled_events_get(
        self,
        guild_id: int,
        ll2_id: str
    ) -> int | None:
        """
        Get the scheduled event ID of an LL2 event
        in a Guild if enabled in settings.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        ll2_id : str
            Launch Library 2 ID.

        Returns
        -------
        scheduled_event_id : int or None
            Discord scheduled event ID.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    se.scheduled_event_id
                FROM
                    enabled_guilds AS eg
                JOIN
                    scheduled_events AS se
                    ON se.guild_id = eg.guild_id
                WHERE
                    eg.guild_id = %s
                    AND
                    eg.notification_scheduled_event
                    AND
                    se.ll2_id = %s
                """,
                (guild_id, ll2_id)
            )
            result = await cur.fetchone()
            if result:
                return result[0]

    async def scheduled_events_guild_id_iter(
        self,
        guild_id: int
    ) -> AsyncGenerator[int]:
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
        scheduled_event_id : AsyncGenerator[int]
            Discord scheduled event IDs.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
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
    ) -> AsyncGenerator[tuple[int, int]]:
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
        AsyncGenerator[tuple[
            scheduled_event_id: int
            guild_id: int
        ]]
            Yields row with of a scheduled
            event linked to the LL2 event.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
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

    async def scheduled_events_remove_iter(
        self
    ) -> AsyncGenerator[dict[str, int | bool]]:
        """
        Asynchronous iterator that goes over
        Discord scheduled events that need
        to be removed.

        Yields
        ------
        AsyncGenerator[dict[
            guild_id : int,
            scheduled_event_id : int,
            create_remove : bool = False
        ]]
        """
        async with (
            self.pool.acquire() as con,
            con.cursor(aiomysql.DictCursor) as cur
        ):
            await cur.execute(
                """
                SELECT
                    se.guild_id,
                    se.scheduled_event_id,
                    0 as create_remove
                FROM
                    scheduled_events as se
                LEFT JOIN
                    (
                        SELECT
                            le.guild_id,
                            le.ll2_id
                        FROM
                            (
                                SELECT
                                    eg.guild_id,
                                    eg.scheduled_events,
                                    le.ll2_id,
                                    le.`start`,
                                    le.ll2_id REGEXP '^[0-9]+$' AS `type`,
                                    ROW_NUMBER() OVER
                                    (
                                        PARTITION BY
                                            eg.guild_id
                                        ORDER BY
                                            le.`start`
                                            ASC
                                    ) row_nr
                                FROM
                                    ll2_events AS le
                                JOIN
                                    enabled_guilds AS eg
                                LEFT JOIN
                                    ll2_agencies_filter as laf
                                    ON laf.guild_id = eg.guild_id
                                    AND laf.agency_id = le.agency_id
                                WHERE
                                    le.`end` > NOW()
                                    AND
                                    (
                                        le.`status` IS NULL
                                        OR
                                        le.`status` NOT IN (3, 4, 7)
                                    )
                                GROUP BY
                                    eg.guild_id,
                                    laf.agency_id,
                                    eg.agencies_include_exclude,
                                    le.ll2_id,
                                    le.url,
                                    eg.scheduled_events,
                                    eg.se_launch,
                                    eg.se_event,
                                    eg.se_no_url
                                HAVING
                                    NOT (
                                        eg.se_no_url AND le.url IS NULL
                                    )
                                    AND
                                    (
                                        `type`
                                        OR laf.agency_id IS NULL
                                        XOR eg.agencies_include_exclude <=> 1
                                    )
                                    AND
                                    (
                                        (
                                            `type` AND
                                            eg.se_event
                                        ) OR (
                                            NOT `type` AND
                                            eg.se_launch
                                        )
                                    )
                            ) AS le
                        GROUP BY
                            le.guild_id,
                            le.ll2_id,
                            le.row_nr,
                            le.scheduled_events
                        HAVING
                            le.row_nr <= le.scheduled_events
                    ) AS le
                    ON le.guild_id = se.guild_id
                    AND le.ll2_id = se.ll2_id
                WHERE
                    le.guild_id IS NULL
                """
            )
            async for row in cur:
                row['create_remove'] = bool(row['create_remove'])
                yield row

    async def scheduled_events_create_iter(
        self
    ) -> AsyncGenerator[dict[str, bool | int | str]]:
        """
        Asynchronous iterator that goes over
        Launch Library 2 events that need
        to be created.

        Yields
        ------
        AsyncGenerator[dict[
            guild_id : int,
            ll2_id : str,
            create_remove : bool = True
        ]]
        """
        async with (
            self.pool.acquire() as con,
            con.cursor(aiomysql.DictCursor) as cur
        ):
            await cur.execute(
                """
                SELECT
                    le.guild_id,
                    le.ll2_id,
                    1 as create_remove
                FROM
                    (
                        SELECT
                            eg.guild_id,
                            eg.scheduled_events,
                            le.ll2_id,
                            le.`start`,
                            le.ll2_id REGEXP '^[0-9]+$' AS `type`,
                            ROW_NUMBER() OVER
                            (
                                PARTITION BY
                                    eg.guild_id
                                ORDER BY
                                    le.`start`
                                    ASC
                            ) row_nr
                        FROM
                            ll2_events AS le
                        JOIN
                            enabled_guilds AS eg
                        LEFT JOIN
                            ll2_agencies_filter as laf
                            ON laf.guild_id = eg.guild_id
                            AND laf.agency_id = le.agency_id
                        WHERE
                            le.`end` > NOW()
                            AND
                            (
                                le.`status` IS NULL
                                OR
                                le.`status` NOT IN (3, 4, 7)
                            )
                        GROUP BY
                            eg.guild_id,
                            laf.agency_id,
                            eg.agencies_include_exclude,
                            le.ll2_id,
                            le.url,
                            eg.scheduled_events,
                            eg.se_launch,
                            eg.se_event,
                            eg.se_no_url
                        HAVING
                            NOT (
                                eg.se_no_url AND le.url IS NULL
                            )
                            AND
                            (
                                `type`
                                OR laf.agency_id IS NULL
                                XOR eg.agencies_include_exclude <=> 1
                            )
                            AND
                            (
                                (
                                    `type` AND
                                    eg.se_event
                                ) OR (
                                    NOT `type` AND
                                    eg.se_launch
                                )
                            )
                    ) AS le
                LEFT JOIN
                    scheduled_events AS se
                    ON se.guild_id = le.guild_id
                    AND se.ll2_id = le.ll2_id
                WHERE
                    le.`start` > DATE_ADD(NOW(), INTERVAL 2 MINUTE)
                GROUP BY
                    le.guild_id,
                    le.ll2_id,
                    le.row_nr,
                    le.scheduled_events,
                    se.scheduled_event_id
                HAVING
                    se.scheduled_event_id IS NULL
                    AND
                    le.row_nr <= le.scheduled_events
                """
            )
            async for row in cur:
                row['create_remove'] = bool(row['create_remove'])
                yield row

    async def scheduled_events_remove_create_iter(
        self
    ) -> AsyncGenerator[dict[str, bool | int | str]]:
        """
        Yields
        ------
        AsyncGenerator[dict[
            guild_id : int,
            scheduled_event_id : int or ll2_id : str,
            create_remove : bool
        ]]
        """
        async for row in self.scheduled_events_remove_iter():
            yield row
        async for row in self.scheduled_events_create_iter():
            yield row
