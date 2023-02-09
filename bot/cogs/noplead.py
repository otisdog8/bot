from discord.ext import commands
from collections import defaultdict
import random
random.seed()
from discord.ext import commands

class Cog(commands.Cog, name="noplead"):
    def __init__(self ,bot):
        self.bot = bot
        self.times = defaultdict(int)

    @commands.command()
    async def command(self ,ctx):
        self.permload()
        if self.permcheck(ctx ,self.commandid):
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        content = message.content
        if "🥺" in content or ":pleading:" in content or "🥹" in content or ":face_holding_back_tears:" in content:
          await message.channel.send("gtfo pleading user")
          await message.delete()


async def setup(bot):
    await bot.add_cog(Cog(bot))
