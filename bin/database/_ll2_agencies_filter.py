from ._filter import Filter, FilterTable

class LL2AgenciesFilter(Filter):
    """
    LL2 Agencies Filter table methods.
    """
    def __init__(self) -> None:
        self._agency_filter_table = FilterTable(
            data_table='ll2_agencies',
            filter_table='ll2_agencies_filter',
            id_column='agency_id',
            name_column='name'
        )

    async def ll2_agencies_filter_add(
        self,
        guild_id: int,
        *,
        agency_names: list[str] = None,
        agency_ids: list[int] = None
    ) -> list[int and str]:
        """
        Add filters for agencies per guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        agency_names : list[str], default: None
            Agency name list.
        agency_ids : list[int], default: None
            Agency ID list.

        Returns
        -------
        failed : list[
            int and str
        ]
            List containing all the
            failed names and IDs.
        """
        return await self.filter_add(
            self._agency_filter_table,
            guild_id,
            names=agency_names,
            ids=agency_ids
        )

    async def ll2_agencies_filter_remove(
        self,
        guild_id: int,
        *,
        agency_names: list[str] = None,
        agency_ids: list[int] = None
    ) -> list[int and str]:
        """
        Remove filters for agencies per guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        agency_names : list[str], default: None
            Agency name list.
        agency_ids : list[int], default: None
            Agency ID list.

        Returns
        -------
        failed : list[
            int and str
        ]
            List containing all the
            failed names and IDs.
        """
        return await self.filter_remove(
            self._agency_filter_table,
            guild_id,
            names=agency_names,
            ids=agency_ids
        )

    async def ll2_agencies_filter_list(
        self,
        *,
        guild_id: int = None
    ) -> tuple[tuple[int, str]]:
        """
        List available or enabled
        filters for agencies.

        Parameters
        ----------
        guild_id : int, default: None
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
            self._agency_filter_table,
            guild_id=guild_id
        )

    async def ll2_agencies_filter_check(
        self,
        guild_id: int,
        agency_id: int
    ) -> bool:
        """
        Check if the agency is not
        being filtered in the guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        agency_id : int
            Agency ID.

        Returns
        -------
        check : bool
            True when the agency is not
            filtered within the guild.
        """
        return await self.filter_check(
            self._agency_filter_table,
            guild_id,
            id_value=agency_id
        )
