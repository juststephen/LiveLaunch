from discord import Embed
from discord.ext import commands

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
            name='enable',
            value='Use `/enable` to enable `messages` and/or `events`'
        )
        # Disable
        embed.add_field(
            name='disable',
            value='Use `/disable` to disable either `messages`, `events` or `all`'
        )
        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @help.error
    async def help_error(self, ctx, error):
        """
        Method that handles erroneous interactions.
        """
        print(f'Command: {ctx.name}\nError: {error}')


def setup(client):
    client.add_cog(LiveLaunchHelp(client))