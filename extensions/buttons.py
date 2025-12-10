from discord import app_commands, Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands
import logging

from bin import enums
from main import LiveLaunchBot

logger = logging.getLogger(__name__)

class LiveLaunchButtons(commands.Cog):
    """
    Discord.py cog for the button setting command.
    """
    def __init__(self, bot: LiveLaunchBot):
        self.bot = bot

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def button_settings(
        self,
        interaction: Interaction,
        button_fc: enums.IncludeExclude | None = None,
        button_g4l: enums.IncludeExclude | None = None,
        button_sln: enums.IncludeExclude | None = None,
    ) -> None:
        """
        Button settings, only for administrators.

        Parameters
        ----------
        button_fc : enums.IncludeExclude or None, default: None
            Include/exclude a button to Flight Club.
        button_g4l : enums.IncludeExclude or None, default: None
            Include/exclude a button to Go4Liftoff.
        button_sln : enums.IncludeExclude or None, default: None
            Include/exclude a button to Space Launch Now.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        if (guild_id := interaction.guild_id) is None:
            raise TypeError('guild_id should never be None')

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'Cannot update settings, nothing is enabled within this guild.'
            )
            return

        # Select desired button settings
        settings: dict[str, bool] = {}
        if button_fc is not None:
            settings['button_fc'] = button_fc is enums.IncludeExclude.Include
        if button_g4l is not None:
            settings['button_g4l'] = button_g4l is enums.IncludeExclude.Include
        if button_sln is not None:
            settings['button_sln'] = button_sln is enums.IncludeExclude.Include

        # Update database
        if settings:
            await self.bot.lldb.button_settings_edit(guild_id, **settings)

        # Send reply
        await interaction.followup.send('Changed button settings.')

    @button_settings.error
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
            logger.error(error)


async def setup(bot: LiveLaunchBot):
    await bot.add_cog(LiveLaunchButtons(bot))
