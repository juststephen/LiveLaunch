from itertools import chain

class LL2EventsNext:
    """
    LL2 events method for getting
    the next events for a guild.
    """
    async def ll2_events_next(
        self,
        guild_id: int,
        amount: int,
        *,
        events: bool = False,
        launches: bool = False
    ) -> tuple[str]:
        """
        Get the upcoming events for a guild,
        takes agency filters into account.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        amount : int
            Amount of IDs to return.
        events : bool, default: False
            Select events only.
        launches : bool, default: False
            Select launches only.

        Returns
        -------
        ll2_ids : tuple[str]
            LL2 IDs of the upcoming
            events or launches.
        """
        # Select the event type
        if events:
            event_type = 1
        elif launches:
            event_type = 0
        else:
            return

        # Execute SQL
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    le.ll2_id
                FROM
                    ll2_events AS le
                LEFT JOIN
                    enabled_guilds as eg
                    ON eg.guild_id = %s
                LEFT JOIN
                    ll2_agencies_filter AS laf
                    ON laf.guild_id = eg.guild_id
                    AND laf.agency_id = le.agency_id
                WHERE
                    le.start > NOW()
                    AND
                        le.ll2_id REGEXP '^[0-9]+$' = %s
                    AND
                    (
                        le.ll2_id REGEXP '^[0-9]+$'
                        OR laf.agency_id IS NULL
                        XOR eg.agencies_include_exclude <=> 1
                    )
                ORDER BY
                    le.start
                LIMIT
                    %s
                """,
                (guild_id, event_type, amount)
            )
            # Flatten tuple
            if (results := await cur.fetchall()):
                return tuple(chain(*results))
