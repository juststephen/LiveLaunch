import discord
from discord.ext import commands
import logging

from bin import combine_strings

class LiveLaunchNewsSitesFilter(commands.Cog):
    """
    Discord.py cog for the news site filter commands.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def newsfilter(self, ctx) -> None:
        """
        List, add and remove filters for news sites.
        """
        pass

    @newsfilter.command(name='list')
    @commands.defer(ephemeral=True)
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
            # Format individual filters
            filters_text = [f'{i}) {j}\n' for i, j in filters_available]
            # Combine them
            filters_text = combine_strings(filters_text)
            # Insert into the embed
            for i, j in enumerate(filters_text):
                embed.add_field(
                    name='Available' + (' (continued)' if i else ''),
                    value=f'```{j}```'
                )
        # Add enabled filters
        if filters_guild:
            # Format individual filters
            filters_text = [f'{i}) {j}\n' for i, j in filters_guild]
            # Combine them
            filters_text = combine_strings(filters_text)
            # Insert into the embed
            for i, j in enumerate(filters_text):
                embed.add_field(
                    name='Enabled' + (' (continued)' if i else ''),
                    value=f'```{j}```'
                )

        # Send list
        await ctx.send(embed=embed)

    @newsfilter.command(name='add')
    @commands.defer(ephemeral=True)
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
                'This guild has nothing enabled, can\'t add filters.'
            )
            return

        # Split bulk into a list
        newssites = [i.strip() for i in newssite.split(',')]

        news_site_ids = []
        news_site_names = []
        for item in newssites:

            try:
                news_site_ids.append(
                    int(item)
                )

            # Input is a string
            except:
                # Lowercase
                news_site_names.append(
                    item.lower()
                )

        # Add to the database and get the failed ones
        failed = await self.bot.lldb.news_filter_add(
            guild_id,
            news_site_ids=news_site_ids,
            news_site_names=news_site_names
        )

        # Notify user
        newssites = list(map(str, newssites))
        failed = list(map(str, failed))
        if not failed:
            await ctx.send(
                f"Added news site filter(s): `{', '.join(newssites)}`."
            )
        elif len(failed) == len(newssites):
            await ctx.send(
                f"News site filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist."
            )
        else:
            # Check failed / success
            successes = set(newssites) ^ set(failed)
            # Send
            await ctx.send(
                f"Added news site filter(s): `{', '.join(successes)}`, "
                f"couldn\'t add news site filter(s): `{', '.join(failed)}`."
            )

    @newsfilter.command(name='remove')
    @commands.defer(ephemeral=True)
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
                'This guild has nothing enabled, can\'t remove filters.'
            )
            return

        # Split bulk into a list
        newssites = [i.strip() for i in newssite.split(',')]

        news_site_ids = []
        news_site_names = []
        for item in newssites:

            try:
                news_site_ids.append(
                    int(item)
                )

            # Input is a string
            except:
                # Lowercase
                news_site_names.append(
                    item.lower()
                )

        # Remove from the database and get the failed ones
        failed = await self.bot.lldb.news_filter_remove(
            guild_id,
            news_site_ids=news_site_ids,
            news_site_names=news_site_names
        )

        # Notify user
        newssites = list(map(str, newssites))
        failed = list(map(str, failed))
        if not failed:
            await ctx.send(
                f"Removed news site filter(s): `{', '.join(newssites)}`."
            )
        elif len(failed) == len(newssites):
            await ctx.send(
                f"News site filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist."
            )
        else:
            # Check failed / success
            successes = set(newssites) ^ set(failed)
            # Send
            await ctx.send(
                f"Removed news site filter(s): `{', '.join(successes)}`, "
                f"couldn\'t remove news site filter(s): `{', '.join(failed)}`."
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
                await ctx.send('This command is only for administrators.')
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send('This command is only for guild channels.')
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(
                f'This command is on cooldown for {error.retry_after:.0f} more seconds.'
            )
        else:
            logging.warning(f'Command: {ctx.command}\nError: {error}')
            print(f'Command: {ctx.command}\nError: {error}')


def setup(client):
    client.add_cog(LiveLaunchNewsSitesFilter(client))
