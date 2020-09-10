from discord.ext import commands
from discord import File


class Cog(commands.Cog, name="cog"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def setup_icon_protection(self, ctx):
        icon = ctx.guild.icon_url
        with open("icons/" + str(ctx.guild.id), "wb") as file:
            await icon.save(file)
            await ctx.send("Icon protected!")

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        # Check to see if it's the icon that changed
        if before.icon != after.icon:
            await self.handle_icon_change(after)

    async def handle_icon_change(self, guild):
        with open("icons/" + str(guild.id), "rb") as f:
            icon = f.read()
            await guild.edit(icon=icon)


def setup(bot):
    bot.add_cog(Cog(bot))
