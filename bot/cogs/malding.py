import asyncio
import datetime

import discord
from discord.ext import commands

duration: int = 3600

class Cog(commands.Cog, name="malding"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    def on_message(self, message: discord.Message):
        if message.guild.id == 964451976186310668 and message.channel.id == 1014390289181446174:
            self.last_message = datetime.datetime.now()
            await asyncio.sleep(duration)
            if (self.last_message + datetime.timedelta(seconds=duration)) < datetime.datetime.now():
                # Purge the channel
                message.channel.purge(limit=None)



def setup(bot):
    bot.add_cog(Cog(bot))