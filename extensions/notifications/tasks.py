import aiohttp
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import logging

from bin import (
    convert_minutes,
    LaunchLibrary2 as ll2
)

class LiveLaunchNotificationsTasks(commands.Cog):
    """
    Discord.py cog for sending notifications.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Scheduled event base url
        self.se_url = 'https://discord.com/events/%s/%s'
        # Start loops
        self.countdown_notifications.start()

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
                title_url = {'url': url}
                url = f'[Stream]({url})'
            else:
                title_url = {}
                url = ll2.no_stream

            # Select the correct G4L and SLN base URL
            if notification['type']:
                g4l_url = ll2.g4l_event_url
                sln_url = ll2.sln_event_url
            else:
                g4l_url = ll2.g4l_launch_url
                sln_url = ll2.sln_launch_url

            # Message dict
            message = {}

            # FC, G4L and SLN buttons for the event
            buttons = []
            # Add SLN button
            if notification['button_sln']:
                buttons.append(
                    Button(
                        label=ll2.sln_name,
                        style=discord.ButtonStyle.link,
                        emoji=ll2.sln_emoji,
                        url=sln_url % notification['slug']
                    )
                )
            # Add G4L button
            if notification['button_g4l']:
                buttons.append(
                    Button(
                        label=ll2.g4l_name,
                        style=discord.ButtonStyle.link,
                        emoji=ll2.g4l_emoji,
                        url=g4l_url % notification['ll2_id']
                    )
                )
            # Add FC button
            if notification['button_fc']:
                buttons.append(
                    Button(
                        label=ll2.fc_name,
                        style=discord.ButtonStyle.link,
                        emoji=ll2.fc_emoji,
                        url=ll2.fc_url % notification['ll2_id']
                    )
                )
            # Add to the message
            if buttons:
                message['view'] = View()
                for i in buttons:
                    message['view'].add_item(i)

            # Creating embed
            embed = discord.Embed(
                color=ll2.status_colours.get(status, 0xFFFF00),
                description=f"**T-{convert_minutes(notification['minutes'])}**\n" +
                    (f'**Status:** {ll2.status_names[status]}\n{url}' if status else url),
                timestamp=notification['start'],
                title=notification['name'],
                **title_url
            )
            # Set thumbnail
            if notification['image_url']:
                embed.set_thumbnail(
                    url=notification['image_url']
                )
            # Set footer
            embed.set_footer(
                text='LiveLaunch Notifications, powered by LL2'
            )
            message['embed'] = embed

            # Scheduled event
            if notification['scheduled_event_id']:
                message['content'] = self.se_url % (
                    guild_id,
                    notification['scheduled_event_id']
                )

            try:
                # Creating session
                async with aiohttp.ClientSession() as session:
                    # Creating webhook with the client to be able to send buttons
                    webhook = discord.Webhook.from_url(
                        notification['notification_webhook_url'],
                        client=self.bot,
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
                logging.info(f'Guild ID: {guild_id}\tRemoved notification webhook, not found.')
            # When the bot fails (edge case)
            except Exception as e:
                logging.error(f'Guild ID: {guild_id}\tError during notification webhook sending: {e}, {type(e)}')


async def setup(bot: commands.Bot):
    await bot.add_cog(LiveLaunchNotificationsTasks(bot))
