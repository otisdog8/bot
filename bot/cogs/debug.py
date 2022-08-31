from discord.ext import commands


class Cog(commands.Cog, name="debug"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def debug_print(self, msg: str) -> None:
        await self.bot.get_channel(1014576933255786598).send(msg)


async def setup(bot):
    await bot.add_cog(Cog(bot))

