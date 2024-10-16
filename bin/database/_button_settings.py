import aiomysql

class ButtonSettings:
    """
    Access button settings.
    """
    async def button_settings_edit(
        self,
        guild_id,
        *,
        button_fc: bool = None,
        button_g4l: bool = None,
        button_sln: bool = None
    ) -> None:
        """
        Modify the button
        settings of a guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        button_fc : bool, default: None
            Include/exclude a button
            to Flight Club in notifications.
        button_g4l : bool, default: None
            Include/exclude a button
            to Go4Liftoff in notifications.
        button_sln : bool, default: None
            Include/exclude a button
            to Space Launch Now in notifications.
        """
        cols, args = [], []
        # Update button_fc if given
        if button_fc is not None:
            cols.append('notification_button_fc=%s')
            args.append(button_fc)
        # Update button_g4l if given
        if button_g4l is not None:
            cols.append('notification_button_g4l=%s')
            args.append(button_g4l)
        if button_sln is not None:
            cols.append('notification_button_sln=%s')
            args.append(button_sln)
        # Add guild ID to the arguments
        args.append(guild_id)

        # Update db
        async with self.pool.acquire() as con:
            async with con.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE enabled_guilds
                    SET {', '.join(cols)}
                    WHERE guild_id=%s
                    """,
                    args
                )

    async def button_settings_get(
        self,
        guild_id: int,
        ll2_id: str,
    ) -> dict[str, bool]:
        """
        Get the button settings for
        the requested guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        ll2_id : str
            Launch Library 2 ID.

        Returns
        -------
        button_settings : dict[
            button_fc : bool,
            button_g4l : bool,
            button_sln : bool
        ]
            Button settings
            for the guild.
        """
        async with self.pool.acquire() as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT
                        le.flightclub AND eg.notification_button_fc AS button_fc,
                        eg.notification_button_g4l AS button_g4l,
                        eg.notification_button_sln AS button_sln
                    FROM
                        enabled_guilds as eg
                    JOIN
                        ll2_events as le
                        ON le.ll2_id = %s
                    WHERE
                        eg.guild_id = %s
                    """,
                    (ll2_id, guild_id)
                )
                return await cur.fetchone()
