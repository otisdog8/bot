
from discord.ext import commands
from collections import defaultdict
import random
random.seed()
from discord.ext import commands

class Cog(commands.Cog, name="dad"):
    def __init__(self ,bot):
        self.bot = bot
        self.times = defaultdict(int)

    @commands.command()
    async def command(self ,ctx):
        self.permload()
        if self.permcheck(ctx ,self.commandid):
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            for w in ["i'm" ,"i’m" ,"im" ,"i am", "soy", "estoy", "i m", "|'m", "i [autocorrect_safety_function]", '"i\'m', "i [AUTOCORRECT_IMMUNITY_hehe]".lower()]:
                if w in message.content.lower():
                    result = ""
                    contents = message.content.lower()
                    contents2 = list(message.content)
                    contents3 = list(message.content)

                    content = contents.split(w)
                    if not ((content[0].endswith(" ") or content[0] == "") and content[1].startswith(" ")):
                        continue

                    for i in range(len(content[0])):
                        if content[0][i] == contents2[i].lower():
                            contents3.pop(0)

                    for i in range(len(w)):
                        contents3.pop(0)
                    # content.pop(0)
                    # for j in content:
                    # result += j + w
                    # result = result[1:-1*len(w)]
                    for c in contents3:
                        result += c

                    if message.author.id != 542605369705234434 or random.randint(1, 5) == 2:
                        await message.channel.send("Hi" + result[:1985] + ", I'm Edward")
                        await message.author.edit(nick=result[:31])
                    break


def setup(bot):
    bot.add_cog(Cog(bot))