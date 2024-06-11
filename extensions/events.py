from discord import app_commands, Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands
import logging

from bin import enums

class LiveLaunchEvents(commands.Cog):
    """
    Discord.py cog for event commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def event_settings(
        self,
        interaction: Interaction,
        events: enums.EnableDisable = None,
        launches: enums.EnableDisable = None,
        no_url: enums.HideShow = None,
    ) -> None:
        """
        Event settings, only for administrators.

        Parameters
        ----------
        events : enums.EnableDisable, default: None
            Enable/disable other
            scheduled events.
        launches : enums.EnableDisable, default: None
            Enable/disable launch
            scheduled events.
        no_url : enums.HideShow, default: None
            Hide/show scheduled events
            without live stream URLs.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        guild_id = interaction.guild_id

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'Cannot update settings, nothing is enabled within this guild.'
            )
            return

        settings = {}
        if events is not None:
            settings['event'] = events is enums.EnableDisable.Enable
        if launches is not None:
            settings['launch'] = launches is enums.EnableDisable.Enable
        if no_url is not None:
            settings['no_url'] = no_url is enums.HideShow.Hide

        # Update database
        if settings:
            await self.bot.lldb.scheduled_events_settings_edit(guild_id, **settings)

        # Send reply
        await interaction.followup.send('Changed event settings.')

    @event_settings.error
    async def command_error(
        self,
        interaction: Interaction,
        error: AppCommandError
    ) -> None:
        """
        Method that handles erroneous interactions with the commands.
        """
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                'This command is only for administrators.',
                ephemeral=True
            )
        elif isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown for {error.retry_after:.0f} more seconds.',
                ephemeral=True
            )
        else:
            logging.error(f'Command: {interaction.command}\tError: {error}')


async def setup(bot: commands.Bot):
    await bot.add_cog(LiveLaunchEvents(bot))
