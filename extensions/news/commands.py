from discord import app_commands, Embed, Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands
import logging

from bin import combine_strings

@app_commands.guild_only()
class LiveLaunchNewsSitesFilter(
    commands.GroupCog,
    group_name='newsfilter',
    group_description='List, add and remove filters '
        'for news sites, only for administrators.'
):
    """
    Discord.py cog for the news site filter commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='list')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def newsfilter_list(
        self,
        interaction: Interaction
    ) -> None:
        """
        List filters for news sites.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        guild_id = interaction.guild_id

        # Get all available filters
        filters_all = await self.bot.lldb.news_filter_list()

        # Get all filters enabled in the guild
        filters_guild = await self.bot.lldb.news_filter_list(
            guild_id=guild_id
        )

        # Create list embed
        embed = Embed(
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
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='add')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def newsfilter_add(
        self,
        interaction: Interaction,
        newssite: str
    ) -> None:
        """
        Add a filter for a news site, either one or comma-separated.

        Parameters
        ----------
        newssite : str
            News site name or ID.
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
            await interaction.followup.send(
                f"Added news site filter(s): `{', '.join(newssites)}`."
            )
        elif len(failed) == len(newssites):
            await interaction.followup.send(
                f"News site filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist."
            )
        else:
            # Check failed / success
            successes = set(newssites) ^ set(failed)
            # Send
            await interaction.followup.send(
                f"Added news site filter(s): `{', '.join(successes)}`, "
                f"couldn\'t add news site filter(s): `{', '.join(failed)}`."
            )

    @app_commands.command(name='remove')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def newsfilter_remove(
        self,
        interaction: Interaction,
        newssite: str
    ) -> None:
        """
        Remove a filter for a news site, either one or comma-separated.

        Parameters
        ----------
        newssite : str
            News site name or ID.
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
            await interaction.followup.send(
                f"Removed news site filter(s): `{', '.join(newssites)}`."
            )
        elif len(failed) == len(newssites):
            await interaction.followup.send(
                f"News site filter(s) `{', '.join(failed)}` doesn\'t/don\'t exist."
            )
        else:
            # Check failed / success
            successes = set(newssites) ^ set(failed)
            # Send
            await interaction.followup.send(
                f"Removed news site filter(s): `{', '.join(successes)}`, "
                f"couldn\'t remove news site filter(s): `{', '.join(failed)}`."
            )

    @newsfilter_list.error
    @newsfilter_add.error
    @newsfilter_remove.error
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
    await bot.add_cog(LiveLaunchNewsSitesFilter(bot))
