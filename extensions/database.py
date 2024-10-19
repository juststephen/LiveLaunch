import aiohttp
from discord import Webhook
from discord.ext import commands, tasks
import logging

class LiveLaunchDB(commands.Cog):
    """
    Discord.py cog for cleaning up the database.
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.clean_database.start()

    @tasks.loop(hours=24)
    async def clean_database(self) -> None:
        """
        Discord task for cleaning up the database.
        """
        # Clean sent media
        await self.bot.lldb.sent_media_clean()

        # Clean guilds with an unused notifications webhook
        async_iter = self.bot.lldb.enabled_guilds_unused_notification_iter()
        async for guild_id, webhook_url in async_iter:

            # Create webhook connection for deletion
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(
                    webhook_url,
                    session=session
                )
                # Delete webhook
                try:
                    await webhook.delete()
                except:
                    pass

            # Update the guild settings
            await self.bot.lldb.enabled_guilds_edit(
                guild_id,
                notification_channel_id=None,
                notification_webhook_url=None
            )

            # Logging deletion of unused notification webhook
            logging.info(
                f'Guild ID: {guild_id}\tRemoved notification webhook, unused.'
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(LiveLaunchDB(bot))
