import discord
from discord import app_commands, Interaction
from discord.app_commands import AppCommandError, Range
from discord.ext import commands
import logging

from bin import convert_minutes, enums
from main import LiveLaunchBot

logger = logging.getLogger(__name__)

@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class LiveLaunchNotificationsCommands(
    commands.GroupCog,
    group_name='notifications',
    group_description='Notification settings, only for administrators.'
):
    """
    Discord.py cog for notifications setting commands.
    """
    # Subgroup countdown command
    countdown = app_commands.Group(
        name='countdown',
        description='Countdown notification settings'
    )
    def __init__(self, bot: LiveLaunchBot):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def general(
        self,
        interaction: Interaction,
        everything: enums.EnableDisable | None = None,
        events: enums.EnableDisable | None = None,
        launches: enums.EnableDisable | None = None,
        t0_changes: enums.EnableDisable | None = None,
        include_scheduled_events: enums.IncludeExclude | None = None
    ) -> None:
        """
        General notification settings.

        Parameters
        ----------
        everything : enums.EnableDisable or None, default: None
            Enable/disable all notification
            settings except for countdowns.
        events : enums.EnableDisable or None, default: None
            Enable/disable event
            notifications.
        launches : enums.EnableDisable or None, default: None
            Enable/disable launch notifications
            (ignores status settings).
        t0_changes : enums.EnableDisable or None, default: None
            Enable/disable notifications
            for when T-0 changes.
        include_scheduled_events : enums.IncludeExclude or None, default: None
            Include/exclude Discord
            scheduled events in the
            notification.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        if (guild_id := interaction.guild_id) is None:
            raise TypeError('guild_id should never be None')

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'Cannot update settings, nothing is enabled within this guild.'
            )
            return

        # Select desired settings
        if everything is not None:
            message = 'all'
            everything_bool = everything is enums.EnableDisable.Enable
            settings = {
                'launch': everything_bool,
                'event': everything_bool,
                't0_change': everything_bool,
                'tbd': everything_bool,
                'tbc': everything_bool,
                'go': everything_bool,
                'liftoff': everything_bool,
                'hold': everything_bool,
                'deploy': everything_bool,
                'end_status': everything_bool,
                'scheduled_event': everything_bool
            }
        else:
            message = 'selected general'
            settings = {}
            if events is not None:
                settings['event'] = events is enums.EnableDisable.Enable
            if launches is not None:
                settings['launch'] = launches is enums.EnableDisable.Enable
            if t0_changes is not None:
                settings['t0_change'] = t0_changes is enums.EnableDisable.Enable
            if include_scheduled_events is not None:
                settings['scheduled_event'] = include_scheduled_events is enums.IncludeExclude.Include

        # Update database
        if settings:
            await self.bot.lldb.notification_settings_edit(guild_id, **settings)

        # Send reply
        await interaction.followup.send(
            f'Changed {message} notification settings.'
        )

    @countdown.command(name='list')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def countdown_list(
        self,
        interaction: Interaction
    ) -> None:
        """
        List countdown notifications.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        if (guild_id := interaction.guild_id) is None:
            raise TypeError('guild_id should never be None')

        # Fetch settings
        settings = await self.bot.lldb.notification_countdown_list(guild_id)

        # When there are none
        if not settings:
            await interaction.followup.send(
                'No countdown notification settings created yet.'
            )
            return

        # Create list embed
        embed = discord.Embed(
            color=0x00E8FF,
            description='All active countdown times for notifications.'
                '\nThe index can be used to remove countdown times.',
            title='Countdown list'
        )
        # Add countdown settings
        embed.add_field(
            name='List:',
            value='```index) time```\n```' +
                '\n'.join(f'{i}) {convert_minutes(j)}' for i, j in settings) +
                '```'
        )

        # Send embed
        await interaction.followup.send(embed=embed)

    @countdown.command(name='add')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def countdown_add(
        self,
        interaction: Interaction,
        days: Range[int, 1, 31] | None = None,
        hours: Range[int, 1, 24] | None = None,
        minutes: Range[int, 1, 60] | None = None
    ) -> None:
        """
        Add a countdown notification.

        Parameters
        ----------
        days : Range[int, 1, 31] or None, default: None
            Amount of days [1-31].
        hours : Range[int, 1, 31] or None, default: None
            Amount of hours [1-24].
        minutes : Range[int, 1, 31] or None, default: None
            Amount of minutes [1-60].
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        if (guild_id := interaction.guild_id) is None:
            raise TypeError('guild_id should never be None')

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'Cannot update settings, nothing is enabled within this guild.'
            )
            return

        # Maximum check
        if await self.bot.lldb.notification_countdown_check(guild_id):
            await interaction.followup.send(
                'Maximum amount (64) of countdowns already active.'
            )
            return

        # Convert all to minutes
        days = 0 if days is None else days
        hours = 0 if hours is None else hours
        minutes = 0 if minutes is None else minutes
        minutes += ( days * 24 + hours ) * 60

        # Update database when more than 0
        if minutes:
            await self.bot.lldb.notification_countdown_add(guild_id, minutes)
            # Send reply
            await interaction.followup.send('Added countdown setting.')
        else:
            # Send reply
            await interaction.followup.send(
                'Countdown times have a minimum of 1 minute.'
            )

    @countdown.command(name='remove')
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    @app_commands.describe(index='Index [1-64].')
    async def countdown_remove(
        self,
        interaction: Interaction,
        index: Range[int, 1, 64]
    ) -> None:
        """
        Remove a countdown notification by index, use list to see these

        Parameters
        ----------
        index : Range[int, 1, 31]
            Index of the time
            when sorting minutes
            by ascending.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        if (guild_id := interaction.guild_id) is None:
            raise TypeError('guild_id should never be None')

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'Cannot update settings, nothing is enabled within this guild.'
            )
            return

        # Update database
        await self.bot.lldb.notification_countdown_remove(guild_id, index)
        # Send reply
        await interaction.followup.send('Removed countdown setting.')

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 8)
    async def launch_status(
        self,
        interaction: Interaction,
        end_status: enums.EnableDisable | None = None,
        deploy: enums.EnableDisable | None = None,
        hold: enums.EnableDisable | None = None,
        liftoff: enums.EnableDisable | None = None,
        go: enums.EnableDisable | None = None,
        tbc: enums.EnableDisable | None = None,
        tbd: enums.EnableDisable | None = None
    ) -> None:
        """
        Launch status notification settings.

        Parameters
        ----------
        end_status : enums.EnableDisable or None, default: None
            Enable/disable final
            status notifications.
        deploy : enums.EnableDisable or None, default: None
            Enable/disable payload
            deployed status notifications.
        hold : enums.EnableDisable or None, default: None
            Enable/disable
            hold notifications.
        liftoff : enums.EnableDisable or None, default: None
            Enable/disable liftoff
            notifications.
        go : enums.EnableDisable or None, default: None
            Enable/disable go for
            launch notifications.
        tbc : enums.EnableDisable or None, default: None
            Enable/disable to be
            confirmed notifications.
        tbd : enums.EnableDisable or None, default: None
            Enable/disable to be
            determined notifications.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Guild ID
        if (guild_id := interaction.guild_id) is None:
            raise TypeError('guild_id should never be None')

        # Check if anything is enabled
        if not await self.bot.lldb.enabled_guilds_check(guild_id):
            await interaction.followup.send(
                'Cannot update settings, nothing is enabled within this guild.'
            )
            return

        # Select desired settings
        settings: dict[str, bool] = {}
        if end_status is not None:
            settings['end_status'] = end_status is enums.EnableDisable.Enable
        if deploy is not None:
            settings['deploy'] = deploy is enums.EnableDisable.Enable
        if hold is not None:
            settings['hold'] = hold is enums.EnableDisable.Enable
        if liftoff is not None:
            settings['liftoff'] = liftoff is enums.EnableDisable.Enable
        if go is not None:
            settings['go'] = go is enums.EnableDisable.Enable
        if tbc is not None:
            settings['tbc'] = tbc is enums.EnableDisable.Enable
        if tbd is not None:
            settings['tbd'] = tbd is enums.EnableDisable.Enable

        # Update database
        if settings:
            await self.bot.lldb.notification_settings_edit(guild_id, **settings)

        # Send reply
        await interaction.followup.send(
            'Changed selected launch status notification settings.'
        )

    @general.error
    @countdown_list.error
    @countdown_add.error
    @countdown_remove.error
    @launch_status.error
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
            logger.error(error)


async def setup(bot: LiveLaunchBot):
    await bot.add_cog(LiveLaunchNotificationsCommands(bot))
