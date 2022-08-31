from discord.ext import commands


EXTENSIONS_TO_LOAD = ("loading", "config", "loading_redundant", "dad", "management", "scheduler")
EXTENSIONS_THAT_EXIST = list(EXTENSIONS_TO_LOAD) + ["minecraft", "channelarchive", "malding"]
UNRELOADABLE_EXTENSIONS = ("config",)


class Cog(commands.Cog, name="loading"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, *modules):
        for m in modules:
            if m in EXTENSIONS_THAT_EXIST:
                await self.bot.load_extension("cogs." + m)
                await ctx.send("Loaded " + m)
            else:
                await ctx.send("Module not found")

    # Names are different to prevent conflict with python builtin
    @commands.command(name="reload")
    @commands.is_owner()
    async def _reload(self, ctx, *modules):
        for m in modules:
            if m in EXTENSIONS_THAT_EXIST and m not in UNRELOADABLE_EXTENSIONS:
                await self.bot.reload_extension("cogs." + m)
                await ctx.send("Reloaded " + m)
            else:
                await ctx.send("Module not found")

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *modules):
        for m in modules:
            if m in EXTENSIONS_THAT_EXIST:
                await self.bot.unload_extension("cogs." + m)
                await ctx.send("Unloaded " + m)
            else:
                await ctx.send("Module not found")

    @load.error
    @_reload.error
    @unload.error
    async def loading_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Non-owners are not allowed to access loading commands")
        else:
            await ctx.send(error)

    async def _initialize_all(self):
        for m in EXTENSIONS_TO_LOAD:
            if m != "loading":
                await self.bot.load_extension("cogs." + m)

    async def _load_all(self):
        for m in EXTENSIONS_TO_LOAD:
            await self.bot.load_extension("cogs." + m)

    async def _unload_all(self):
        for m in EXTENSIONS_TO_LOAD:
            await self.bot.unload_extension("cogs." + m)


async def setup(bot):
    await bot.add_cog(Cog(bot))

