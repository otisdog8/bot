from discord.ext import commands
from discord.ext.commands import Context
from os import getenv
from mcrcon import MCRcon
from pystemd.systemd1 import Unit
from os.path import join
from asyncio import sleep
import shutil


class Cog(commands.Cog, name="minecraft"):
    def __init__(self, bot):
        self.bot = bot
        self.ratelimit = 0

        # Handle setting up the config
        self.config = bot.get_cog("config").get_config("minecraft")

        # Default values
        self.config.set_default("server_ip", "127.0.0.1")
        self.config.set_default("versions", ["1.8", "1.17"])
        self.config.set_default("servers_root_directory", "/insert/path/here/")
        self.config.set_default("currently_selected_version", "1.8")
        self.config.set_default("rcon_port", 25575)

    def get_server_path(self):
        return join(
            self.config["servers_root_directory"],
            "mc-server-{}".format(self.config["currently_selected_version"]),
        )

    def is_server_off(ctx):
        if isinstance(ctx, Context):
            self = ctx.cog
        else:
            self = ctx
        unit = Unit(
            b"mc-service-%s.service"
            % self.config["currently_selected_version"].encode("UTF-8")
        )
        unit.load()
        return (
            unit.Unit.ActiveState == b"inactive" or unit.Unit.ActiveState == b"failed"
        )

    def is_server_unpopulated(ctx):
        if isinstance(ctx, Context):
            self = ctx.cog
        else:
            self = ctx
        if self.is_server_off():
            return True
        resp = self.execute_command("list")
        return "There are 0" in resp

    async def turn_server_off(self):
        unit = Unit(
            b"mc-service-%s.service"
            % self.config["currently_selected_version"].encode("UTF-8")
        )
        unit.load()
        unit.Unit.Stop(b"replace")
        while not self.is_server_off():
            await sleep(1)

    @commands.command()
    @commands.check(is_server_off)
    async def start_server(self, ctx):
        unit = Unit(
            b"mc-service-%s.service"
            % self.config["currently_selected_version"].encode("UTF-8")
        )
        unit.load()
        unit.Unit.Start(b"replace")
        await ctx.send("Started Server")

    @commands.command()
    @commands.check(is_server_unpopulated)
    async def stop_server(self, ctx):
        self.turn_server_off()

    @commands.command()
    @commands.check(is_server_unpopulated)
    async def change_version(self, ctx, version):
        await ctx.send(
            "Changing server to version {} and regenerating world".format(version)
        )
        await ctx.send("Turning off server...")
        await self.turn_server_off()
        await ctx.send("Changing version jar...")
        if version in self.config["versions"]:
            self.config["currently_selected_version"] = version
        await ctx.invoke(self.bot.get_command("start_server"))

    @commands.command()
    @commands.check(is_server_unpopulated)
    async def reset_world(self, ctx):
        await self.turn_server_off()
        await ctx.send("Changing world...")
        shutil.rmtree(join(self.get_server_path(), "world"))
        shutil.rmtree(join(self.get_server_path(), "world_nether"))
        shutil.rmtree(join(self.get_server_path(), "world_the_end"))
        await ctx.invoke(self.bot.get_command("start_server"))

    def execute_command(self, command):
        with MCRcon(
            self.config["server_ip"],
            getenv("RCON_PASSWORD"),
            port=self.config["rcon_port"],
        ) as mcr:
            return mcr.command(command)

    @commands.command()
    async def execute(self, ctx, command):
        await ctx.send(self.execute_command(command))

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
