import aiomysql
from datetime import datetime, timedelta, timezone

class NotificationCountdown:
    """
    Notification Countdown table.
    """
    async def notification_countdown_add(
        self,
        guild_id: int,
        minutes: int
    ) -> str:
        """
        Add a countdown setting
        for the guild with the given
        amount of minutes.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        minutes : int
            Amount of minutes
            per notification.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO notification_countdown
                    (guild_id, minutes)
                    VALUES (%s, %s) AS new
                    ON DUPLICATE KEY UPDATE
                        minutes = new.minutes
                    """,
                    (guild_id, minutes)
                )

    async def notification_countdown_remove(
        self,
        guild_id: int,
        index: int
    ) -> None:
        """
        Remove a countdown setting
        for the guild with the given
        amount of minutes.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        index : int
            Index of the time
            when sorting minutes
            by ascending.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM
                        notification_countdown
                    WHERE
                        (guild_id, minutes) IN (
                            SELECT
                                guild_id,
                                minutes
                            FROM
                            (
                                SELECT
                                    guild_id,
                                    minutes,
                                    ROW_NUMBER() OVER
                                    (
                                        ORDER BY
                                            minutes
                                            ASC
                                    ) `index`
                                FROM
                                    notification_countdown
                                WHERE
                                    guild_id = %s
                            ) AS tmp
                            WHERE
                                `index` = %s
                        )
                    """,
                    (guild_id, index)
                )

    async def notification_countdown_list(self, guild_id: int) -> tuple[int]:
        """
        List all countdown notification
        minutes settings of a guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.

        Returns
        -------
        settings : tuple[
            index : int
            minutes : int
        ]
            A list containing all
            the countdown minute
            settings of the guild.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        ROW_NUMBER() OVER
                        (
                            ORDER BY
                                minutes
                                ASC
                        ) `index`,
                        minutes
                    FROM
                        notification_countdown
                    WHERE
                        guild_id=%s
                    """,
                    (guild_id,)
                )
                return await cur.fetchall()

    async def notification_countdown_check(self, guild_id: int) -> bool:
        """
        Check if a guild has their maximum amount
        of countdown notification settings.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.

        Returns
        -------
        check : bool
            Whether or not the maximum
            has been reached.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*) >= 64
                    FROM notification_countdown
                    WHERE guild_id=%s
                    """,
                    (guild_id,)
                )
                return (await cur.fetchone())[0] != 0

    async def notification_countdown_iter(
        self
    ) -> dict[str, datetime and int and str]:
        """
        Retrieve all countdown notifications
        that need sending to their respective
        guild depending on their settings.

        Yields
        -------
        notifications : dict[
            guild_id : int,
            notification_webhook_url : str,
            minutes : int,
            name : str,
            slug : str,
            status : int,
            agency : str,
            logo_url : str,
            url : str,
            image_url : str,
            start : datetime,
            scheduled_event_id : int
            type : int
        ]
            A list containing the
            notification data.

        Notes
        -----
        the `type` key in the yielded dict
        is a 1 for events and 0 for launches.
        """
        # Check for missing `.last_get`
        if not hasattr(self, 'last_get'):
            self.last_get = datetime.now(timezone.utc).replace(
                microsecond=0,
                tzinfo=None
            )
            return

        # Execute SQL
        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        eg.guild_id,
                        eg.notification_webhook_url,
                        nc.minutes,
                        le.name,
                        le.slug,
                        le.status,
                        la.name AS agency,
                        la.logo_url,
                        le.url,
                        le.image_url,
                        le.start,
                        se.scheduled_event_id,
                        le.ll2_id REGEXP '^[0-9]+$' AS `type`,
                        NOW() AS now
                    FROM ll2_events AS le
                    JOIN
                        enabled_guilds AS eg
                        ON eg.notification_webhook_url IS NOT NULL
                    JOIN
                        notification_countdown AS nc
                        ON nc.guild_id = eg.guild_id
                    LEFT JOIN
                        ll2_agencies AS la
                        ON la.agency_id = le.agency_id
                    LEFT JOIN
                        ll2_agencies_filter as laf
                        ON laf.guild_id = eg.guild_id
                        AND laf.agency_id = le.agency_id
                    LEFT JOIN
                        scheduled_events AS se
                        ON se.guild_id = eg.guild_id AND
                            eg.notification_scheduled_event AND
                            se.ll2_id = le.ll2_id
                    WHERE
                        le.status != 5
                        OR
                        le.status IS NULL
                    GROUP BY
                        eg.guild_id,
                        nc.minutes,
                        le.ll2_id,
                        laf.agency_id,
                        eg.notification_event,
                        eg.notification_launch,
                        se.scheduled_event_id
                    HAVING
                        le.start BETWEEN
                            DATE_ADD(
                                STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i:%%s'),
                                INTERVAL nc.minutes MINUTE
                            )
                            AND
                            DATE_ADD(NOW(), INTERVAL nc.minutes MINUTE)
                        AND
                            laf.agency_id IS NULL
                        AND
                        (
                            (
                                `type` AND
                                eg.notification_event
                            ) OR (
                                NOT `type` AND
                                eg.notification_launch
                            )
                        )
                    """,
                    (self.last_get,)
                )

                # No results, increment `.last_get` for next call
                if not cur.rowcount:
                    self.last_get += timedelta(minutes=1)

                async for row in cur:
                    # New `.last_get` for next call
                    self.last_get = row.pop('now')
                    # Convert timezone unaware datetime into UTC datetime
                    row['start'] = row['start'].replace(tzinfo=timezone.utc)
                    yield row
