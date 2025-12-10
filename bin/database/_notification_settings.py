class NotificationSettings:
    """
    Access notification settings.
    """
    async def notification_settings_edit(
        self,
        guild_id : int,
        *,
        launch: bool | None = None,
        event: bool | None = None,
        t0_change: bool | None = None,
        tbd: bool | None = None,
        tbc: bool | None = None,
        go: bool | None = None,
        liftoff: bool | None = None,
        hold: bool | None = None,
        deploy: bool | None = None,
        end_status: bool | None = None,
        scheduled_event: bool | None = None
    ) -> None:
        """
        Modify the notification
        settings of a guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        launch : bool or None, default: None
            Enable/disable launch
            notifications.
        event : bool or None, default: None
            Enable/disable event
            notifications.
        t0_change : bool or None, default: None
            Enable/disable notifications
            for when start changes.
        tbd : bool or None, default: None
            Enable/disable tbd
            notifications.
        tbc : bool or None, default: None
            Enable/disable tbc
            notifications.
        go : bool or None, default: None
            Enable/disable go
            notifications.
        liftoff : bool or None, default: None
            Enable/disable launch
            liftoff notifications.
        hold : bool or None, default: None
            Enable/disable launch
            hold notifications.
        deploy : bool or None, default: None
            Enable/disable payload
            deployed status notifications.
        end_status : bool or None, default: None
            Enable/disable launch
            end status notifications.
        scheduled_event : bool or None, default: None
            Include/exclude Discord
            scheduled events in the
            notification when available.
        """
        cols: list[str] = []
        args: list[bool | int] = []
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
        # Update deploy if given
        if deploy is not None:
            cols.append('notification_deploy=%s')
            args.append(deploy)
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
        async with self.pool.acquire() as con, con.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE enabled_guilds
                SET {', '.join(cols)}
                WHERE guild_id=%s
                """,
                args
            )
