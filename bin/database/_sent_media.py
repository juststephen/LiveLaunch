from datetime import datetime, timezone

class SentMedia:
    """
    Sent streams/news tables.
    """
    async def sent_media_add(
        self,
        *,
        snapi_id: int | None = None,
        yt_vid_id: str | None = None,
        timestamp: datetime | None = None
    ) -> None:
        """
        Adds an entry in the specified sent media
        table of the LiveLaunch database.

        Parameters
        ----------
        snapi_id : int or None, default: None
            SNAPI article ID.
        yt_vid_id : str or None, default: None
            YouTube video ID.
        timestamp : datetime or None, default: None
            Datetime object, when default,
            the current UTC datetime is used.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Select the correct sent media table
        if snapi_id:
            table = 'news'
            args = (snapi_id, timestamp)
        else:
            table = 'streams'
            args = (yt_vid_id, timestamp)

        # Connect and add
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                f"""
                INSERT INTO sent_{table}
                VALUES (%s, %s)
                """,
                args
            )

    async def sent_media_clean(self) -> None:
        """
        Removes old entries in the sent media
        tables of the LiveLaunch database.

        Notes
        -----
        Removes entries older than one year.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM sent_news
                WHERE datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR);
                DELETE FROM sent_streams
                WHERE datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR)
                """
            )

    async def sent_media_exists(
        self,
        *,
        snapi_id: int | None = None,
        yt_vid_id: str | None = None,
    ) -> bool:
        """
        Checks if an entry exists in the specified
        sent media table of the LiveLaunch database.

        Parameters
        ----------
        snapi_id : int or None, default: None
            SNAPI article ID.
        yt_vid_id : str or None, default: None
            YouTube video ID.

        Returns
        -------
        check : bool
            Returns a boolean whether an entry
            exists with the given ID.
        """
        # Select the correct sent media table
        if snapi_id:
            table = 'news'
            col = 'snapi_id'
            args = (snapi_id,)
        else:
            table = 'streams'
            col = 'yt_vid_id'
            args = (yt_vid_id,)

        # Connect and check
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                f"""
                SELECT COUNT(*)
                FROM sent_{table}
                WHERE {col}=%s
                """,
                args
            )
            return (await cur.fetchone())[0] != 0
