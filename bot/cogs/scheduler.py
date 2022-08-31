import asyncio
from asyncio import Task
from types import coroutine
from typing import Coroutine

from discord.ext import commands

import bot.cogs.debug


class ServerCogScheduler:
    def __init__(self, data: dict):
        if "persistent" not in data:
            data["persistent"] = []
        if "normal" not in data:
            data["normal"] = []
        self.data: dict[str, list[Task] | dict] = data

    def run_task(self, task: Coroutine, persistent: bool = False) -> None:
        running_task = asyncio.create_task(task)
        if persistent:
            self.data["persistent"].append(running_task)
        else:
            self.data["normal"].append(running_task)


class CogScheduler:
    def __init__(self, data):
        self.data: dict[int, dict[str, list[Task] | dict]] = data

    def get_server(self, server_id: int) -> ServerCogScheduler:
        if server_id not in self.data:
            self.data[server_id] = {}
        return ServerCogScheduler(self.data[server_id])

    def run_task(self, task: Coroutine, persistent: bool = False) -> None:
        inst = self.get_server(0)
        inst.run_task(task, persistent)

    def handle_unload(self):
        for k, v in self.data.items():
            for k1, v1 in v.items():
                if k1 == "persistent":
                    continue
                for item in v1:
                    item.cancel()
                v[k1] = []


class Cog(commands.Cog, name="scheduler"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.tasks: dict[str, dict[int, dict[str, list[Task] | dict]]] = {}

    async def cog_load(self) -> None:
        # Nothing yet, but might need to handle serialization logic or smth
        state_broker: bot.cogs.persistent_state_broker.Cog = self.bot.get_cog("persistent_state_broker")
        debug: bot.cogs.debug.Cog = self.bot.get_cog("debug")
        await debug.debug_print(self.__cog_name__)
        state = state_broker.get_state(self.__cog_name__)
        if state is not None:
            self.tasks = state
        else:
            self.tasks = {}

    async def cog_unload(self) -> None:
        state_broker: bot.cogs.persistent_state_broker.Cog = self.bot.get_cog("persistent_state_broker")
        state_broker.set_state(self.__cog_name__, self.tasks)

    def get_scheduler(self, cog: str) -> CogScheduler:
        if cog not in self.tasks:
            self.tasks[cog] = {}
        return CogScheduler(self.tasks[cog])


async def setup(bot):
    await bot.add_cog(Cog(bot))
