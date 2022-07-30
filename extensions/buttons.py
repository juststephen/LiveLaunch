from discord.ext import commands
import logging

class LiveLaunchButtons(commands.Cog):
    """
    Discord.py cog for the button setting command.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    @commands.defer(ephemeral=True)
    async def button_settings(
        self,
        ctx,
        button_fc: str = None,
        button_g4l: str = None,
        button_sln: str = None,
    ) -> None:
        """
        Button settings.

        Parameters
        ----------
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
        # Guild ID
        guild_id = ctx.guild.id

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await ctx.send(
                'Cannot update settings, nothing is enabled within this guild.',
                ephemeral=True
            )
            return

        # Select desired button settings
        settings = {}
        if button_fc is not None:
            settings['button_fc'] = button_fc == 'True'
        if button_g4l is not None:
            settings['button_g4l'] = button_g4l == 'True'
        if button_sln is not None:
            settings['button_sln'] = button_sln == 'True'

        # Update database
        if settings:
            await self.bot.lldb.button_settings_edit(guild_id, **settings)

        # Send reply
        await ctx.send(
            f'Changed button settings.',
            ephemeral=True
        )

    @button_settings.error
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
    client.add_cog(LiveLaunchButtons(client))
