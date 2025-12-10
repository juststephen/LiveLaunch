import asyncio
from discord import Game, Intents, VoiceClient
from discord.ext import commands
from dotenv import load_dotenv
import logging
from os import getenv
from pathlib import Path
from typing import override
import warnings

from bin import Database

class LiveLaunchBot(commands.Bot):
    """
    LiveLaunch Discord bot.
    """
    def __init__(self) -> None:
        super().__init__(
            command_prefix=(),
            help_command=None,
            intents=Intents.default()
        )

        # Database object
        self.lldb = Database()

        # Extensions to load with database first as others depend on it
        self.initial_extensions  = [
            'extensions.database',
            *[
                f"{'.'.join(file.parent.parts)}.{file.stem}"
                for file in Path('extensions').glob('**/*.py') if
                file.suffix == '.py' and file.stem != 'database'
            ]
        ]

    @override
    def run(self, token: str) -> None:  # type: ignore
        """
        Connect to the database and start the bot.

        Parameters
        ----------
        token : str
            The authentication token.
        """
        async def runner() -> None:
            async with self.lldb, self:
                await self.lldb.start()
                await self.start(token, reconnect=True)

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            return

    async def setup_hook(self) -> None:
        """
        Setting up the bot by loading extensions
        and syncing application commands.
        """
        # Load extensions during setup
        for extension in self.initial_extensions:
            await self.load_extension(extension)
            logger.info(f'Loaded {extension}')

        # Create application commands
        response = await self.tree.sync()
        logger.debug(f'Created application commands: {response}')

    async def on_ready(self) -> None:
        """
        On ready event listener.
        """
        # Set status
        await bot.change_presence(activity=Game(name='Kerbal Space Program'))

        # Log amount of servers joined
        logger.info(f'{bot.user} connected to {len(bot.guilds)} servers')


if __name__ == '__main__':
    logging.basicConfig(
        filename='livelaunch.log',
        format='{asctime} - {name} - {levelname} - {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{',
        level=logging.WARNING,
        encoding='utf-8'
    )
    logger = logging.getLogger('main')

    # No Discord voice support required, turn warning off
    VoiceClient.warn_nacl = False
    # Turn off aiomysql table creation warnings
    warnings.filterwarnings(
        'ignore',
        message=".*Table '.*' already exists.*",
        module='aiomysql'
    )

    # Loading Discord API token
    load_dotenv()
    if not (token := getenv('DISCORD_TOKEN')):
        logger.critical('Cannot find Discord API token, exiting')
        exit()

    bot = LiveLaunchBot()
    bot.run(token)
