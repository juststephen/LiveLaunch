from dataclasses import dataclass

@dataclass
class FilterTable:
    """
    Data class to store the details
    of the tables that are used in
    the `Filter` class.

    Attributes
    ----------
    data_table : str
        Table name of the table that
        stores the data's name and IDs.
    filter_table : str
        Table namee of the table that
        stores the data ID with the
        Discord Guild ID.
    id_column : str
        Column name of the data table
        that contains the IDs.
    include_exclude_column : str
        Column name of the `enabled_guilds`
        table where the include/
        exclude boolean is set.
    name_column : str
        Column name of the data table
        that contains the names.
    """
    data_table: str
    filter_table: str
    id_column: str
    include_exclude_column: str
    name_column: str

class Filter:
    """
    Base methods for filter tables.
    Contains methods for adding, removing,
    listing and checking filters.
    """
    async def filter_set_include_exclude(
        self,
        tables: FilterTable,
        guild_id: int,
        *,
        include_or_exclude: bool
    ) -> None:
        """
        Set the filter to include/exclude.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        guild_id : int
            Discord guild ID.
        include_or_exclude : bool
            Set the filter
            to Include/Exclude.
            `True` when included,
            `False` when excluded.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE enabled_guilds
                SET {tables.include_exclude_column}=%s
                WHERE guild_id=%s
                """,
                (include_or_exclude, guild_id)
            )

    async def filter_get_include_exclude(
        self,
        tables: FilterTable,
        guild_id: int
    ) -> bool:
        """
        See if the filter is set to include/exclude.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        guild_id : int
            Discord guild ID.

        Returns
        -------
        include_or_exclude : bool
            `True` when included,
            `False` when excluded.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {tables.include_exclude_column}
                FROM enabled_guilds
                WHERE guild_id=%s
                """,
                (guild_id,)
            )
            return (await cur.fetchone())[0] != 0

    async def _filter_base_add_remove(
        self,
        tables: FilterTable,
        query: str,
        guild_id: int,
        *,
        names: list[str] | None = None,
        ids: list[int] | None = None
    ) -> list[int | str]:
        """
        Base for add/remove filters.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        query : str
            SQL query to perform
            on the data.
        guild_id : int
            Discord guild ID.
        names : list[str] or None, default: None
            Name list.
        ids : list[int] or None, default: None
            ID list.

        Returns
        -------
        failed : list[
            int and str
        ]
            List containing all the
            failed names and IDs.
        """
        data: dict[str, list[int] | list[str]] = {}
        if names:
            data[tables.name_column] = names
        if ids:
            data[tables.id_column] = ids

        failed: list[int | str] = []

        async with self.pool.acquire() as con, con.cursor() as cur:
            # Iterating over data to check & perform SQL
            for col, args in data.items():
                for arg in args:
                    # Check if data exists
                    await cur.execute(
                        f"""
                        SELECT IFNULL(
                            (
                                SELECT {tables.id_column}
                                FROM {tables.data_table}
                                WHERE {col} = %s
                            ),
                            0
                        )
                        """,
                        arg
                    )

                    # Perform SQL query if it exists, else add to failed
                    if (_id := (await cur.fetchone())[0]):
                        await cur.execute(
                            query,
                            (guild_id, _id)
                        )
                    else:
                        failed.append(arg)

        return failed

    async def filter_add(
        self,
        tables: FilterTable,
        guild_id: int,
        *,
        names: list[str] | None = None,
        ids: list[int] | None = None
    ) -> list[int | str]:
        """
        Add filters per guild.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        guild_id : int
            Discord guild ID.
        names : list[str] or None, default: None
            Name list.
        ids : list[int] or None, default: None
            ID list.

        Returns
        -------
        failed : list[
            int and str
        ]
            List containing all the
            failed names and IDs.
        """
        return await self._filter_base_add_remove(
            tables,
            f"""
            INSERT INTO {tables.filter_table}
            (guild_id, {tables.id_column})
            VALUES (%s, %s) AS new
            ON DUPLICATE KEY UPDATE
                {tables.id_column} = new.{tables.id_column}
            """,
            guild_id,
            names=names,
            ids=ids
        )

    async def filter_remove(
        self,
        tables: FilterTable,
        guild_id: int,
        *,
        names: list[str] | None = None,
        ids: list[int] | None = None
    ) -> list[int | str]:
        """
        Remove filters per guild.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        guild_id : int
            Discord guild ID.
        names : list[str] or None, default: None
            Name list.
        ids : list[int] or None, default: None
            ID list.

        Returns
        -------
        failed : list[
            int and str
        ]
            List containing all the
            failed names and IDs.
        """
        return await self._filter_base_add_remove(
            tables,
            f"""
            DELETE FROM
                {tables.filter_table}
            WHERE
                guild_id = %s
                AND
                {tables.id_column} = %s
            """,
            guild_id,
            names=names,
            ids=ids
        )

    async def filter_list(
        self,
        tables: FilterTable,
        *,
        guild_id: int | None = None
    ) -> tuple[tuple[int, str]]:
        """
        List available or enabled filters.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        guild_id : int or None, default: None
            Discord guild ID, when
            None, return all available
            items for filtering.

        Returns
        -------
        filters : tuple[
            tuple[int, str]
        ]
            Returns a tuple of strings
            containing the current
            names & IDs being filtered
            or all available ones.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            if guild_id:
                await cur.execute(
                    f"""
                    SELECT
                        `data`.{tables.id_column}, `data`.{tables.name_column}
                    FROM
                        {tables.filter_table} AS `filter`
                    JOIN
                        {tables.data_table} AS `data`
                        ON `data`.{tables.id_column} = `filter`.{tables.id_column}
                    WHERE
                        `filter`.guild_id = %s
                    ORDER BY
                        `data`.{tables.id_column}
                    """,
                    (guild_id,)
                )
            else:
                await cur.execute(
                    f"""
                    SELECT
                        {tables.id_column}, {tables.name_column}
                    FROM
                        {tables.data_table}
                    ORDER BY
                        {tables.id_column}
                    """
                )
            return await cur.fetchall()

    async def filter_check(
        self,
        tables: FilterTable,
        guild_id: int,
        *,
        name_value: str | None = None,
        id_value: int | None = None
    ) -> bool:
        """
        Check if the name or ID is not
        being filtered in the guild.

        Parameters
        ----------
        tables : FilterTable
            FilterTable object
            with the required
            SQL table data.
        guild_id : int
            Discord guild ID.
        name_value : str or None, default: None
            Name to check.
        id_value : int or None, default: None
            ID to check.

        Returns
        -------
        check : bool
            True when the name or ID is
            not filtered within the guild.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            if name_value:
                await cur.execute(
                    f"""
                    SELECT
                        COUNT(*)
                    FROM
                        {tables.filter_table} AS `filter`
                    JOIN
                        {tables.data_table} AS `data`
                        ON `data`.{tables.id_column} = `filter`.{tables.id_column}
                    WHERE
                        `filter`.guild_id = %s
                        AND
                        `data`.{tables.name_column} = %s
                    """,
                    (guild_id, name_value)
                )
            else:
                await cur.execute(
                    f"""
                    SELECT
                        COUNT(*)
                    FROM
                        {tables.filter_table}
                    WHERE
                        guild_id = %s
                        AND
                        {tables.id_column} = %s
                    """,
                    (guild_id, id_value)
                )
            return (await cur.fetchone())[0] == 0
