from discord.ext import commands
from discord.ext.commands import is_owner
from pystemd.systemd1 import Unit


class Cog(commands.Cog, name="management"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.check(is_owner())
    def stop(self):
        await self.bot.close()
        exit(0)

    @commands.command()
    @commands.check(is_owner())
    def restart(self):
        await self.bot.close()
        unit = Unit(
            "edward-bot.service"
        )
        unit.load()
        unit.Unit.Restart(b'replace')


async def setup(bot):
    await bot.add_cog(Cog(bot))

