from discord.ext import commands


class Cog(commands.Cog, name="cog"):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Cog(bot))
