from discord import Embed
from discord.ext import commands
import logging

class LiveLaunchHelp(commands.Cog):
    """
    Discord.py cog for supplying help for LiveLaunch.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.defer(ephemeral=True)
    async def help(self, ctx):
        """
        Explanation of LiveLaunch
        """
        # Create embed
        embed = Embed(
            color=0x00FF00,
            description='Creates space related events and sends live streams!',
            title='LiveLaunch - Help',
            url='https://juststephen.com/projects/LiveLaunch'
        )
        # Set author
        embed.set_author(
            name='by juststephen',
            url='https://juststephen.com',
            icon_url='https://juststephen.com/images/apple-touch-icon.png'
        )
        # Enable
        embed.add_field(
            name='Enable',
            value='Use `/enable` to enable `notifications`, `news`, `messages` and/or `events`'
        )
        # Disable
        embed.add_field(
            name='Disable',
            value='Use `/disable` to disable either `notifications`, `news`, `messages`, `events`, or `all`'
        )
        # Synchronize
        embed.add_field(
            name='Synchronize',
            value='Use `/synchronize` to manually synchronize events,' \
                ' for example after accidentally deleting an event.'
        )
        # News Filter
        embed.add_field(
            name='News Filter',
            value='Use `/newsfilter` to list, add or remove news site filters.'
        )
        # Notifications
        embed.add_field(
            name='Notifications Countdown',
            value='Use `/notifications countdown` to list, add or remove countdown from'
                'the notifications.\nRemoving is done by index, which is shown in the list.'
        )
        embed.add_field(
            name='Notifications General',
            value='Use `/notifications general` to enable/disable `launches`, `events` '
                'and include/exclude Discord scheduled events in the countdown notifications.'
                '\n`everything` is used to enable all general and launch status settings.'
        )
        embed.add_field(
            name='Notifications Launch Status',
            value='Use `/notifications launch_status` to enable/disable notifications '
                'for launch status changes. These are `end_status`, `hold` and `liftoff`.'
        )

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @help.error
    async def help_error(self, ctx, error):
        """
        Method that handles erroneous interactions.
        """
        logging.warning(f'Command: {ctx.command}\nError: {error}')
        print(f'Command: {ctx.command}\nError: {error}')


def setup(client):
    client.add_cog(LiveLaunchHelp(client))