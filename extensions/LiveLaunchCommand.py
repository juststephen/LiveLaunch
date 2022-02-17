import aiohttp
from discord import (
    Embed,
    Permissions,
    TextChannel,
    Webhook
)
from discord.errors import Forbidden
from discord.ext import commands
from itertools import compress
import logging

class LiveLaunchCommand(commands.Cog):
    """
    Discord.py cog for enabling/disabling LiveLaunch in a Discord channel.
    """
    def __init__(self, bot):
        self.bot = bot
        # Settings
        self.webhook_avatar_path = 'LiveLaunch_Webhook_Avatar.png'

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(
        manage_webhooks=True,
        manage_events=True,
        send_messages=True,
        embed_links=True
    )
    @commands.cooldown(1, 16)
    @commands.defer(ephemeral=True)
    async def enable(
        self,
        ctx,
        news: TextChannel = None,
        messages: TextChannel = None,
        events: int = None
    ) -> None:
        """
        Enable LiveLaunch features, only for administrators.

        Parameters
        ----------
        news : discord.TextChannel, default: None
            Discord channel to send news to.
        messages : discord.TextChannel, default: None
            Discord channel to send streams to.
        events : int, default: None
            Maximum amount of events to create if
            given, between 1 and 50.
        """
        async def create_webhook(channel: TextChannel, *, feature: str) -> None:
            """
            Create a webhook for the given channel.

            Parameters
            ----------
            channel : TextChannel
                Text channel to
                add webhook in.
            feature : str
                Feature to mention
                when it fails.
            """
            # Read image for the avatar
            webhook_avatar = open(self.webhook_avatar_path, 'rb').read()
            # Try creating the webhook, otherwise send fail message and stop
            try:
                url = (await channel.create_webhook(
                    name=f'LiveLaunch {feature}',
                    avatar=webhook_avatar
                )).url
            except Forbidden:
                await ctx.send(
                    'LiveLaunch requires the `Manage Webhooks`, '
                    '`Send Messages` and `Embed Links` permissions for '
                    'the `messages` feature in the specified channel.'
                )
            except:
                await ctx.send(
                    f'Failed to enable the {feature} feature',
                    ephemeral=True
                )
            else:
                return url

        # Guild ID
        guild_id = ctx.guild.id

        # Check if it is already enabled in the guild
        settings = await self.bot.lldb.enabled_guilds_get(guild_id)

        # Existing entry, editing
        if settings:
            new_settings = {'guild_id': guild_id}

            # Webhook news settings
            if news:
                # Move messages to another channel if there was a previous one
                if news.id != settings['news_channel_id'] and settings['news_channel_id']:

                    # Create webhook for deletion
                    async with aiohttp.ClientSession() as session:
                        webhook = Webhook.from_url(
                            settings['news_webhook_url'],
                            session=session
                        )
                        # Delete webhook
                        try:
                            await webhook.delete()
                        except:
                            pass

                # Add new data
                news_webhook_url = await create_webhook(news, feature='News')
                if news_webhook_url is None:
                    return
                else:
                    new_settings['news_channel_id'] = news.id
                    new_settings['news_webhook_url'] = news_webhook_url

            # Webhook stream settings
            if messages:
                # Move messages to another channel if there was a previous one
                if messages.id != settings['channel_id'] and settings['channel_id']:

                    # Create webhook for deletion
                    async with aiohttp.ClientSession() as session:
                        webhook = Webhook.from_url(
                            settings['webhook_url'],
                            session=session
                        )
                        # Delete webhook
                        try:
                            await webhook.delete()
                        except:
                            pass

                # Add new data
                webhook_url = await create_webhook(messages, feature='Messages')
                if webhook_url is None:
                    return
                else:
                    new_settings['channel_id'] = messages.id
                    new_settings['webhook_url'] = webhook_url

            # Event settings
            if events:
                new_settings['scheduled_events'] = events

            # Existing entry, edit row
            await self.bot.lldb.enabled_guilds_edit(
                **new_settings
            )

            # Notify user
            await ctx.send(
                'Features updated',
                ephemeral=True
            )

        # New entry
        else:
            settings = {'guild_id': guild_id}

            # Get channel ID and create a news if requested
            if news:
                news_webhook_url = await create_webhook(news, feature='News')
                if news_webhook_url is None:
                    return
                else:
                    settings['news_channel_id'] = news.id
                    settings['news_webhook_url'] = news_webhook_url

            # Get channel ID and create a stream webhook if requested
            if messages:
                webhook_url = await create_webhook(messages, feature='Messages')
                if webhook_url is None:
                    return
                else:
                    settings['channel_id'] = messages.id
                    settings['webhook_url'] = webhook_url

            # Amount of Discord scheduled events if requested
            if events:
                settings['scheduled_events'] = events
            else:
                settings['scheduled_events'] = 0

            # Add to the database
            await self.bot.lldb.enabled_guilds_add(
                **settings
            )

            # Notify user
            await ctx.send(
                'Requested features are now enabled',
                ephemeral=True
            )

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 16)
    @commands.defer(ephemeral=True)
    async def disable(self, ctx, features: str) -> None:
        """
        Disable LiveLaunch features, only for administrators.

        Parameters
        ----------
        features : str
            Features to disable,
            - options:
                - ` news `:
                    Disable news sending.
                - ` messages `:
                    Disable stream sending.
                - ` events `:
                    Disable event creation.
                - ` all `:
                    Disable everything.
        """
        # Guild ID
        guild_id = ctx.guild.id

        # Check if it is even enabled in the channel
        if not (settings := await self.bot.lldb.enabled_guilds_get(guild_id)):
            await ctx.send(
                'No features are enabled',
                ephemeral=True
            )
        else:
            new_settings = {'guild_id': guild_id}

            # Remove the news webhook if needed
            if features in ('news', 'all') and settings['news_webhook_url']:
                # Create webhook for deletion
                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(
                        settings['news_webhook_url'],
                        session=session
                    )
                    # Delete webhook
                    try:
                        await webhook.delete()
                    except:
                        pass

                new_settings['news_channel_id'] = None
                new_settings['news_webhook_url'] = None

            # Remove the stream webhook if needed
            if features in ('messages', 'all') and settings['webhook_url']:
                # Create webhook for deletion
                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(
                        settings['webhook_url'],
                        session=session
                    )
                    # Delete webhook
                    try:
                        await webhook.delete()
                    except:
                        pass

                new_settings['channel_id'] = None
                new_settings['webhook_url'] = None

            # Remove the events feature if needed
            if features in ('events', 'all') and settings['scheduled_events']:
                new_settings['scheduled_events'] = 0

            # Remove row from the database
            if all(
                i in new_settings for i in (
                    'webhook_url',
                    'scheduled_events',
                    'news_webhook_url'
                )
            ):
                # Update database
                await self.bot.lldb.enabled_guilds_edit(
                    **new_settings
                )
                # Notify user
                await ctx.send(
                    'All features are now disabled',
                    ephemeral=True
                )
            # Update row, other feature stays enabled
            elif len(new_settings) > 1:
                # Update database
                await self.bot.lldb.enabled_guilds_edit(
                    **new_settings
                )
                # Notify user
                await ctx.send(
                    'Requested features are now disabled',
                    ephemeral=True
                )
            else:
                # Notify user
                await ctx.send(
                    'Requested feature is already disabled',
                    ephemeral=True
                )

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 1024)
    @commands.defer(ephemeral=True)
    async def synchronize(self, ctx) -> None:
        """
        Manually synchronize LiveLaunch events, only for administrators.
        """
        # Amount of unsynchronized scheduled events
        amount = 0

        # Guild ID
        guild_id = ctx.guild.id

        # Get guild's Discord scheduled events
        discord_events = await self.bot.http.list_guild_scheduled_events(guild_id)

        # Get a list of the scheduled event IDs only made by the bot itself
        discord_events = [
            int(i['id']) for i in discord_events \
            if int(i['creator_id']) == self.bot.application_id
        ]

        # Get guild's scheduled events cached in the database
        async for scheduled_event_id in self.bot.lldb.scheduled_events_guild_id_iter(guild_id):
            # Check if the event still exists
            if scheduled_event_id not in discord_events:
                # Increment amount
                amount += 1
                # Remove scheduled_event_id from the database
                await self.bot.lldb.scheduled_events_remove(
                    scheduled_event_id
                )

        # Notify user
        await ctx.send(
            f"Synchronized, {amount} event{'s are' if amount != 1 else ' is'} missing.",
            ephemeral=True
        )

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
        embed = Embed(
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

    @enable.error
    @disable.error
    @synchronize.error
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
        elif isinstance(error, commands.errors.BotMissingPermissions):
            await ctx.send(
                'LiveLaunch requires the `Manage Webhooks`, `Manage Events`, '
                '`Send Messages` and `Embed Links` permissions.'
            )
        else:
            logging.warning(f'Command: {ctx.command}\nError: {error}')
            print(f'Command: {ctx.command}\nError: {error}')


def setup(client):
    client.add_cog(LiveLaunchCommand(client))
