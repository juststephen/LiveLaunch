# News sites/filter tables

class News:
    async def news_sites_add(self, news_site_name: str) -> None:
        """
        Add a news site to the
        database table `news_sites`.

        Parameters
        ----------
        news_site_name : str
            Name of the news site.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO
                    news_sites(news_site_name)
                    SELECT %s
                    WHERE NOT EXISTS(
                        SELECT *
                        FROM news_sites
                        WHERE news_site_name=%s
                    )
                    """,
                    (news_site_name, news_site_name)
                )

    async def news_filter_add(
        self,
        guild_id: int,
        *,
        news_site_name: str = None,
        news_site_id: int = None
    ) -> bool:
        """
        Adds a news site filter to
        the guild's news settings.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        news_site_name : str, default: None
            News site filter word.
        news_site_id : int, default: None
            News site filter index.

        Returns
        -------
        status : bool
            Whether the filter
            could be added or not.
        """
        if news_site_name:
            col = 'news_site_name'
            args = (guild_id, news_site_name)
            val = """
                (
                    SELECT news_site_id
                    FROM news_sites
                    WHERE news_site_name=%s
                )
            """
        elif news_site_id:
            col = 'news_site_id'
            args = (guild_id, news_site_id)
            val = '%s'
        else:
            return False
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM news_sites
                    WHERE {col}=%s
                    """,
                    args[1:]
                )
                status = (await cur.fetchone())[0] != 0
                if status:
                    await cur.execute(
                        f"""
                        REPLACE INTO news_filter
                        VALUES (%s, {val})
                        """,
                        args
                    )
                return status

    async def news_filter_remove(
        self,
        guild_id: int,
        *,
        news_site_name: str = None,
        news_site_id: int = None
    ) -> bool:
        """
        Removes a news site filter to
        the guild's news settings.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        news_site_name : str, default: None
            News site filter word.
        news_site_id : int, default: None
            News site filter index.

        Returns
        -------
        status : bool
            Whether the filter
            could be removed or not.
        """
        if news_site_name:
            col = 'news_site_name'
            args = (guild_id, news_site_name)
            val = """
                (
                    SELECT news_site_id
                    FROM news_sites
                    WHERE news_site_name=%s
                )
            """
        elif news_site_id:
            col = 'news_site_id'
            args = (guild_id, news_site_id)
            val = '%s'
        else:
            return False
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM news_sites
                    WHERE {col}=%s
                    """,
                    args[1:]
                )
                status = (await cur.fetchone())[0] != 0
                if status:
                    await cur.execute(
                        f"""
                        DELETE FROM news_filter
                        WHERE guild_id=%s AND
                        news_site_id={val}
                        """,
                        args
                    )
                return status

    async def news_filter_list(self, *, guild_id: int = None) -> tuple[tuple[int, str]]:
        """
        Get all current news site
        filters of the guild.

        Parameters
        ----------
        guild_id : int, default: None
            Discord guild ID, when
            None, return all available
            news sites for filtering.

        Returns
        -------
        filters : tuple[
            tuple[int, str]
        ]
            Returns a tuple of strings
            containing the current
            news sites & IDs being filtered
            or all available ones.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                if guild_id:
                    await cur.execute(
                        """
                        SELECT
                            ns.news_site_id,
                            ns.news_site_name
                        FROM news_filter AS nf
                        JOIN
                            news_sites AS ns
                            ON ns.news_site_id = nf.news_site_id
                        WHERE guild_id=%s
                        ORDER BY ns.news_site_id
                        """,
                        (guild_id,)
                    )
                else:
                    await cur.execute(
                        """
                        SELECT *
                        FROM news_sites
                        ORDER BY news_site_id
                        """
                    )
                return await cur.fetchall()

    async def news_filter_check(
        self,
        guild_id: int,
        news_site_name: str
    ) -> bool:
        """
        Check if the news site is not
        being filtered in the guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        news_site_name : str
            News site's name.

        Returns
        -------
        check : bool
            True when the news site is
            not filtered within the guild.
        """
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM news_filter AS nf
                    JOIN
                        news_sites AS ns
                        ON ns.news_site_id = nf.news_site_id
                    WHERE guild_id=%s AND news_site_name=%s
                    """,
                    (guild_id, news_site_name)
                )
                return (await cur.fetchone())[0] == 0
