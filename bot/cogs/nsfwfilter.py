import os

import discord
from discord.ext import commands
from fastai.vision.all import *

class Cog(commands.Cog, name="cog"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        dirname = os.path.dirname(__file__)
        modelpath = os.path.join(dirname, 'nsfw.model')
        self.learn = load_learner(modelpath)

    async def process_attachment(self, attachment: discord.Attachment, message: discord.Message):
        # If not in nsfw channel
        # Run prediction on attachment - if nsfw above 0.7 return result
        if message.channel.is_nsfw():
            return

        attachment_raw = await attachment.read()
        val = self.learn.predict(attachment_raw)
        certainty = val[2].storage()[val[1].storage()[0]]
        if certainty > 0.7 and val[0] in ["porn", "hentai"]:
            await message.channel.send(f"Attachment {attachment.filename} is nsfw with certainty {certainty}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        for attachment in message.attachments:
            await self.process_attachment(attachment, message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        bset = set(before.attachments)
        for attachment in after.attachments:
            if attachment in bset:
                continue
            else:
                await self.process_attachment(attachment, after)




async def setup(bot):
    await bot.add_cog(Cog(bot))

