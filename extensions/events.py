from discord.ext import commands

class LiveLaunchEvents(commands.Cog):
    """
    Discord.py cog for event commands.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    @commands.defer(ephemeral=True)
    async def event_settings(
        self,
        ctx,
        launches: str = None,
        events: str = None,
        no_url: str = None,
    ) -> None:
        """
        General notification settings.

        Parameters
        ----------
        events : bool, default: None
            Enable/disable other
            scheduled events.
        launches : bool, default: None
            Enable/disable launch
            scheduled events.
        no_url : bool, default: None
            Hide scheduled events
            without live stream URLs.
        """
        # Guild ID
        guild_id = ctx.guild.id

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await ctx.send(
                'Cannot update settings, nothing is enabled within this guild.',
                ephemeral=True
            )
            return

        settings = {}
        if events is not None:
            settings['event'] = events == 'True'
        if launches is not None:
            settings['launch'] = launches == 'True'
        if no_url is not None:
            settings['no_url'] = no_url == 'True'

        # Update database
        if settings:
            await self.bot.lldb.scheduled_events_settings_edit(guild_id, **settings)

        # Send reply
        await ctx.send(
            f'Changed event settings.',
            ephemeral=True
        )

    @event_settings.error
    async def command_error(self, ctx, error) -> None:
        """
        Method that handles erroneous interactions with the commands.
        """
        if isinstance(error, commands.errors.MissingPermissions):
            if ctx.prefix == '/':
                await ctx.send('This command is only for administrators.', ephemeral=True)
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send('This command is only for guild channels.')
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(
                f'This command is on cooldown for {error.retry_after:.0f} more seconds.',
                ephemeral=True
            )
        else:
            logging.warning(f'Command: {ctx.command}\nError: {error}')
            print(f'Command: {ctx.command}\nError: {error}')


def setup(client):
    client.add_cog(LiveLaunchEvents(client))
