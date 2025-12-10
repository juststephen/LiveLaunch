from discord import app_commands, Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands
import logging

from main import LiveLaunchBot

logger = logging.getLogger(__name__)

class LiveLaunchDashboard(commands.Cog):
    """
    Discord.py cog for linking to the dashboard.
    """
    def __init__(self, bot: LiveLaunchBot):
        self.bot = bot

    @app_commands.command()
    async def dashboard(self, interaction: Interaction):
        """
        LiveLaunch dashboard link.
        """
        await interaction.response.send_message(
            '**[Dashboard](https://livelaunch.juststephen.com/)**',
            ephemeral=True
        )

    @dashboard.error
    async def dashboard_error(
        self,
        interaction: Interaction,
        error: AppCommandError
    ) -> None:
        """
        Method that handles erroneous interactions.
        """
        logger.error(error)


async def setup(bot: LiveLaunchBot):
    await bot.add_cog(LiveLaunchDashboard(bot))
