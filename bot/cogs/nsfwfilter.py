import os

from discord.ext import commands
from fastai.vision.all import *

class Cog(commands.Cog, name="cog"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        dirname = os.path.dirname(__file__)
        modelpath = os.path.join(dirname, 'resnet152_model_v2.pth')
        self.learn = vision_learner(data, models.resnet152, metrics=accuracy)



async def setup(bot):
    await bot.add_cog(Cog(bot))

