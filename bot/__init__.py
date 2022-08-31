import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv, chdir

__version__ = "0.1.0"


def main():
    # Signs of life
    print("Hello, world!")

    # Environment Setup - get token
    env_path = __file__ + ".env"
    load_dotenv(env_path)
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
    bot.load_extension("cogs.loading")
    bot.get_cog("loading")._initialize_all()

    @bot.event
    async def on_ready():
        print("Ready!")
        print("Logged in as ---->", bot.user)
        print("ID:", bot.user.id)

    # Run the bot
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
