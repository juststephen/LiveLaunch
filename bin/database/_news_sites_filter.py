from ._filter import Filter, FilterTable

class NewsFilter(Filter):
    """
    News sites filter table methods.
    """
    def __init__(self) -> None:
        self._news_filter_table = FilterTable(
            data_table='news_sites',
            filter_table='news_filter',
            id_column='news_site_id',
            include_exclude_column='news_include_exclude',
            name_column='news_site_name'
        )

    async def news_filter_set_include_exclude(
        self,
        guild_id: int,
        *,
        include_or_exclude: bool
    ) -> None:
        """
        Set the news filter to include/exclude.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        include_or_exclude : bool
            Set the filter
            to Include/Exclude.
            `True` when included,
            `False` when excluded.
        """
        return await self.filter_set_include_exclude(
            self._news_filter_table,
            guild_id,
            include_or_exclude=include_or_exclude
        )

    async def news_filter_get_include_exclude(
        self,
        guild_id: int
    ) -> bool:
        """
        See if the news filter is set to include/exclude.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.

        Returns
        -------
        include_or_exclude : bool
            `True` when included,
            `False` when excluded.
        """
        return await self.filter_get_include_exclude(
            self._news_filter_table,
            guild_id
        )

    async def news_filter_add(
        self,
        guild_id: int,
        *,
        news_site_names: list[str] | None = None,
        news_site_ids: list[int] | None = None
    ) -> list[int | str]:
        """
        Add filters for news sites per guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        news_site_names : list[str] or None, default: None
            News site name list.
        news_site_ids : list[int] or None, default: None
            News site ID list.

        Returns
        -------
        failed : list[
            int and str
        ]
            List containing all the
            failed names and IDs.
        """
        return await self.filter_add(
            self._news_filter_table,
            guild_id,
            names=news_site_names,
            ids=news_site_ids
        )

    async def news_filter_remove(
        self,
        guild_id: int,
        *,
        news_site_names: list[str] | None = None,
        news_site_ids: list[int] | None = None
    ) -> list[int | str]:
        """
        Remove filters for news sites per guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        news_site_names : list[str] or None, default: None
            News site name list.
        news_site_ids : list[int] or None, default: None
            News site ID list.

        Returns
        -------
        failed : list[
            int or str
        ]
            List containing all the
            failed names and IDs.
        """
        return await self.filter_remove(
            self._news_filter_table,
            guild_id,
            names=news_site_names,
            ids=news_site_ids
        )

    async def news_filter_list(
        self,
        *,
        guild_id: int | None = None
    ) -> tuple[tuple[int, str]]:
        """
        List available or enabled
        filters for news sites.

        Parameters
        ----------
        guild_id : int or None, default: None
            Discord guild ID, when
            None, return all available
            agencies for filtering.

        Returns
        -------
        filters : tuple[
            tuple[int, str]
        ]
            Returns a tuple of strings
            containing the current
            agencies & IDs being filtered
            or all available ones.
        """
        return await self.filter_list(
            self._news_filter_table,
            guild_id=guild_id
        )

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
        news_site_name : int
            News site name.

        Returns
        -------
        check : bool
            True when the news site is not
            filtered within the guild.
        """
        return await self.filter_check(
            self._news_filter_table,
            guild_id,
            name_value=news_site_name
        )
