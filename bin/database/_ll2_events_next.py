from itertools import chain
from typing import Literal

class LL2EventsNext:
    """
    LL2 events method for getting
    the next events for a guild.
    """
    async def ll2_events_next(
        self,
        guild_id: int | None,
        amount: int,
        event_type: Literal['events', 'launches']
    ) -> tuple[str] | None:
        """
        Get the upcoming events for a guild,
        takes agency filters into account.

        Parameters
        ----------
        guild_id : int or None
            Optional Discord guild ID.
        amount : int
            Amount of IDs to return.
        event_type : Literal['events', 'launches']
            Type of event.

        Returns
        -------
        ll2_ids : tuple[str] or None
            LL2 IDs of the upcoming
            events or launches.
        """
        # Select the event type
        if event_type == 'events':
            event_type_int = 1
        else:
            event_type_int = 0

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
                (guild_id, event_type_int, amount)
            )
            # Flatten tuple
            if (results := await cur.fetchall()):
                return tuple(chain(*results))
