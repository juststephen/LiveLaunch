class NotificationSettings:
    """
    Access notification settings.
    """
    async def notification_settings_edit(
        self,
        guild_id,
        *,
        launch: bool = None,
        event: bool = None,
        liftoff: bool = None,
        hold: bool = None,
        end_status: bool = None,
        scheduled_event: bool = None
    ) -> None:
        """
        Modify the notification
        settings of a guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        launch : bool, default: None
            Enable/disable launch
            notifications.
        event : bool, default: None
            Enable/disable event
            notifications.
        liftoff : bool, default: None
            Enable/disable launch
            liftoff notifications.
        hold : bool, default: None
            Enable/disable launch
            hold notifications.
        end_status : bool, default: None
            Enable/disable launch
            end status notifications.
        scheduled_event : bool, default: None
            Include/exclude Discord
            scheduled events in the
            notification when available.
        """
        cols, args = [], []
        # Update launch if given
        if launch is not None:
            cols.append('notification_launch=%s')
            args.append(launch)
        # Update event if given
        if event is not None:
            cols.append('notification_event=%s')
            args.append(event)
        # Update liftoff if given
        if liftoff is not None:
            cols.append('notification_liftoff=%s')
            args.append(liftoff)
        # Update hold if given
        if hold is not None:
            cols.append('notification_hold=%s')
            args.append(hold)
        # Update end_status if given
        if end_status is not None:
            cols.append('notification_end_status=%s')
            args.append(end_status)
        # Update scheduled_event if given
        if scheduled_event is not None:
            cols.append('notification_scheduled_event=%s')
            args.append(scheduled_event)
        # Add guild ID to the arguments
        args.append(guild_id)

        # Update db
        with await self.pool as con:
            async with con.cursor() as cur:
                await cur.execute(
                    f"""
                    UPDATE enabled_guilds
                    SET {', '.join(cols)}
                    WHERE guild_id=%s
                    """,
                    args
                )
