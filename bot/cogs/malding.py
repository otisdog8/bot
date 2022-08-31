import asyncio
import datetime

import discord
from discord.ext import commands

duration: int = 10
guildId: int = 964451976186310668
channel_name: str = "bot-test-channel"

class Cog(commands.Cog, name="malding"):
    def __init__(self, bot):
        self.last_message: datetime.datetime = None
        self.bot: commands.Bot = bot

    async def cog_load(self) -> None:
        asyncio.create_task(self.run_channel_deletes())

    async def run_channel_deletes(self) -> None:
        now = datetime.datetime.now()
        time = now.replace(hour=5, minute=58, second=0, microsecond=0)
        diff = time - now
        secs = diff.total_seconds()
        print(secs)
        #await asyncio.sleep(secs)
        while True:
            # Delete and recreate
            guild = await self.bot.fetch_guild(guildId)
            print(guild)
            for channel in guild.channels:
                print(channel.name)
                if channel.name == channel_name:
                    await channel.delete(reason="Delete malding")
                    await guild.create_text_channel(channel_name, reason="Recreate malding", category=channel.category)
                break
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id == guildId:
            self.last_message = datetime.datetime.now()
            await asyncio.sleep(duration)
            if (self.last_message + datetime.timedelta(seconds=duration)) < datetime.datetime.now():
                # Purge the channel
                for channel in message.guild.channels:
                    if channel.name == channel_name:
                        await message.channel.purge(limit=None)
                        break



async def setup(bot):
    await bot.add_cog(Cog(bot))

