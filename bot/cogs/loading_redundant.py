from discord.ext import commands


class Cog(commands.Cog, name="loading"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load_redundant(self, ctx, *modules):
        for m in modules:
            self.bot.load_extension("cogs." + m)
            await ctx.send("Loaded " + m)

    # Names are different to prevent conflict with python builtin
    @commands.command(name="reload_redundant")
    @commands.is_owner()
    async def _reload_redundant(self, ctx, *modules):
        for m in modules:
            self.bot.reload_extension("cogs." + m)
            await ctx.send("Reloaded " + m)

    @commands.command()
    @commands.is_owner()
    async def unload_redundant(self, ctx, *modules):
        for m in modules:
            self.bot.unload_extension("cogs." + m)
            await ctx.send("Unloaded " + m)

    @load_redundant.error
    @_reload_redundant.error
    @unload_redundant.error
    async def loading_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Non-owners are not allowed to access loading commands")
        else:
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Cog(bot))
