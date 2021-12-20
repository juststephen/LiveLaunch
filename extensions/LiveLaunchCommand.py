import aiohttp
from discord import TextChannel, Webhook
from discord.ext import commands
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
    @commands.cooldown(1, 16)
    @commands.defer(ephemeral=True)
    async def enable(self, ctx,
        messages: TextChannel = None,
        events: int = None
    ):
        """
        Enable LiveLaunch features, only for administrators.

        Parameters
        ----------
        messages : discord.TextChannel, default: None
            Discord channel to send streams to.
        events : int, default: None
            Maximum amount of events to create if
            given, between 1 and 50.
        """
        # Rearange input when wrong
        if isinstance(messages, int) and events is None:
            events = messages
            messages = None

        async def create_webhook():
            """
            Create a webhook for the given channel.
            """
            # Read image for the avatar
            webhook_avatar = open(self.webhook_avatar_path, 'rb').read()
            # Try creating the webhook, otherwise send fail message and stop
            try:
                url = (await messages.create_webhook(name='LiveLaunch', avatar=webhook_avatar)).url
            except:
                await ctx.send('Failed to enable the messages feature', ephemeral=True)
            else:
                return url

        # Guild ID
        guild_id = ctx.guild.id

        # Check if it is already enabled in the guild
        settings = await self.bot.lldb.enabled_guilds_get(guild_id)

        # Existing entry, editing
        if settings:
            new_settings = {'guild_id': guild_id}

            # Webhook settings
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
                new_settings['channel_id'] = messages.id
                new_settings['webhook_url'] = await create_webhook()

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
            # Get channel ID and create a webhook if requested
            if messages:
                settings['channel_id'] = messages.id
                settings['webhook_url'] = await create_webhook()
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
    async def disable(self, ctx, features: str):
        """
        Disable LiveLaunch features, only for administrators.

        Parameters
        ----------
        features : str
            Features to disable,
            - options:
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

            # Remove the webhook if needed
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
            if ('webhook_url' and 'scheduled_events') in new_settings:
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
                    'Requested feature is arleady disabled',
                    ephemeral=True
                )

    @enable.error
    @disable.error
    async def command_error(self, ctx, error) -> None:
        """
        Method that handles interactions with non administrators for the enable/disable commands.
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


def setup(client):
    client.add_cog(LiveLaunchCommand(client))