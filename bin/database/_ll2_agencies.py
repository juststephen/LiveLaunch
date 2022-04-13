class LL2Agencies:
    """
    LL2 Agencies table methods.
    """
    async def ll2_agencies_replace(
        self,
        agency_id: int,
        name: str
    ) -> None:
        """
        Adds an agency to the
        database for storing
        their name and logo.

        Parameters
        ----------
        agency_id : int
            LL2 agency ID.
        name : str
            Name of the agency.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO ll2_agencies
                    (agency_id, name)
                    VALUES (%s, %s) AS new
                    ON DUPLICATE KEY UPDATE
                        name = new.name
                    """,
                    (
                        agency_id,
                        name
                    )
                )

    async def ll2_agencies_get(self, ll2_id: str) -> tuple[str, str]:
        """
        Get an angency's name and logo by
        an ID of one of their events.

        Parameters
        ----------
        ll2_id : int
            Launch Library 2 ID.

        Returns
        -------
        name : str
            Name of the agency.
        logo_url : str
            Logo of the agency.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        la.name,
                        la.logo_url
                    FROM
                        ll2_events AS le
                    JOIN
                        ll2_agencies AS la
                        ON
                        la.agency_id = le.agency_id
                    WHERE
                        ll2_id = %s
                    """,
                    (ll2_id,)
                )
        return await cur.fetchone()
