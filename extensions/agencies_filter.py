import discord
from discord.ext import commands
import logging

class LiveLaunchAgenciesFilter(commands.Cog):
    """
    Discord.py cog for the agencies filter commands.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.defer(ephemeral=True)
    async def agencyfilter(self, ctx) -> None:
        """
        List, add and remove filters for agencies.
        """
        pass

    @agencyfilter.command(name='list')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def agencyfilter_list(self, ctx) -> None:
        """
        List filters for agencies.
        """
        # Guild ID
        guild_id = ctx.guild.id

        # Get all available filters
        filters_all = await self.bot.lldb.ll2_agencies_filter_list()

        # Get all filters enabled in the guild
        filters_guild = await self.bot.lldb.ll2_agencies_filter_list(
            guild_id=guild_id
        )

        # Create list embed
        embed = discord.Embed(
            color=0x00E8FF,
            description='When an agency filter is enabled it will not use these for **launches**.',
            title='Agency Filters'
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

    @agencyfilter.command(name='add')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def agencyfilter_add(self, ctx, agency: str) -> None:
        """
        Add a filter for agencies.

        Parameters
        ----------
        agency : str
            Enable filter for
            agencies.
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
        agencies = [i.strip() for i in agency.split(',')]

        agency_ids = []
        agency_names = []
        for item in agencies:

            try:
                agency_ids.append(
                    int(item)
                )

            # Input is a string
            except:
                # Lowercase
                agency_names.append(
                    item.lower()
                )

        # Add to the database and get the failed ones
        failed = await self.bot.lldb.ll2_agencies_filter_add(
            guild_id,
            agency_names=agency_names,
            agency_ids=agency_ids
        )

        # Notify user
        agencies = list(map(str, agencies))
        failed = list(map(str, failed))
        if not failed:
            await ctx.send(
                f"Added agency filter(s): `{', '.join(agencies)}`.",
                ephemeral=True
            )
        elif len(failed) == len(agencies):
            await ctx.send(
                f"Agency filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist.",
                ephemeral=True
            )
        else:
            # Check failed / success
            successes = set(agencies) ^ set(failed)
            # Send
            await ctx.send(
                f"Added agency filter(s): `{', '.join(successes)}`, "
                f"couldn\'t add agency filter(s): `{', '.join(failed)}`.",
                ephemeral=True
            )

    @agencyfilter.command(name='remove')
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 8)
    async def agencyfilter_remove(self, ctx, agency: str) -> None:
        """
        Remove a filter for agencies.

        Parameters
        ----------
        agency : str
            Enable filter for
            agencies.
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
        agencies = [i.strip() for i in agency.split(',')]

        agency_ids = []
        agency_names = []
        for item in agencies:

            try:
                agency_ids.append(
                    int(item)
                )

            # Input is a string
            except:
                # Lowercase
                agency_names.append(
                    item.lower()
                )

        # Remove from the database and get the failed ones
        failed = await self.bot.lldb.ll2_agencies_filter_remove(
            guild_id,
            agency_names=agency_names,
            agency_ids=agency_ids
        )

        # Notify user
        agencies = list(map(str, agencies))
        failed = list(map(str, failed))
        if not failed:
            await ctx.send(
                f"Removed agency filter(s): `{', '.join(agencies)}`.",
                ephemeral=True
            )
        elif len(failed) == len(agencies):
            await ctx.send(
                f"Agency filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist.",
                ephemeral=True
            )
        else:
            # Check failed / success
            successes = set(agencies) ^ set(failed)
            # Send
            await ctx.send(
                f"Removed agency filter(s): `{', '.join(successes)}`, "
                f"couldn\'t remove agency filter(s): `{', '.join(failed)}`.",
                ephemeral=True
            )

    @agencyfilter.error
    @agencyfilter_list.error
    @agencyfilter_add.error
    @agencyfilter_remove.error
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


def setup(client):
    client.add_cog(LiveLaunchAgenciesFilter(client))
