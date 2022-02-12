from discord import Game
from discord.ext.commands import Bot
from dotenv import load_dotenv
import json
import logging
from os import getenv, listdir

logging.basicConfig(
    filename='LiveLaunch.log',
    format='%(asctime)s : %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

# The command_prefix is here to prevent non application commands
client = Bot(
    command_prefix="""
    01001001 00100000 01101100 01101001
    01101011 01100101 00100000 01110100
    01110010 01100001 01101001 01101110
    01110011 00100001 00100001 00100001
    """,
    help_command=None
)

load_dotenv() # Loading token
TOKEN = getenv('DISCORD_TOKEN')
if not TOKEN:
    print('RIP, no TOKEN.')
    exit()

@client.event # On startup
async def on_ready():
    # Create application commands if needed
    if False:
        with open('LiveLaunch_Commands.json', 'r', encoding='utf-8') as f:
            commands = json.load(f)
        response = await client.http.bulk_create_global_application_commands(
            client.application_id, commands['commands']
        )
        print(response)
    # Set status
    await client.change_presence(activity=Game(name='Kerbal Space Program'))
    # Print amount of servers joined
    print(f'{client.user} Connected to {len(client.guilds)} servers.')

# Load cogs when run, with LiveLaunchDB first
extensions = ['extensions.LiveLaunchDB', \
    *[f'extensions.{file[:-3]}' for file in listdir('./extensions') if \
    file.endswith('.py') and not 'LiveLaunchDB' in file]]
for extension in extensions:
    client.load_extension(extension)
    print(f'Loaded {extension}')

client.run(TOKEN)