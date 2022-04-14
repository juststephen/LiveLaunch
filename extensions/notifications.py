import aiohttp
import discord
from discord.ext import commands, tasks
from discord.ui import Button, MessageComponents, ActionRow
import logging

from bin import (
    convert_minutes,
    LaunchLibrary2 as ll2
)

class LiveLaunchNotifications(commands.Cog):
    """
    Discord.py cog for sending notifications.
    """
    def __init__(self, bot):
        self.bot = bot
        # Scheduled event base url
        self.se_url = 'https://discord.com/events/%s/%s'
        # Start loops
        self.countdown_notifications.start()

    @commands.group()
    @commands.defer(ephemeral=True)
    async def notifications(self, ctx) -> None:
        """
        Main notification settings group.
        """
        pass

    @notifications.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def general(
        self,
        ctx,
        events: str = None,
        everything: str = None,
        launches: str = None,
        include_scheduled_events: str = None
    ) -> None:
        """
        General notification settings.

        Parameters
        ----------
        events : bool, default: None
            Enable/disable event
            notifications.
        everything : bool, default: None
            Enable/disable everything.
        launches : bool, default: None
            Enable/disable launch
            notifications.
        include_scheduled_events : bool, default: None
            Include/exclude Discord
            scheduled events in the
            notification when available.
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

        # Select desired settings
        if everything is not None:
            message = 'all'
            everything = everything == 'True'
            settings = {
                'launch': everything,
                'event': everything,
                'liftoff': everything,
                'hold': everything,
                'end_status': everything,
                'scheduled_event': everything
            }
        else:
            message = 'selected general'
            settings = {}
            if events is not None:
                settings['event'] = events == 'True'
            if launches is not None:
                settings['launch'] = launches == 'True'
            if include_scheduled_events is not None:
                settings['scheduled_event'] = include_scheduled_events == 'True'

        # Update database
        if settings:
            await self.bot.lldb.notification_settings_edit(guild_id, **settings)

        # Send reply
        await ctx.send(
            f'Changed {message} notification settings.',
            ephemeral=True
        )

    @notifications.group()
    async def countdown(self, ctx) -> None:
        """
        Group for the countdown setting commands.
        """
        pass

    @countdown.command(name='list')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def countdown_list(self, ctx) -> None:
        """
        List countdown time settings.
        """
        # Fetch settings
        settings = await self.bot.lldb.notification_countdown_list(ctx.guild.id)

        # When there are none
        if not settings:
            await ctx.send(
                'No countdown notification settings created yet.',
                ephemeral=True
            )
            return

        # Create list embed
        embed = discord.Embed(
            color=0x00E8FF,
            description='All active countdown times for notifications.'
                '\nThe index can be used to remove countdown times.',
            title='Countdown list'
        )
        # Add countdown settings
        embed.add_field(
            name='List:',
            value='```index) time```\n```' +
                '\n'.join(f'{i}) {convert_minutes(j)}' for i, j in settings) +
                '```'
        )

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @countdown.command(name='add')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 4)
    async def countdown_add(
        self,
        ctx,
        days: int = None,
        hours: int = None,
        minutes: int = None
    ) -> None:
        """
        Add a countdown time setting.

        Parameters
        ----------
        days : int, default: None
            Amount of days.
        hours : int, default: None
            Amount of hours.
        minutes : int, default: None
            Amount of minutes.
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

        # Maximum check
        if await self.bot.lldb.notification_countdown_check(guild_id):
            await ctx.send(
                'Maximum amount (64) of countdowns already active.',
                ephemeral=True
            )
            return

        # Convert all to minutes
        days = 0 if days is None else days
        hours = 0 if hours is None else hours
        minutes = 0 if minutes is None else minutes
        minutes += ( days * 24 + hours ) * 60

        # Update database when more than 0
        if minutes:
            await self.bot.lldb.notification_countdown_add(ctx.guild.id, minutes)
            # Send reply
            await ctx.send(
                'Added countdown setting.',
                ephemeral=True
            )
        else:
            # Send reply
            await ctx.send(
                'Countdown times have a minimum of 1 minute.',
                ephemeral=True
            )

    @countdown.command(name='remove')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def countdown_remove(
        self,
        ctx,
        index: int
    ) -> None:
        """
        Remove a countdown time setting.

        Parameters
        ----------
        index : int
            Index of the time
            when sorting minutes
            by ascending.
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

        # Update database
        await self.bot.lldb.notification_countdown_remove(ctx.guild.id, index)
        # Send reply

        await ctx.send(
            'Removed countdown setting.',
            ephemeral=True
        )

    @notifications.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def launch_status(
        self,
        ctx,
        end_status: str = None,
        hold: str = None,
        liftoff: str = None
    ) -> None:
        """
        Enable/disable notifications
        related to launch status changes.

        Parameters
        ----------
        end_status: str, default: None
            Enable/disable final
            status notifications.
        hold : str, default: None
            Enable/disable launch
            hold notifications.
        liftoff : str, default: None
            Enable/disable liftoff
            notifications.
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

        # Select desired settings
        settings = {}
        if end_status is not None:
            settings['end_status'] = end_status == 'True'
        if hold is not None:
            settings['hold'] = hold == 'True'
        if liftoff is not None:
            settings['liftoff'] = liftoff == 'True'

        # Update database
        if settings:
            await self.bot.lldb.notification_settings_edit(guild_id, **settings)

        # Send reply
        await ctx.send(
            f'Changed selected launch status notification settings.',
            ephemeral=True
        )

    @general.error
    @countdown_list.error
    @countdown_add.error
    @countdown_remove.error
    @launch_status.error
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

    @tasks.loop(minutes=1)
    async def countdown_notifications(self):
        """
        Discord task for sending
        countdown notifications.
        """
        async for notification in self.bot.lldb.notification_countdown_iter():
            guild_id = notification['guild_id']
            status = notification['status']

            # Only enable video URL when available
            if (url := notification['url']):
                url = f'[Stream]({url})'
            else:
                url = ll2.no_stream

            # Select the correct SLN base URL
            if notification['type']:
                base_url = ll2.sln_event_url
            else:
                base_url = ll2.sln_launch_url

            # Message dict
            message = {}

            # Creating embed
            embed = discord.Embed(
                color=ll2.status_colours.get(notification['status'], 0xFFFF00),
                description=f"**T-{convert_minutes(notification['minutes'])}**\n" +
                    (f'**Status:** {ll2.status_names[status]}\n{url}' if status else url),
                timestamp=notification['start'],
                title=notification['name'],
                url=base_url % notification['ll2_id']
            )
            # Add a thumbnail when scheduled events aren't enabled
            if (notification['scheduled_event_id'] is None
                    and notification['image_url']):
                # Set image
                embed.set_thumbnail(
                    url=notification['image_url']
                )
            # Set footer
            embed.set_footer(
                text='LiveLaunch Notifications'
            )
            message['embed'] = embed

            # Scheduled event
            if notification['scheduled_event_id']:
                message['content'] = self.se_url % (
                    notification['guild_id'],
                    notification['scheduled_event_id']
                )

            try:
                # Creating session
                async with aiohttp.ClientSession() as session:
                    # Creating webhook
                    webhook = discord.Webhook.from_url(
                        notification['notification_webhook_url'],
                        session=session
                    )

                    # Sending notification
                    await webhook.send(
                        **message,
                        username=notification['agency'],
                        avatar_url=notification['logo_url']
                    )

            # Remove channel and url from the db when either is removed or deleted
            except discord.errors.NotFound:
                await self.bot.lldb.enabled_guilds_edit(
                    guild_id,
                    notification_channel_id=None,
                    notification_webhook_url=None
                )
                logging.warning(f'Guild ID: {guild_id}\tRemoved notification webhook, not found.')
            # When the bot fails (edge case)
            except Exception as e:
                logging.warning(f'Guild ID: {guild_id}\tError during notification webhook sending: {e}, {type(e)}')
                print(f'Guild ID: {guild_id}\tError during notification webhook sending: {e}, {type(e)}')

    @countdown_notifications.before_loop
    async def before_loop(self):
        """
        Wait untill the database is loaded.
        """
        await self.bot.wait_until_ready()


def setup(client):
    client.add_cog(LiveLaunchNotifications(client))