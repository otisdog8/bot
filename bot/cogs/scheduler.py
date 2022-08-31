from discord.ext import commands


class Cog(commands.Cog, name="cog"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot


async def setup(bot):
    await bot.add_cog(Cog(bot))

