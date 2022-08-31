from typing import Any

from discord.ext import commands


class Cog(commands.Cog, name="cog"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    def getdep(self, dep: str, obj: Any) -> Any:
        # Note: This code will modify the object obj at the field dep upon updating of the dep component
        pass

async def setup(bot):
    await bot.add_cog(Cog(bot))

