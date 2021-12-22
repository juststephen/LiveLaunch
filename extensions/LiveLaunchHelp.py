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
            title='LiveLaunch - Help',
            description='Send live launches and events to your guild!',
            color=0x00FF00
        )
        # Set author
        embed.set_author(
            name='by juststephen',
            url='https://juststephen.com'
        )
        # Enable
        embed.add_field(
            name='Enable',
            value='Use `/enable` to enable `messages` and/or `events`'
        )
        # Disable
        embed.add_field(
            name='Disable',
            value='Use `/disable` to disable either `messages`, `events` or `all`'
        )
        # Synchronize
        embed.add_field(
            name='Synchronize',
            value='Use `/synchronize` to manually synchronize events,' \
                ' for example after accidentally deleting an event.'
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