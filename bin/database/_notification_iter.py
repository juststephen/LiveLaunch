import aiomysql

class NotificationIter:
    """
    Request guilds that enabled
    certain notifications.
    """
    async def notification_iter(
        self,
        *,
        event: bool = False,
        launch: bool = False,
        ll2_id: str = None,
        status: int = None,
        no_status: bool = False,
        no_t0: bool = False
    ) -> dict[str, int and str]:
        """
        Request webhooks for guilds with the
        given setting and notifications enabled.

        Parameters
        ----------
        event : bool, default: False
            Whether or not the NET
            change is for an event.
        launch : bool, default: False
            Whether or not the NET
            change is for a launch.
        ll2_id : str, default: None
            Launch Library 2 ID.
        status : int, default: None
            Status ID.
        no_status : bool, default: False
            Invert the status check
            to get guilds without the
            status type on.
        no_t0 : bool, default: False
            Don't add the event or launch
            checks for a T-0 notification
            if this is True.

        Yields
        -------
        notifications : dict[
            guild_id : int,
            webhook_url : str,
            button_g4l : bool,
            button_sln : bool,
            scheduled_event_id : int
        ]
            A dictionary containing the
            guild notification data.
        """
        # Select setting columns
        settings = []
        status_prefix = 'NOT ' if no_status else ''

        # T-0 settings
        if no_t0:
            settings.append('NOT eg.notification_t0_change')
        elif event:
            settings.append('eg.notification_t0_change')
            settings.append('eg.notification_event')
        elif launch:
            settings.append('eg.notification_t0_change')
            settings.append('eg.notification_launch')

        # Status settings
        if status == 2:
            settings.append(
                f'{status_prefix}eg.notification_tbd'
            )
        elif status == 8:
            settings.append(
                f'{status_prefix}eg.notification_tbc'
            )
        elif status == 1:
            settings.append(
                f'{status_prefix}eg.notification_go'
            )
        elif status == 6:
            settings.append(
                f'{status_prefix}eg.notification_liftoff'
            )
        elif status == 5:
            settings.append(
                f'{status_prefix}eg.notification_hold'
            )
        elif status in (3, 4, 7):
            settings.append(
                f'{status_prefix}eg.notification_end_status'
            )

        # Execute SQL
        with await self.pool as con:
            async with con.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT
                        eg.guild_id,
                        eg.notification_webhook_url,
                        eg.notification_button_g4l AS button_g4l,
                        eg.notification_button_sln AS button_sln,
                        se.scheduled_event_id
                    FROM
                        enabled_guilds AS eg
                    JOIN
                        ll2_events as le
                        ON le.ll2_id = %s
                    LEFT JOIN
                        ll2_agencies_filter as laf
                        ON laf.guild_id = eg.guild_id
                        AND laf.agency_id = le.agency_id
                    LEFT JOIN
                        scheduled_events AS se
                        ON se.guild_id = eg.guild_id
                        AND eg.notification_scheduled_event
                        AND se.ll2_id = le.ll2_id
                    WHERE
                        eg.notification_webhook_url IS NOT NULL
                        AND
                        laf.agency_id IS NULL
                        AND
                        {' AND '.join(settings)}
                    """,
                    (ll2_id,)
                )
                async for row in cur:
                    # Convert button settings to bools
                    row['button_g4l'] = bool(row['button_g4l'])
                    row['button_sln'] = bool(row['button_sln'])
                    yield row
