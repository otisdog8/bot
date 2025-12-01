import asyncio
import shutil
from os import getenv
from os.path import join
from typing import Optional

from discord.ext import commands
from mcrcon import MCRcon
from pystemd.systemd1 import Unit

from bot.cogs.permissions import AuthorizedUser, PermissionDenied

# Commands that require only operator permission (not admin)
OPERATOR_COMMANDS = {
    "say", "list", "give", "tp", "teleport", "time", "weather",
    "gamemode", "msg", "tell", "w", "me", "seed", "difficulty"
}


class MinecraftServer:
    """Represents a single Minecraft server instance."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.ip = config.get("server_ip", "127.0.0.1")
        self.rcon_port = config.get("rcon_port", 25575)
        self.rcon_password_env = config.get("rcon_password_env", "RCON_PASSWORD")
        self.directory = config.get("directory", "")
        self.service_name = config.get("service_name", f"mc-{name}.service")
        self.versions = config.get("versions", [])
        self.mcr: Optional[MCRcon] = None

    @property
    def rcon_password(self) -> Optional[str]:
        return getenv(self.rcon_password_env)

    def connect_rcon(self):
        """Connect to the server's RCON."""
        if self.mcr:
            return
        self.mcr = MCRcon(self.ip, self.rcon_password, port=self.rcon_port)
        self.mcr.connect()

    def disconnect_rcon(self):
        """Disconnect from the server's RCON."""
        if self.mcr:
            self.mcr.disconnect()
            self.mcr = None

    def is_running(self) -> bool:
        """Check if the server's systemd service is running."""
        unit = Unit(self.service_name.encode())
        unit.load()
        return unit.Unit.ActiveState not in (b"inactive", b"failed")

    def is_empty(self) -> bool:
        """Check if the server has no players online."""
        if not self.is_running():
            return True
        try:
            resp = self.execute("list")
            return "There are 0" in resp
        except Exception:
            return True

    def execute(self, command: str) -> str:
        """Execute an RCON command on the server."""
        if not self.mcr:
            raise RuntimeError(f"Server {self.name} is not connected via RCON")
        return self.mcr.command(command)

    async def start(self) -> None:
        """Start the server's systemd service."""
        unit = Unit(self.service_name.encode())
        unit.load()
        unit.Unit.Start(b"replace")
        # Wait for server to start
        await asyncio.sleep(15)
        self.connect_rcon()

    async def stop(self) -> None:
        """Stop the server's systemd service."""
        self.disconnect_rcon()
        unit = Unit(self.service_name.encode())
        unit.load()
        unit.Unit.Stop(b"replace")
        # Wait for server to stop
        while self.is_running():
            await asyncio.sleep(1)

    def get_world_path(self, world: str = "world") -> str:
        """Get the path to a world directory."""
        return join(self.directory, world)


class Cog(commands.Cog, name="minecraft"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.config = bot.get_cog("config").get_config(self.__cog_name__)
        self.config.set_default("servers", {})
        self.perms = bot.get_cog("permissions")
        self.servers: dict[str, MinecraftServer] = {}
        self._load_servers()

    def _load_servers(self):
        """Load all configured servers."""
        for name, cfg in self.config["servers"].items():
            server = MinecraftServer(name, cfg)
            if server.is_running():
                try:
                    server.connect_rcon()
                except Exception:
                    pass  # Server might be starting up
            self.servers[name] = server

    def _get_server(self, name: str) -> MinecraftServer:
        """Get a server by name, raising an error if not found."""
        if name not in self.servers:
            raise commands.BadArgument(f"Unknown server: `{name}`. Available: {', '.join(self.servers.keys())}")
        return self.servers[name]

    def cog_unload(self):
        """Disconnect all RCON connections on unload."""
        for server in self.servers.values():
            server.disconnect_rcon()

    # --- Main Command Group ---

    @commands.group()
    async def mc(self, ctx):
        """Minecraft server commands."""
        if ctx.invoked_subcommand is None:
            if self.servers:
                server_list = ", ".join(f"`{name}`" for name in self.servers.keys())
                await ctx.send(f"Available servers: {server_list}\n\nUse `~mc <command> <server>` to interact.")
            else:
                await ctx.send("No Minecraft servers configured.")

    @mc.command(name="list")
    async def list_servers(self, ctx):
        """List all configured servers and their status."""
        if not self.servers:
            await ctx.send("No servers configured.")
            return

        lines = []
        for name, server in self.servers.items():
            status = "Online" if server.is_running() else "Offline"
            lines.append(f"**{name}**: {status}")
        await ctx.send("\n".join(lines))

    @mc.command()
    async def status(self, ctx, server: str):
        """Show server status and player count."""
        self.perms.require(ctx.author, f"minecraft.{server}.status")
        srv = self._get_server(server)

        if srv.is_running():
            try:
                players = srv.execute("list")
                await ctx.send(f"**{server}**: Online\n{players}")
            except Exception as e:
                await ctx.send(f"**{server}**: Online (RCON error: {e})")
        else:
            await ctx.send(f"**{server}**: Offline")

    # --- Whitelist Commands ---

    @mc.command(name="whitelist_add")
    async def whitelist_add(self, ctx, server: str, player: str):
        """Add a player to the server whitelist."""
        self.perms.require(ctx.author, f"minecraft.{server}.whitelist")
        srv = self._get_server(server)

        if not srv.is_running():
            await ctx.send(f"Server `{server}` is not running")
            return

        result = srv.execute(f"whitelist add {player}")
        await ctx.send(result)

    @mc.command(name="whitelist_remove")
    async def whitelist_remove(self, ctx, server: str, player: str):
        """Remove a player from the server whitelist."""
        self.perms.require(ctx.author, f"minecraft.{server}.whitelist")
        srv = self._get_server(server)

        if not srv.is_running():
            await ctx.send(f"Server `{server}` is not running")
            return

        result = srv.execute(f"whitelist remove {player}")
        await ctx.send(result)

    @mc.command(name="whitelist")
    async def whitelist_list(self, ctx, server: str):
        """Show the server whitelist."""
        self.perms.require(ctx.author, f"minecraft.{server}.whitelist")
        srv = self._get_server(server)

        if not srv.is_running():
            await ctx.send(f"Server `{server}` is not running")
            return

        result = srv.execute("whitelist list")
        await ctx.send(result)

    # --- Command Execution ---

    @mc.command(name="run")
    async def run_command(self, ctx, server: str, *, command: str):
        """Run a command on the server.

        Operator commands (say, list, give, tp, etc.) require minecraft.<server>.operator
        Other commands require minecraft.<server>.admin
        """
        srv = self._get_server(server)

        # Determine required permission level
        cmd_word = command.split()[0].lower().lstrip("/")
        if cmd_word in OPERATOR_COMMANDS:
            self.perms.require(ctx.author, f"minecraft.{server}.operator")
        else:
            self.perms.require(ctx.author, f"minecraft.{server}.admin")

        if not srv.is_running():
            await ctx.send(f"Server `{server}` is not running")
            return

        result = srv.execute(command)
        await ctx.send(result or "(no output)")

    # --- Server Management ---

    @mc.command()
    async def start(self, ctx, server: str):
        """Start a server."""
        self.perms.require(ctx.author, f"minecraft.{server}.admin")
        srv = self._get_server(server)

        if srv.is_running():
            await ctx.send(f"Server `{server}` is already running")
            return

        await ctx.send(f"Starting `{server}`...")
        await srv.start()
        await ctx.send(f"Server `{server}` started")

    @mc.command()
    async def stop(self, ctx, server: str):
        """Stop a server (only if empty)."""
        self.perms.require(ctx.author, f"minecraft.{server}.admin")
        srv = self._get_server(server)

        if not srv.is_running():
            await ctx.send(f"Server `{server}` is already stopped")
            return

        if not srv.is_empty():
            await ctx.send(f"Server `{server}` has players online. Cannot stop.")
            return

        await ctx.send(f"Stopping `{server}`...")
        await srv.stop()
        await ctx.send(f"Server `{server}` stopped")

    @mc.command()
    async def force_stop(self, ctx, server: str):
        """Force stop a server (even if players are online)."""
        self.perms.require(ctx.author, f"minecraft.{server}.admin")
        srv = self._get_server(server)

        if not srv.is_running():
            await ctx.send(f"Server `{server}` is already stopped")
            return

        await ctx.send(f"Force stopping `{server}`...")
        await srv.stop()
        await ctx.send(f"Server `{server}` stopped")

    @mc.command()
    async def restart(self, ctx, server: str):
        """Restart a server (only if empty)."""
        self.perms.require(ctx.author, f"minecraft.{server}.admin")
        srv = self._get_server(server)

        if srv.is_running() and not srv.is_empty():
            await ctx.send(f"Server `{server}` has players online. Cannot restart.")
            return

        await ctx.send(f"Restarting `{server}`...")
        if srv.is_running():
            await srv.stop()
        await srv.start()
        await ctx.send(f"Server `{server}` restarted")

    # --- Server Configuration ---

    @mc.command(name="add")
    async def add_server(
        self,
        ctx,
        name: str,
        directory: str,
        service_name: str,
        rcon_port: int = 25575,
        server_ip: str = "127.0.0.1",
        rcon_password_env: str = "RCON_PASSWORD"
    ):
        """Add a new Minecraft server configuration.

        Args:
            name: Unique identifier for the server
            directory: Path to the server's directory
            service_name: Systemd service name (e.g. mc-survival.service)
            rcon_port: RCON port (default: 25575)
            server_ip: Server IP address (default: 127.0.0.1)
            rcon_password_env: Environment variable name for RCON password (default: RCON_PASSWORD)

        Example:
            ~mc add survival /opt/minecraft/survival mc-survival.service
            ~mc add creative /opt/minecraft/creative mc-creative.service 25576
        """
        self.perms.require(ctx.author, "minecraft.manage")

        if name in self.servers:
            await ctx.send(f"Server `{name}` already exists. Use `~mc configure` to modify it.")
            return

        # Build the config
        server_config = {
            "server_ip": server_ip,
            "rcon_port": rcon_port,
            "rcon_password_env": rcon_password_env,
            "directory": directory,
            "service_name": service_name,
            "versions": []
        }

        # Save to config
        servers = dict(self.config["servers"])
        servers[name] = server_config
        self.config["servers"] = servers

        # Create and load the server instance
        server = MinecraftServer(name, server_config)
        if server.is_running():
            try:
                server.connect_rcon()
            except Exception:
                pass
        self.servers[name] = server

        await ctx.send(
            f"Added server `{name}`:\n"
            f"- Directory: `{directory}`\n"
            f"- Service: `{service_name}`\n"
            f"- RCON: `{server_ip}:{rcon_port}`\n"
            f"- Password env: `{rcon_password_env}`\n\n"
            f"Grant permissions with: `~perms grant minecraft.{name}.admin @role`"
        )

    @mc.command(name="remove")
    async def remove_server(self, ctx, name: str):
        """Remove a Minecraft server configuration.

        This only removes the bot's configuration - it does NOT delete server files
        or stop the systemd service.
        """
        self.perms.require(ctx.author, "minecraft.manage")

        if name not in self.servers:
            await ctx.send(f"Server `{name}` not found.")
            return

        # Disconnect RCON if connected
        self.servers[name].disconnect_rcon()

        # Remove from memory
        del self.servers[name]

        # Remove from config
        servers = dict(self.config["servers"])
        del servers[name]
        self.config["servers"] = servers

        await ctx.send(f"Removed server `{name}` from configuration.")

    @mc.command(name="configure")
    async def configure_server(
        self,
        ctx,
        name: str,
        setting: str,
        value: str
    ):
        """Modify a server's configuration.

        Available settings:
            server_ip, rcon_port, rcon_password_env, directory, service_name

        Example:
            ~mc configure survival rcon_port 25576
            ~mc configure survival directory /new/path/to/server
        """
        self.perms.require(ctx.author, "minecraft.manage")

        if name not in self.servers:
            await ctx.send(f"Server `{name}` not found.")
            return

        valid_settings = {"server_ip", "rcon_port", "rcon_password_env", "directory", "service_name"}
        if setting not in valid_settings:
            await ctx.send(f"Invalid setting `{setting}`. Valid: {', '.join(valid_settings)}")
            return

        # Convert value for rcon_port
        if setting == "rcon_port":
            try:
                value = int(value)
            except ValueError:
                await ctx.send(f"Invalid port number: `{value}`")
                return

        # Update config
        servers = dict(self.config["servers"])
        server_config = dict(servers[name])
        old_value = server_config.get(setting, "(not set)")
        server_config[setting] = value
        servers[name] = server_config
        self.config["servers"] = servers

        # Reload the server instance
        self.servers[name].disconnect_rcon()
        server = MinecraftServer(name, server_config)
        if server.is_running():
            try:
                server.connect_rcon()
            except Exception:
                pass
        self.servers[name] = server

        await ctx.send(f"Updated `{name}.{setting}`: `{old_value}` → `{value}`")

    @mc.command()
    async def reset_world(self, ctx, server: str):
        """Reset a server's world (deletes all world data)."""
        self.perms.require(ctx.author, f"minecraft.{server}.admin")
        srv = self._get_server(server)

        if srv.is_running() and not srv.is_empty():
            await ctx.send(f"Server `{server}` has players online. Cannot reset.")
            return

        await ctx.send(f"Resetting world for `{server}`...")
        if srv.is_running():
            await srv.stop()

        # Delete world directories
        for world in ["world", "world_nether", "world_the_end"]:
            world_path = srv.get_world_path(world)
            try:
                shutil.rmtree(world_path)
            except FileNotFoundError:
                pass

        await srv.start()
        await ctx.send(f"World reset complete for `{server}`")

    # --- Error Handling ---

    @mc.error
    @status.error
    @whitelist_add.error
    @whitelist_remove.error
    @whitelist_list.error
    @run_command.error
    @start.error
    @stop.error
    @force_stop.error
    @restart.error
    @reset_world.error
    @add_server.error
    @remove_server.error
    @configure_server.error
    async def mc_error(self, ctx, error):
        if isinstance(error, PermissionDenied):
            await ctx.send(f"Permission denied: you need `{error.action}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(str(error))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument: `{error.param.name}`")
        else:
            await ctx.send(f"Error: {error}")


async def setup(bot):
    await bot.add_cog(Cog(bot))
