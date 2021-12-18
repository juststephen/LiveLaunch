from datetime import datetime, timedelta
from discord.ext import commands, tasks

from bin import Database

class LiveLaunchDB(commands.Cog):
    """
    Discord.py cog for loading database methods.

    Notes
    -----
    The database can be accessed via
    the `.bot.lldb` variable.
    """
    def __init__(self, bot):
        self.bot = bot
        self.bot.lldb = Database()
        self.clean_database.start()

    def cog_unload(self):
        self.bot.lldb.pool.close()

    @tasks.loop(hours=24)
    async def clean_database(self):
        """
        Discord task for starting
        and cleaning up the database.
        """
        if not self.bot.lldb.started:
            await self.bot.lldb.start()
        # Clean
        await self.bot.lldb.sent_streams_clean()


def setup(client):
    client.add_cog(LiveLaunchDB(client))