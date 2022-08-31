# Stores state for Cogs that persists across reloads
from typing import Any

from discord.ext import commands


class Cog(commands.Cog, name="persistent_state_broker"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.state: dict[str, Any] = {}

    def set_state(self, key: str, val: Any):
        self.state[key] = val

    def get_state(self, key: str) -> Any:
        return self.state.pop(key, None)

    @commands.command()
    @commands.is_owner()
    async def clear_persistent_storage(self, ctx):
        self.state = {}
        await ctx.send("Cleared")

async def setup(bot):
    await bot.add_cog(Cog(bot))


