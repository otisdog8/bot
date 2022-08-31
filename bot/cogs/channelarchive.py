from datetime import datetime
from discord.ext import commands


class Cog(commands.Cog, name="channelarchive"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command
    @commands.is_owner
    async def archive_channel(ctx):
        async for message in ctx.channel.history():
            for attachment in message.attachments:
                await attachment.save(attachment.filename+str(datetime.now()))


async def setup(bot):
    await bot.add_cog(Cog(bot))

