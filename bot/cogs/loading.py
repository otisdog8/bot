from discord.ext import commands


EXTENSIONS_TO_LOAD = ("loading", "icon")


class Cog(commands.Cog, name="loading"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, *modules):
        for m in modules:
            if m in EXTENSIONS_TO_LOAD:
                self.bot.load_extension("cogs." + m)
                await ctx.send("Loaded " + m)
            else:
                await ctx.send("Module not found")

    # Names are different to prevent conflict with python builtin
    @commands.command(name="reload")
    @commands.is_owner()
    async def _reload(self, ctx, *modules):
        for m in modules:
            if m in EXTENSIONS_TO_LOAD:
                self.bot.reload_extension("cogs." + m)
                await ctx.send("Reloaded " + m)
            else:
                await ctx.send("Module not found")

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *modules):
        for m in modules:
            if m in EXTENSIONS_TO_LOAD:
                self.bot.unload_extension("cogs." + m)
                await ctx.send("Unloaded " + m)
            else:
                await ctx.send("Module not found")

    @commands.command()
    @commands.is_owner()
    async def reload_all(self, ctx):
        self._reload_all()

    @reload_all.error
    @load.error
    @_reload.error
    @unload.error
    async def loading_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Non-owners are not allowed to access loading commands")
        else:
            await ctx.send(error)

    def _initialize_all(self):
        for m in EXTENSIONS_TO_LOAD:
            if m != "loading":
                self.bot.load_extension("cogs." + m)

    def _load_all(self):
        for m in EXTENSIONS_TO_LOAD:
            self.bot.load_extension("cogs." + m)

    def _unload_all(self):
        for m in EXTENSIONS_TO_LOAD:
            self.bot.unload_extension("cogs." + m)


def setup(bot):
    bot.add_cog(Cog(bot))
