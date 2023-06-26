from discord import Game, Intents, VoiceClient
from discord.ext.commands import Bot
from dotenv import load_dotenv
import logging
from os import getenv
from pathlib import Path
import warnings

logger = logging.basicConfig(
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
    print('RIP, no TOKEN.')
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
        # Extensions to load with database first as others depend on it
        self.initial_extensions  = [
            'extensions.database',
            *[
                f"{'.'.join(file.parent.parts)}.{file.stem}"
                for file in Path('extensions').glob('**/*.py') if
                file.suffix == '.py' and file.stem != 'database'
            ]
        ]

    async def setup_hook(self) -> None:
        """
        Setting up the bot by loading extensions
        and syncing application commands.
        """
        # Load extensions during setup
        for extension in self.initial_extensions :
            await self.load_extension(extension)
            print(f'Loaded {extension}')

        # Create application commands if needed
        if False:
            response = await self.tree.sync()
            print(response)

bot = LiveLaunchBot()

@bot.event # On startup
async def on_ready():
    # Set status
    await bot.change_presence(activity=Game(name='Kerbal Space Program'))
    # Print amount of servers joined
    print(f'{bot.user} Connected to {len(bot.guilds)} servers.')

bot.run(TOKEN, log_handler=logger)
