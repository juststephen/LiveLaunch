import aiomysql
from datetime import datetime

from ._missing import MISSING

class LL2Events:
    """
    LL2 events table.
    """
    async def ll2_events_add(
        self,
        ll2_id: str,
        name: str,
        description: str,
        url: str,
        image_url: str,
        start: datetime,
        end: datetime,
        agency_id: int = None,
        status: int = None,
        webcast_live: bool = False,
        **kwargs
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
        agency_id : int, default: None
            LL2 agency ID.
        status : int, default: None
            Status ID.
        webcast_live : bool, default: False
            Event is live or not.
        **kwargs
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO ll2_events
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ll2_id,
                        agency_id,
                        name,
                        status,
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
    ) -> dict[str, bool and datetime and str]:
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
            ll2_id : str,
            agency_id : int,
            name : str,
            status : int,
            description : str,
            url : str,
            image_url : str,
            start : datetime,
            end : datetime,
            webcast_live : bool
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
    ) -> dict[str, datetime and str] or None:
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
            agency_id : int,
            name : str,
            status : int,
            description : str,
            url : str,
            image_url : str,
            start : datetime,
            end : datetime,
            webcast_live : bool
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
        agency_id: int = None,
        name: str = None,
        status: int = None,
        description: str = None,
        url: str = None,
        image_url: str = MISSING,
        start: datetime = None,
        end: datetime = None,
        webcast_live: bool = None,
        **kwargs
    ) -> None:
        """
        Modifies an entry in the `ll2_events`
        table of the LiveLaunch database.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.
        agency_id : int
            LL2 agency ID.
        name : str, default: None
            Name of the event.
        status : int, default: None
            Status ID.
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
        **kwargs
        """
        cols, args = [], []
        # Update variables in the row if given
        if agency_id is not None:
            cols.append('agency_id=%s')
            args.append(agency_id)
        if name is not None:
            cols.append('name=%s')
            args.append(name)
        if status is not None:
            cols.append('status=%s')
            args.append(status)
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
