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

    @commands.group()
    @commands.defer(ephemeral=True)
    async def newsfilter(self, ctx) -> None:
        """
        List, add and remove filters for news sites.
        """
        pass

    @newsfilter.command(name='list')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def newsfilter_list(self, ctx) -> None:
        """
        List filters for news sites.
        """
        # Guild ID
        guild_id = ctx.guild.id

        # Get all available filters
        filters_all = await self.bot.lldb.news_filter_list()

        # Get all filters enabled in the guild
        filters_guild = await self.bot.lldb.news_filter_list(
            guild_id=guild_id
        )

        # Create list embed
        embed = discord.Embed(
            color=0x00E8FF,
            description='When a news site filter is enabled it will not be posted.',
            title='News Site Filters'
        )
        # Add available filters
        if (filters_available := [i for i in filters_all if i not in filters_guild]):
            embed.add_field(
                name='Available',
                value='```' +
                    '\n'.join(f'{i}) {j}' for i, j in filters_available) +
                    '```'
            )
        # Add enabled filters
        if filters_guild:
            embed.add_field(
                name='Enabled',
                value='```' +
                    '\n'.join(f'{i}) {j}' for i, j in filters_guild) +
                    '```'
            )

        # Send list
        await ctx.send(
            embed=embed,
            ephemeral=True
        )

    @newsfilter.command(name='add')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def newsfilter_add(self, ctx, newssite: str) -> None:
        """
        Add a filter for news sites.

        Parameters
        ----------
        newssite : str
            Enable filter for
            this news site.
        """
        # Guild ID
        guild_id = ctx.guild.id

        # Check if guild has settings
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await ctx.send(
                'This guild has nothing enabled, can\'t add filters.',
                ephemeral=True
            )
            return

        # Split bulk into a list
        newssite = [i.strip() for i in newssite.split(',')]

        status_list = []
        for item in newssite:

            try:
                item = int(item)

            # Input is a string
            except:
                # Lowercase
                item = item.lower()

                # Add filter to the db by name
                status = await self.bot.lldb.news_filter_add(
                    guild_id,
                    news_site_name=item
                )

            # Input is an index number
            else:
                # Add filter to the db by index
                status = await self.bot.lldb.news_filter_add(
                    guild_id,
                    news_site_id=item
                )

            # Add to status list
            status_list.append(status)

        # Notify user
        if all(status_list):
            await ctx.send(
                f"Added news site filter(s): `{', '.join(newssite)}`.",
                ephemeral=True
            )
        elif not any(status_list):
            await ctx.send(
                f"News site filter(s) `{', '.join(newssite)}` doesn\'t/don\'t exist.",
                ephemeral=True
            )
        else:
            # Check failed / success
            successes = list(compress(newssite, status_list))
            fails = [i for i in newssite if i not in successes]
            # Send
            await ctx.send(
                f"Added news site filter(s): `{', '.join(successes)}`, "
                f"couldn\'t add site filter(s): `{', '.join(fails)}`.",
                ephemeral=True
            )

    @newsfilter.command(name='remove')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def newsfilter_remove(self, ctx, newssite: str) -> None:
        """
        Remove a filter for news sites.

        Parameters
        ----------
        newssite : str
            Disable filter for
            this news site.
        """
        # Guild ID
        guild_id = ctx.guild.id

        # Check if guild has settings
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await ctx.send(
                'This guild has nothing enabled, can\'t remove filters.',
                ephemeral=True
            )
            return

        # Split bulk into a list
        newssite = [i.strip() for i in newssite.split(',')]

        status_list = []
        for item in newssite:

            try:
                item = int(item)

            # Input is a string
            except:
                # Lowercase
                item = item.lower()

                # Remove filter to the db by name
                status = await self.bot.lldb.news_filter_remove(
                    guild_id,
                    news_site_name=item
                )

            # Input is an index number
            else:
                # Remove filter to the db by index
                status = await self.bot.lldb.news_filter_remove(
                    guild_id,
                    news_site_id=item
                )

            # Add to status list
            status_list.append(status)

        # Notify user
        if all(status_list):
            await ctx.send(
                f"Removed news site filter(s): `{', '.join(newssite)}`.",
                ephemeral=True
            )
        elif not any(status_list):
            await ctx.send(
                f"News site filter(s) `{', '.join(newssite)}` doesn\'t/don\'t exist.",
                ephemeral=True
            )
        else:
            # Check failed / success
            successes = list(compress(newssite, status_list))
            fails = [i for i in newssite if i not in successes]
            # Send
            await ctx.send(
                f"Removed news site filter(s): `{', '.join(successes)}`, "
                f"couldn\'t remove site filter(s): `{', '.join(fails)}`.",
                ephemeral=True
            )

    @newsfilter.error
    @newsfilter_list.error
    @newsfilter_add.error
    @newsfilter_remove.error
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

    @tasks.loop(minutes=5)
    async def fetch_news(self):
        """
        Discord task for fetching and
        sending new news articles.
        """
        # Get news articles
        news = await self.snapi()

        # Check if article is already sent, then generate embeds
        new_news = []
        for article in news:
            if await self.bot.lldb.sent_media_exists(snapi_id=article['id']):
                continue

            # Add `snapi_id` to the db to prevent resending
            await self.bot.lldb.sent_media_add(snapi_id=article['id'])

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

            # Add article to sending list
            new_news.append(article)

        # Only continue when there are new articles
        if not new_news:
            return

        # Sending
        async for guild_id, webhook_url in self.bot.lldb.enabled_guilds_news_iter():
            # Continue when a guild doesn't want any articles
            if not any(
                filters := [await self.bot.lldb.news_filter_check(guild_id, i['newsSite']) for i in new_news]
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
                    for article in compress(new_news, filters):
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