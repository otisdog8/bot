from dataclasses import dataclass, field
from typing import Optional, Union

import discord
from discord.ext import commands


@dataclass
class AuthorizedUser:
    """Proof that a user has been authorized for a specific action.

    Commands should require this type rather than checking permissions inline.
    This prevents accidentally forgetting to check permissions.
    """
    user: Union[discord.Member, discord.User]
    action: str
    is_root: bool = False
    _valid: bool = field(default=False, repr=False)

    def __post_init__(self):
        if not self._valid:
            raise RuntimeError("AuthorizedUser must be created via PermissionsCog.authorize()")


class PermissionDenied(commands.CheckFailure):
    """Raised when a user lacks permission for an action."""
    def __init__(self, member: Union[discord.Member, discord.User], action: str):
        self.member = member
        self.action = action
        super().__init__(f"{member} lacks permission for {action}")


class Cog(commands.Cog, name="permissions"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.config = bot.get_cog("config").get_config(self.__cog_name__)
        self.config.set_default("global", {"users": {}, "roles": {}})
        self.config.set_default("guilds", {})

        # In-memory state (not persisted)
        self.sudo_as_root: set[int] = set()

    def authorize(
        self,
        member: discord.Member,
        action: str,
        guild: discord.Guild = None
    ) -> Optional[AuthorizedUser]:
        """Attempt to authorize a user for an action.

        Returns AuthorizedUser if authorized, None if not.
        This is the ONLY way to create an AuthorizedUser.
        """
        guild = guild or getattr(member, 'guild', None)

        # Check if user is currently root
        if member.id in self.sudo_as_root:
            return AuthorizedUser(user=member, action=action, is_root=True, _valid=True)

        # Check global user permissions
        global_perms = self.config["global"]
        user_id = str(member.id)
        if user_id in global_perms.get("users", {}):
            if action in global_perms["users"][user_id]:
                return AuthorizedUser(user=member, action=action, _valid=True)

        # Check guild-specific permissions
        if guild:
            guild_id = str(guild.id)
            if guild_id in self.config["guilds"]:
                guild_perms = self.config["guilds"][guild_id]

                # Check guild user permissions
                if user_id in guild_perms.get("users", {}):
                    if action in guild_perms["users"][user_id]:
                        return AuthorizedUser(user=member, action=action, _valid=True)

                # Check guild role permissions
                if hasattr(member, 'roles'):
                    for role in member.roles:
                        role_id = str(role.id)
                        if role_id in guild_perms.get("roles", {}):
                            if action in guild_perms["roles"][role_id]:
                                return AuthorizedUser(user=member, action=action, _valid=True)

        return None

    def require(
        self,
        member: discord.Member,
        action: str,
        guild: discord.Guild = None
    ) -> AuthorizedUser:
        """Like authorize(), but raises PermissionDenied if not authorized."""
        auth = self.authorize(member, action, guild)
        if auth is None:
            raise PermissionDenied(member, action)
        return auth

    def _grant_permission(
        self,
        scope: str,
        target_type: str,
        target_id: str,
        action: str
    ) -> bool:
        """Grant a permission. Returns True if newly granted, False if already existed."""
        if scope == "global":
            global_perms = dict(self.config["global"])
            targets = dict(global_perms.get(target_type, {}))
            if target_id not in targets:
                targets[target_id] = []
            if action in targets[target_id]:
                return False
            targets[target_id] = list(targets[target_id]) + [action]
            global_perms[target_type] = targets
            self.config["global"] = global_perms
        else:
            guilds = dict(self.config["guilds"])
            if scope not in guilds:
                guilds[scope] = {"users": {}, "roles": {}}
            guild_perms = dict(guilds[scope])
            targets = dict(guild_perms.get(target_type, {}))
            if target_id not in targets:
                targets[target_id] = []
            if action in targets[target_id]:
                return False
            targets[target_id] = list(targets[target_id]) + [action]
            guild_perms[target_type] = targets
            guilds[scope] = guild_perms
            self.config["guilds"] = guilds
        return True

    def _revoke_permission(
        self,
        scope: str,
        target_type: str,
        target_id: str,
        action: str
    ) -> bool:
        """Revoke a permission. Returns True if revoked, False if didn't exist."""
        if scope == "global":
            global_perms = dict(self.config["global"])
            targets = dict(global_perms.get(target_type, {}))
            if target_id not in targets or action not in targets[target_id]:
                return False
            targets[target_id] = [a for a in targets[target_id] if a != action]
            if not targets[target_id]:
                del targets[target_id]
            global_perms[target_type] = targets
            self.config["global"] = global_perms
        else:
            guilds = dict(self.config["guilds"])
            if scope not in guilds:
                return False
            guild_perms = dict(guilds[scope])
            targets = dict(guild_perms.get(target_type, {}))
            if target_id not in targets or action not in targets[target_id]:
                return False
            targets[target_id] = [a for a in targets[target_id] if a != action]
            if not targets[target_id]:
                del targets[target_id]
            guild_perms[target_type] = targets
            guilds[scope] = guild_perms
            self.config["guilds"] = guilds
        return True

    # --- Root/Sudo Commands (owner only) ---

    @commands.command()
    @commands.is_owner()
    async def sudo_root(self, ctx):
        """Toggle root mode for owner. Root has all permissions."""
        if ctx.author.id in self.sudo_as_root:
            self.sudo_as_root.remove(ctx.author.id)
            await ctx.send("Root mode disabled")
        else:
            self.sudo_as_root.add(ctx.author.id)
            await ctx.send("Root mode enabled - you have all permissions")

    @commands.command()
    @commands.is_owner()
    async def sudo_as(self, ctx, member: discord.Member, *, command: str):
        """Execute a command as another user (for testing permissions)."""
        msg = ctx.message
        msg.author = member
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)

    # --- Permission Management Commands ---

    @commands.group()
    async def perms(self, ctx):
        """Permission management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @perms.command(name="grant_global")
    async def grant_global(self, ctx, action: str, user: discord.User):
        """Grant a global permission to a user."""
        self.require(ctx.author, "permissions.grant_global")
        if self._grant_permission("global", "users", str(user.id), action):
            await ctx.send(f"Granted `{action}` globally to {user}")
        else:
            await ctx.send(f"{user} already has `{action}` globally")

    @perms.command(name="revoke_global")
    async def revoke_global(self, ctx, action: str, user: discord.User):
        """Revoke a global permission from a user."""
        self.require(ctx.author, "permissions.revoke_global")
        if self._revoke_permission("global", "users", str(user.id), action):
            await ctx.send(f"Revoked `{action}` globally from {user}")
        else:
            await ctx.send(f"{user} doesn't have `{action}` globally")

    @perms.command(name="grant")
    async def grant(self, ctx, action: str, target: Union[discord.Role, discord.Member]):
        """Grant a guild permission to a role or user."""
        self.require(ctx.author, "permissions.grant")
        guild_id = str(ctx.guild.id)
        if isinstance(target, discord.Role):
            target_type = "roles"
            target_id = str(target.id)
            target_name = f"role {target.name}"
        else:
            target_type = "users"
            target_id = str(target.id)
            target_name = str(target)

        if self._grant_permission(guild_id, target_type, target_id, action):
            await ctx.send(f"Granted `{action}` to {target_name}")
        else:
            await ctx.send(f"{target_name} already has `{action}`")

    @perms.command(name="revoke")
    async def revoke(self, ctx, action: str, target: Union[discord.Role, discord.Member]):
        """Revoke a guild permission from a role or user."""
        self.require(ctx.author, "permissions.revoke")
        guild_id = str(ctx.guild.id)
        if isinstance(target, discord.Role):
            target_type = "roles"
            target_id = str(target.id)
            target_name = f"role {target.name}"
        else:
            target_type = "users"
            target_id = str(target.id)
            target_name = str(target)

        if self._revoke_permission(guild_id, target_type, target_id, action):
            await ctx.send(f"Revoked `{action}` from {target_name}")
        else:
            await ctx.send(f"{target_name} doesn't have `{action}`")

    @perms.command(name="list")
    async def list_perms(self, ctx, target: Union[discord.Role, discord.Member] = None):
        """List permissions in this guild, optionally filtered by target."""
        guild_id = str(ctx.guild.id)
        guild_perms = self.config["guilds"].get(guild_id, {"users": {}, "roles": {}})

        lines = []
        if target is None:
            # List all permissions in guild
            for role_id, actions in guild_perms.get("roles", {}).items():
                role = ctx.guild.get_role(int(role_id))
                role_name = role.name if role else f"(deleted role {role_id})"
                for action in actions:
                    lines.append(f"@{role_name}: `{action}`")
            for user_id, actions in guild_perms.get("users", {}).items():
                for action in actions:
                    lines.append(f"<@{user_id}>: `{action}`")
        elif isinstance(target, discord.Role):
            role_id = str(target.id)
            actions = guild_perms.get("roles", {}).get(role_id, [])
            for action in actions:
                lines.append(f"`{action}`")
        else:
            user_id = str(target.id)
            actions = guild_perms.get("users", {}).get(user_id, [])
            for action in actions:
                lines.append(f"`{action}`")

        if lines:
            await ctx.send("\n".join(lines[:20]))  # Limit output
            if len(lines) > 20:
                await ctx.send(f"... and {len(lines) - 20} more")
        else:
            await ctx.send("No permissions found")

    @perms.command(name="check")
    async def check_perms(self, ctx, action: str, target: discord.Member = None):
        """Check if a user has a specific permission."""
        target = target or ctx.author
        auth = self.authorize(target, action)
        if auth:
            root_note = " (root)" if auth.is_root else ""
            await ctx.send(f"{target} has permission `{action}`{root_note}")
        else:
            await ctx.send(f"{target} does NOT have permission `{action}`")

    @perms.command(name="my")
    async def my_perms(self, ctx):
        """Show your permissions in this guild."""
        guild_id = str(ctx.guild.id)
        guild_perms = self.config["guilds"].get(guild_id, {"users": {}, "roles": {}})
        global_perms = self.config["global"]

        actions = set()

        # Global user permissions
        user_id = str(ctx.author.id)
        if user_id in global_perms.get("users", {}):
            actions.update(global_perms["users"][user_id])

        # Guild user permissions
        if user_id in guild_perms.get("users", {}):
            actions.update(guild_perms["users"][user_id])

        # Guild role permissions
        for role in ctx.author.roles:
            role_id = str(role.id)
            if role_id in guild_perms.get("roles", {}):
                actions.update(guild_perms["roles"][role_id])

        if ctx.author.id in self.sudo_as_root:
            await ctx.send("You are root - all permissions granted")
        elif actions:
            action_list = "\n".join(f"- `{a}`" for a in sorted(actions))
            await ctx.send(f"Your permissions:\n{action_list}")
        else:
            await ctx.send("You have no permissions")

    # --- Error Handler ---

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, PermissionDenied):
            await ctx.send(f"Permission denied: you need `{error.action}`")
        # Don't suppress other errors - let them propagate


async def setup(bot):
    await bot.add_cog(Cog(bot))
