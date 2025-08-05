import asyncio
from ..abstracts.user_mode import UserMode
from src.utils import Agent

class DevMode(UserMode):
    def __init__(self):
        self.agent = Agent()

    def interact(self):
        asyncio.run(self.agent.probe_website('https://uoregon.joinhandshake.com'))
