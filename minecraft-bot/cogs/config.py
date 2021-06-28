from discord.ext import commands
import json


class Cog(commands.Cog, name="config"):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.load_json()

    def get_config(self, section):
        self.load_json()
        if section in self.data:
            return self.data[section]
        else:
            return {}

    def set_config(self, section, config):
        self.data[section] = config
        self.save_json()

    def load_json(self):
        with open("config.json", "r") as f:
            json.load(f)

    def save_json(self):
        with open("config.json", "w") as f:
            json.dump(self.data, f)


def setup(bot):
    bot.add_cog(Cog(bot))
