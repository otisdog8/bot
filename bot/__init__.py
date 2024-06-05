import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv, chdir

__version__ = "0.1.0"


async def main():
    # Signs of life
    print("Hello, world!")

    # Environment Setup - get token
    TOKEN = getenv("TOKEN")

    # Set current directory to root of this thing
    folder_path = ""
    for f in env_path.split("/")[:-1]:
        folder_path += f + "/"
    chdir(folder_path)

    # Bot Setup
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="~", intents=intents)

    await bot.load_extension("cogs.loading")
    await bot.get_cog("loading")._initialize_all()

    @bot.event
    async def on_ready():
        print("Ready!")
        print("Logged in as ---->", bot.user)
        print("ID:", bot.user.id)

    # Run the bot
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
