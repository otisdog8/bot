import asyncio
import datetime

import discord
from discord.ext import commands

import bot

duration: int = 60 * 60
guildId: int = 964451976186310668
channel_name: str = "malding"


class Cog(commands.Cog, name="malding"):
    def __init__(self, bot_instance):
        self.last_message: datetime.datetime = None
        self.bot: commands.Bot = bot_instance
        scheduler: bot.cogs.scheduler.Cog = self.bot.get_cog("scheduler")
        self.scheduler: bot.cogs.scheduler.CogScheduler = scheduler.get_scheduler(self.__cog_name__)

    async def cog_load(self) -> None:
        self.scheduler.run_task(self.run_channel_deletes())

    async def cog_unload(self) -> None:
        self.scheduler.handle_unload()

    async def run_channel_deletes(self) -> None:
        now = datetime.datetime.now()
        time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        diff = time - now
        secs = diff.total_seconds()
        secs = secs if secs > 0 else secs + 24 * 60 * 60
        await asyncio.sleep(secs)
        while True:
            # Delete and recreate
            guild = self.bot.get_guild(guildId)
            for channel in guild.channels:
                if channel.name == channel_name:
                    await channel.delete(reason="Delete malding")
                    await guild.create_text_channel(channel_name, reason="Recreate malding", category=channel.category)
                    break
            await asyncio.sleep(60 * 60 * 24)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id == guildId and message.channel.name == channel_name:
            self.last_message = datetime.datetime.now()
            self.scheduler.run_task(self.run_channel_purge(message))

    async def run_channel_purge(self, message) -> None:
        await asyncio.sleep(duration)
        if (self.last_message + datetime.timedelta(seconds=duration)) < datetime.datetime.now():
            # Purge the channel
            for channel in message.guild.channels:
                if channel.name == channel_name:
                    await channel.purge(limit=None)
                    break


async def setup(bot):
    await bot.add_cog(Cog(bot))
