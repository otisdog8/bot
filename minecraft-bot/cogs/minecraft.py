from discord.ext import commands
from os import getenv
from mcrcon import MCRcon


class Cog(commands.Cog, name="minecraft"):
    def __init__(self, bot):
        self.bot = bot
        self.ratelimit = 0

    def is_server_off(ctx):
        try:
            with MCRcon("10.0.0.8", getenv("RCON_PASSWORD")) as mcr:
                mcr.command("/list")
            return True
        except Exception:
            return False

    def is_server_populated(ctx):
        self = ctx.cog
        if self.is_server_off():
            return True
        with MCRcon("10.0.0.8", getenv("RCON_PASSWORD")) as mcr:
            resp = mcr.command("/list")
            return not resp.contains("There are 0")

    def turn_server_off(self):
        pass

    @commands.command()
    @commands.check(is_server_off)
    async def start_server(self, ctx):
        pass

    @commands.command()
    @commands.check(is_server_populated)
    async def change_version(self, ctx, version):
        await ctx.send(
            "Changing server to version {} and regenerating world".format(version)
        )
        await ctx.send("Turning off server...")
        # Turn off server here
        await ctx.send("Changing version jar...")
        # Changing jars
        await ctx.invoke(self.bot.get_command("start_server"))

    @commands.command()
    @commands.check(is_server_populated)
    async def reset_world(self, ctx):
        # Turn off server here
        await ctx.send("Changing world...")
        # Changing world
        await ctx.invoke(self.bot.get_command("start_server"))

    @start_server.error
    @change_version.error
    @reset_world.error
    async def server_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Server is already running or populated with players")
        else:
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Cog(bot))
