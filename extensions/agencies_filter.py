import discord
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands
import logging

from bin import combine_strings, enums

@app_commands.guild_only()
class LiveLaunchAgenciesFilter(
    commands.GroupCog,
    group_name='agencyfilter',
    group_description='List, add and remove filters '
        'for agencies, only for administrators.'
):
    """
    Discord.py cog for the agencies filter commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='include_exclude')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def agencyfilter_include_exclude(
        self,
        interaction: Interaction,
        include_or_exclude: enums.IncludeExclude
    ) -> None:
        """
        Set the list of filtered agencies to be
        the only ones included or the ones excluded.

        Parameters
        ----------
        events : enums.IncludeExclude
            Set the filter
            to Include/Exclude.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        guild_id = interaction.guild_id

        # Check if guild has settings
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'This guild has nothing enabled, can\'t change setting.'
            )
            return

        # Update the setting
        await self.bot.lldb.ll2_agencies_filter_set_include_exclude(
            guild_id,
            include_or_exclude=include_or_exclude is enums.IncludeExclude.Include
        )

        # Send response
        await interaction.followup.send(
            f'Set agency filter to {include_or_exclude.name.lower()} agencies.'
        )

    @app_commands.command(name='list')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def agencyfilter_list(
        self,
        interaction: Interaction
    ) -> None:
        """
        List filters for agencies.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        guild_id = interaction.guild_id

        # Get all available filters
        filters_all = await self.bot.lldb.ll2_agencies_filter_list()

        # Get all filters enabled in the guild
        filters_guild = await self.bot.lldb.ll2_agencies_filter_list(
            guild_id=guild_id
        )

        # Get the include/exclude setting for the guild if it exists
        if filters_guild:
            include_exclude = await self.bot.lldb.ll2_agencies_filter_get_include_exclude(guild_id)
            include_exclude = 'include' if include_exclude else 'exclude'
        # Exclude is default if the guild has no settings yet
        else:
            include_exclude = 'exclude'

        # Create list embed
        embed = discord.Embed(
            color=0x00E8FF,
            description='When an agency filter is enabled it will be '
                'included or excluded for **launches** depending on the setting set '
                'using the `/agencyfilter include_exclude` command. '
                f'Currently the filter is set to {include_exclude}.',
            title='Agency Filters'
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
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='add')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def agencyfilter_add(
        self,
        interaction: Interaction,
        agency: str
    ) -> None:
        """
        Add a filter for an agency, either one or comma-separated.

        Parameters
        ----------
        agency : str
            Agency name or ID.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        guild_id = interaction.guild_id

        # Check if guild has settings
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'This guild has nothing enabled, can\'t add filters.'
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
            await interaction.followup.send(
                f"Added agency filter(s): `{', '.join(agencies)}`."
            )
        elif len(failed) == len(agencies):
            await interaction.followup.send(
                f"Agency filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist."
            )
        else:
            # Check failed / success
            successes = set(agencies) ^ set(failed)
            # Send
            await interaction.followup.send(
                f"Added agency filter(s): `{', '.join(successes)}`, "
                f"couldn\'t add agency filter(s): `{', '.join(failed)}`."
            )

    @app_commands.command(name='remove')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def agencyfilter_remove(
        self,
        interaction: Interaction,
        agency: str
    ) -> None:
        """
        Remove a filter for an agency, either one or comma-separated.

        Parameters
        ----------
        agency : str
            Agency name or ID.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        guild_id = interaction.guild_id

        # Check if guild has settings
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'This guild has nothing enabled, can\'t remove filters.'
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
            await interaction.followup.send(
                f"Removed agency filter(s): `{', '.join(agencies)}`."
            )
        elif len(failed) == len(agencies):
            await interaction.followup.send(
                f"Agency filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist."
            )
        else:
            # Check failed / success
            successes = set(agencies) ^ set(failed)
            # Send
            await interaction.followup.send(
                f"Removed agency filter(s): `{', '.join(successes)}`, "
                f"couldn\'t remove agency filter(s): `{', '.join(failed)}`."
            )

    @agencyfilter_list.error
    @agencyfilter_add.error
    @agencyfilter_remove.error
    async def command_error(
        self,
        interaction: Interaction,
        error: AppCommandError
    ) -> None:
        """
        Method that handles erroneous interactions with the commands.
        """
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                'This command is only for administrators.',
                ephemeral=True
            )
        elif isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown for {error.retry_after:.0f} more seconds.',
                ephemeral=True
            )
        else:
            logging.warning(f'Command: {interaction.command}\nError: {error}')
            print(f'Command: {interaction.command}\nError: {error}')


async def setup(bot: commands.Bot):
    await bot.add_cog(LiveLaunchAgenciesFilter(bot))
