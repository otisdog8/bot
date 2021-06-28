from discord.ext import commands
import json


class Cog(commands.Cog, name="config"):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.load_json()
        self.sections = []

    def get_config(self, section):
        if section in self.data:
            data = self.data[section]
        else:
            data = {}
        section = ConfigSection(self, section, data)
        self.sections.append(section)
        return section

    def set_data(self, section, data):
        self.data[section] = data
        self.save_json()

    def load_json(self):
        with open("config.json", "r") as f:
            self.data = json.load(f)

    def save_json(self):
        with open("config.json", "w") as f:
            json.dump(self.data, f, indent="\t")

    @commands.command()
    async def reload_config(self, ctx):
        self.load_json()
        for i in self.sections:
            i.__init__(self, i.section, self.data[i.section])
        await ctx.send("Reloaded config")


class ConfigSection:
    def __init__(self, parent, section, data):
        self.parent = parent
        self.section = section
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, item, value):
        self.data[item] = value
        self.parent.set_data(self.section, self.data)

    def set_default(self, key, value):
        if key not in self.data:
            self.__setitem__(key, value)


def setup(bot):
    bot.add_cog(Cog(bot))
