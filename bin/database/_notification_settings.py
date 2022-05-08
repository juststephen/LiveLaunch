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
        t0_change: bool = None,
        tbd: bool = None,
        tbc: bool = None,
        go: bool = None,
        liftoff: bool = None,
        hold: bool = None,
        end_status: bool = None,
        scheduled_event: bool = None,
        button_g4l: bool = None,
        button_sln: bool = None
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
        t0_change : bool, default: None
            Enable/disable notifications
            for when start changes.
        tbd : bool, default: None
            Enable/disable tbd
            notifications.
        tbc : bool, default: None
            Enable/disable tbc
            notifications.
        go : bool, default: None
            Enable/disable go
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
        button_g4l : bool, default: None
            Include/exclude a button
            to Go4Liftoff in notifications.
        button_sln : bool, default: None
            Include/exclude a button
            to Space Launch Now in notifications.
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
        # Update t0_change if given
        if t0_change is not None:
            cols.append('notification_t0_change=%s')
            args.append(t0_change)
        # Update tbd if given
        if tbd is not None:
            cols.append('notification_tbd=%s')
            args.append(tbd)
        # Update tbc if given
        if tbc is not None:
            cols.append('notification_tbc=%s')
            args.append(tbc)
        # Update go if given
        if go is not None:
            cols.append('notification_go=%s')
            args.append(go)
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
