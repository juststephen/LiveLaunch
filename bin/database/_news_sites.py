class News:
    """
    News sites table methods.
    """
    async def news_sites_add(self, news_site_name: str) -> None:
        """
        Add a news site to the
        database table `news_sites`.

        Parameters
        ----------
        news_site_name : str
            Name of the news site.
        """
        async with self.pool.acquire() as con:
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

    async def news_sites_get_logo(self, news_site_name: str) -> str:
        """
        Get a news site's logo by their name.

        Parameters
        ----------
        news_site_name : str
            Name of the news site.

        Returns
        -------
        logo_url : str
            Logo of the news site.
        """
        async with self.pool.acquire() as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        logo_url
                    FROM
                        news_sites
                    WHERE
                        news_site_name = %s
                    """,
                    (news_site_name,)
                )
                return (await cur.fetchone())[0]
