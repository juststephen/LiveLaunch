class ScheduledEventsSettings:
    """
    Methods for chaning the Discord scheduled
    events settings in the enabled_guilds table.
    """
    async def scheduled_events_settings_edit(
        self,
        guild_id,
        *,
        launch: bool = None,
        event: bool = None,
        no_url: bool = None
    ) -> None:
        """
        Modify the scheduled events
        settings of a guild.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        launch : bool, default: None
            Enable/disable launch
            scheduled events.
        event : bool, default: None
            Enable/disable event
            scheduled events.
        no_url : bool, default: None
            Enable/disable scheduled
            events without a URL.
        """
        cols, args = [], []
        # Update launch if given
        if launch is not None:
            cols.append('se_launch=%s')
            args.append(launch)
        # Update event if given
        if event is not None:
            cols.append('se_event=%s')
            args.append(event)
        # Update no_url if given
        if no_url is not None:
            cols.append('se_no_url=%s')
            args.append(no_url)
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
