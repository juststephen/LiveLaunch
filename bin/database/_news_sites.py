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
