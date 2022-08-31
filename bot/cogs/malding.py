import asyncio
import datetime

import discord
from discord.ext import commands

duration: int = 10

class Cog(commands.Cog, name="malding"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        now = datetime.datetime.now()
        time = now.replace(hour=0)
        diff = time - now
        secs = diff.total_seconds()
        print(secs)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id == 964451976186310668 and message.channel.id == 1014390289181446174:
            self.last_message = datetime.datetime.now()
            await asyncio.sleep(duration)
            if (self.last_message + datetime.timedelta(seconds=duration)) < datetime.datetime.now():
                # Purge the channel
                await message.channel.purge(limit=None)



async def setup(bot):
    await bot.add_cog(Cog(bot))

