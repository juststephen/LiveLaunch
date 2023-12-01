from datetime import datetime
import discord
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, Range
from discord.ext import commands
from discord.ui import Button, View
import logging
import re

from bin import LaunchLibrary2 as ll2

class LiveLaunchNext(commands.Cog):
    """
    Discord.py cog for the next launch and event commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Regex check for type checking
        self.type_check = re.compile('^[0-9]+$')
        # Scheduled event base url
        self.se_url = 'https://discord.com/events/%s/%s'

    async def create_buttons(
        self,
        button_settings: dict[str, bool],
        ll2_id: str,
        slug: str
    ) -> View:
        """
        Create buttons if required.

        Parameters
        ----------
        button_settings : dict[str, bool]
            Settings for the buttons.
        ll2_id : str
            Launch Library 2 ID.
        slug : str
            Slug of the event.

        Returns
        -------
        buttons : View
            Created buttons.
        """
        # Select the correct G4L and SLN base URL
        if self.type_check.match(ll2_id):
            g4l_url = ll2.g4l_event_url
            sln_url = ll2.sln_event_url
        else:
            g4l_url = ll2.g4l_launch_url
            sln_url = ll2.sln_launch_url

        # FC, G4L and SLN buttons for the event
        buttons = []
        # Add SLN button
        if button_settings['button_sln']:
            buttons.append(
                Button(
                    label=ll2.sln_name,
                    style=discord.ButtonStyle.link,
                    emoji=ll2.sln_emoji,
                    url=sln_url % slug
                )
            )
        # Add G4L button
        if button_settings['button_g4l']:
            buttons.append(
                Button(
                    label=ll2.g4l_name,
                    style=discord.ButtonStyle.link,
                    emoji=ll2.g4l_emoji,
                    url=g4l_url % ll2_id
                )
            )
        # Add FC button
        if button_settings['button_fc']:
            buttons.append(
                Button(
                    label=ll2.fc_name,
                    style=discord.ButtonStyle.link,
                    emoji=ll2.fc_emoji,
                    url=ll2.fc_url % ll2_id
                )
            )

        # Create buttons if they exist
        if buttons:
            view = View()
            for i in buttons:
                view.add_item(i)
            # Return
            return view

    def create_single_embed(
        self,
        item: dict[str, bool and datetime and int and str]
    ) -> discord.Embed:
        """
        Create the embed with
        the given items.

        Parameters
        ----------
        item : dict[str, bool and datetime and int and str]
            Item for in the message.

        Returns
        -------
        embed : discord.Embed
            Created embed.
        """
        status = item.get('status')

        # Only enable video URL when available
        if (url := item['url']):
            title_url = {'url': url}
            url = f'[Stream]({url})'
        else:
            title_url = {}
            url = ll2.no_stream

        # Creating embed
        embed = discord.Embed(
            color=ll2.status_colours.get(status, 0xFFFF00),
            description=f"<t:{int(item['start'].timestamp())}:F>\n"
                f"{item['location']}\n{url}",
            timestamp=item['start'],
            title=item['name'],
            **title_url
        )
        # Set thumbnail
        if item['image_url']:
            embed.set_thumbnail(
                url=item['image_url']
            )
        # Set footer
        embed.set_footer(
            text='LiveLaunch, powered by LL2'
        )

        return embed

    def create_multi_embed(
        self,
        items: dict[str, dict[str, bool and datetime and int and str]],
        events: bool = False,
        launches: bool = False
    ) -> discord.Embed:
        """
        Create the embed with
        the given items.

        Parameters
        ----------
        items : dict[str, dict[str, bool and datetime and int and str]]
            Items for in the message.
        events : bool, default: False
            Select events only.
        launches : bool, default: False
            Select launches only.

        Returns
        -------
        embed : discord.Embed
            Created embed.
        """
        # Select the event type
        if events:
            type_name = 'events'
        elif launches:
            type_name = 'launches'

        # Creating embed
        embed = discord.Embed(
            color=0x00E8FF,
            title=f'Next {len(items)} {type_name}'
        )
        # Set footer
        embed.set_footer(
            text='LiveLaunch, powered by LL2'
        )

        # Add fields
        for item in items.values():
            # Get status
            status = item.get('status')

            # Only enable video URL when available
            if (url := item['url']):
                url = f'[Stream]({url})'
            else:
                url = ll2.no_stream

            # Add field
            embed.add_field(
                name=item['name'],
                value=f"<t:{int(item['start'].timestamp())}:F>\n"
                    f"{item['location']}\n{url}",
                inline=False
            )

        return embed

    async def next(
        self,
        interaction: Interaction,
        amount: int,
        events: bool = False,
        launches: bool = False
    ) -> None:
        """
        Reply with the upcoming items.

        Parameters
        ----------
        amount : int
            Amount to return.
        events : bool, default: False
            Select events only.
        launches : bool, default: False
            Select launches only.
        """
        # Check if the command was issued in a DM
        dm = isinstance(interaction.channel, discord.abc.PrivateChannel)

        # Defer
        await interaction.response.defer(ephemeral=dm, thinking=True)

        # Check if the cache exists, only happens at startup
        if not hasattr(self.bot, 'll2') or not hasattr(self.bot.ll2, 'cache'):
            await interaction.followup.send('The bot is starting up, please retry later.')
            return

        # Guild ID
        guild_id = None if dm else interaction.guild_id

        # Get events
        ll2_ids = await self.bot.lldb.ll2_events_next(
            guild_id,
            amount,
            events=events,
            launches=launches
        )

        # Reply when nothing is found
        if ll2_ids is None:
            await interaction.followup.send(
                f"No {'events' if events else 'launches'} found."
            )
            return

        # Get items
        items = {i: self.bot.ll2.cache[i] for i in ll2_ids}

        # Message dictionary
        message = {}

        # Amount is 1
        if amount == 1:
            ll2_id = ll2_ids[0]

            # Potentially add a URL to the Discord event
            if (guild_id is not None
                    and (se_id := await self.bot.lldb.scheduled_events_get(guild_id, ll2_id))):
                message['content'] = self.se_url % (
                    guild_id,
                    se_id
                )

            # Create embed
            message['embed'] = self.create_single_embed(items[ll2_id])

            # Request button settings
            if guild_id is not None:
                button_settings = await self.bot.lldb.button_settings_get(
                    guild_id,
                    ll2_id
                )
            else:
                button_settings = None

            # Fallback default button settings
            if button_settings is None:
                button_settings = {
                    'button_fc': items[ll2_id]['flightclub'],
                    'button_g4l': True,
                    'button_sln': True
                }

            # Create buttons
            if (buttons := await self.create_buttons(button_settings, ll2_id, items[ll2_id]['slug'])):
                message['view'] = buttons

        # Amount > 1
        else:
            # Create embed
            message['embed'] = self.create_multi_embed(
                items,
                events=events,
                launches=launches
            )

        # Reply
        await interaction.followup.send(**message)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 8)
    async def nextevent(
        self,
        interaction: Interaction,
        amount: Range[int, 1, 10] = 1
    ) -> None:
        """
        Show upcoming events.

        Parameters
        ----------
        amount : Range[int, 1, 10], default: 1
            Amount of events [1-10].
        """
        await self.next(interaction, amount, events=True)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 8)
    async def nextlaunch(
        self,
        interaction: Interaction,
        amount: Range[int, 1, 10] = 1
    ) -> None:
        """
        Show upcoming launches.

        Parameters
        ----------
        amount : Range[int, 1, 10], default: 1
            Amount of events [1-10].
        """
        await self.next(interaction, amount, launches=True)

    @nextevent.error
    @nextlaunch.error
    async def command_error(
        self,
        interaction: Interaction,
        error: AppCommandError
    ) -> None:
        """
        Method that handles erroneous interactions with the commands.
        """
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown for {error.retry_after:.0f} more seconds.',
                ephemeral=True
            )
        else:
            logging.warning(f'Command: {interaction.command}\nError: {error}')
            print(f'Command: {interaction.command}\nError: {error}')


async def setup(bot: commands.Bot):
    await bot.add_cog(LiveLaunchNext(bot))
