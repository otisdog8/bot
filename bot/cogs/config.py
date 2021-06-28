from discord.ext import commands
import json


class Cog(commands.Cog, name="config"):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.load_json()
        self.sections = []

    def get_config(self, section):
        section = ConfigSection(self, section)
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
            json.dump(self.data, f)

    @commands.command()
    async def reload_config(self, ctx):
        self.load_json()
        await ctx.send("Reloaded config")


class ConfigSection:
    def __init__(self, parent, section):
        self.parent = parent
        self.section = section
        self.data = {}

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, item, value):
        self.data[item] = value
        self.parent.set_data(self.section, self.data)

    def set_default(self, key, value):
        if key not in self.data:
            self.data[key] = value


def setup(bot):
    bot.add_cog(Cog(bot))
