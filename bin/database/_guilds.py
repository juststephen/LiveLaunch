class Guilds:
    """
    Guilds table methods.
    """
    async def guild_sync(self, guild_ids: list[int]) -> None:
        """
        Synchronise list of guild IDs with the database.

        Parameters
        ----------
        guild_ids : list[int]
            Guild IDs.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            # Create a temporary table to store the current list of IDs
            await cur.execute(
                """
                CREATE TEMPORARY TABLE `tmp_guilds` (
                    `guild_id` BIGINT UNSIGNED PRIMARY KEY
                );
                """
            )
            await cur.executemany(
                """
                INSERT INTO `tmp_guilds` (`guild_id`) VALUES (%s);
                """,
                guild_ids
            )

            # Remove old IDs
            await cur.execute(
                """
                DELETE FROM `guilds`
                WHERE `guild_id` NOT IN (SELECT `guild_id` FROM `tmp_guilds`);
                """
            )

            # Add new IDs
            await cur.execute(
                """
                INSERT INTO `guilds` (`guild_id`)
                SELECT `guild_id`
                FROM `tmp_guilds`
                ON DUPLICATE KEY UPDATE `guild_id` = `guilds`.`guild_id`;
                """
            )

    async def guild_add(self, guild_id: int) -> None:
        """
        Add a guild ID.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO `guilds` (`guild_id`)
                VALUES (%s)
                ON DUPLICATE KEY UPDATE `guild_id` = `guild_id`;
                """,
                (guild_id,)
            )

    async def guild_remove(self, guild_id: int) -> None:
        """
        Remove a guild ID.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        """
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM `guilds`
                WHERE `guild_id` = %s;
                """,
                (guild_id,)
            )
