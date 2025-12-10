import discord
from discord.ext import commands
import logging

from main import LiveLaunchBot

logger = logging.getLogger(__name__)

class LiveLaunchGuilds(commands.Cog):
    """
    Discord.py cog for keeping track of the guilds it is in.
    This is used by the dashboard.
    """
    def __init__(self, bot: LiveLaunchBot) -> None:
        self.bot = bot

    @commands.Cog.listener('on_ready')
    @commands.Cog.listener('on_resumed')
    async def sync_guilds(self) -> None:
        """
        Discord task for syncing guilds.
        """
        guild_ids = [guild.id for guild in self.bot.guilds]
        await self.bot.lldb.guild_sync(guild_ids)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """
        Listener for when the bot joins a guild.

        Parameters
        ----------
        guild : discord.Guild
            Joined guild.
        """
        await self.bot.lldb.guild_add(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        Listener for when a guild is removed from the bot.

        Parameters
        ----------
        guild : discord.Guild
            Removed guild.
        """
        await self.bot.lldb.guild_remove(guild.id)


async def setup(bot: LiveLaunchBot):
    await bot.add_cog(LiveLaunchGuilds(bot))
