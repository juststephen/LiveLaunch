class NotificationStatus:
    """
    Request guilds that enabled
    certain status notifications.
    """
    async def notification_status_iter(
        self,
        status: int
    ) -> dict[str, int and str]:
        """
        Request webhooks for guilds with the
        given status and notifications enabled.

        Parameters
        ----------
        status : int
            Status ID.

        Yields
        -------
        notifications : dict[
            guild_id : int,
            webhook_url : str
        ]
            A dictionary containing the
            guild notification data.
        """
        # Select setting column for the status
        if status == 6:
            status_col = 'notification_liftoff'
        elif stutus == 5:
            status_col = 'notification_hold'
        elif status in (3, 4, 7):
            status_col = 'notification_end_status'
        else:
            return

        # Execute SQL
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT
                        guild_id,
                        notification_webhook_url
                    FROM
                        enabled_guilds
                    WHERE
                        notification_webhook_url IS NOT NULL
                        AND
                        {status_col}
                    """
                )

                async for row in cur:
                    yield row
