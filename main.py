import asyncio
from discord import Game, Intents, VoiceClient
from discord.ext.commands import Bot
from dotenv import load_dotenv
import logging
from os import getenv
from pathlib import Path
import warnings

from bin import Database

logging.basicConfig(
    filename='LiveLaunch.log',
    format='%(asctime)s : %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
# No Discord voice support required, turn warning off
VoiceClient.warn_nacl = False
# Turn off aiomysql table creation warnings
warnings.filterwarnings(
    'ignore',
    message=".*Table '.*' already exists.*",
    module='aiomysql'
)

load_dotenv() # Loading token
TOKEN = getenv('DISCORD_TOKEN')
if not TOKEN:
    logging.critical('RIP, no TOKEN.')
    exit()

class LiveLaunchBot(Bot):
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

    def run(self, token: str) -> None:
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
            logging.info(f'Loaded {extension}')

        # Create application commands if needed
        if False:
            response = await self.tree.sync()
            logging.debug(f'Creating application commands: {response}')

bot = LiveLaunchBot()

@bot.event # On startup
async def on_ready() -> None:
    # Set status
    await bot.change_presence(activity=Game(name='Kerbal Space Program'))
    # Log amount of servers joined
    logging.info(f'{bot.user} Connected to {len(bot.guilds)} servers.')

bot.run(TOKEN)
