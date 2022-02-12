import aiohttp
import discord
from discord.ext import commands, tasks
from itertools import compress
import logging

from bin import SpaceflightNewsAPI

class LiveLaunchNews(commands.Cog):
    """
    Discord.py cog for reporting space news.
    """
    def __init__(self, bot):
        self.bot = bot
        # Spaceflight News API
        self.snapi = SpaceflightNewsAPI()
        # Start loops
        self.fetch_news.start()

    @tasks.loop(minutes=1)
    async def fetch_news(self):
        """
        Discord task for fetching and
        sending new news articles.
        """
        # Get new news articles
        news = await self.snapi()

        # Only continue when there are new articles
        if not news:
            return

        # Generate embeds
        for article in news:
            # Add the news site to the db if needed
            await self.bot.lldb.news_sites_add(article['newsSite'])

            # Create embed object
            embed = discord.Embed(
                color=0x00E8FF,
                description=article['summary'],
                timestamp=article['publishedAt'],
                title=article['title'],
                url=article['url']
            )
            # Set image
            embed.set_image(
                url=article['imageUrl']
            )
            # Set footer
            embed.set_footer(
                text='LiveLaunch News, Powered by SNAPI'
            )
            # Add to news dict
            article['embed'] = embed

        # Sending
        async for guild_id, webhook_url in self.bot.lldb.enabled_guilds_news_iter():
            # Continue when a guild doesn't want any articles
            if not any(
                filters := [await self.bot.lldb.news_filter_check(guild_id, i['newsSite']) for i in news]
            ):
                continue
            try:
                # Creating session
                async with aiohttp.ClientSession() as session:
                    # Creating webhook
                    webhook = discord.Webhook.from_url(
                        webhook_url,
                        session=session
                    )

                    # Sending filtered articles
                    for article in compress(news, filters):
                        await webhook.send(
                            embed=article['embed'],
                            username=article['newsSite']
                        )

            # Remove channel and url from the db when either is removed or deleted
            except discord.errors.NotFound:
                await self.bot.lldb.enabled_guilds_edit(
                    guild_id,
                    news_channel_id=None,
                    news_webhook_url=None
                )
                logging.warning(f'Guild ID: {guild_id}\tRemoved news webhook, not found.')
            # When the bot fails (edge case)
            except Exception as e:
                logging.warning(f'Guild ID: {guild_id}\tError during news webhook sending: {e}, {type(e)}')
                print(f'Guild ID: {guild_id}\tError during news webhook sending: {e}, {type(e)}')

    @fetch_news.before_loop
    async def before_loop(self):
        """
        Wait untill the database is loaded.
        """
        await self.bot.wait_until_ready()


def setup(client):
    client.add_cog(LiveLaunchNews(client))