import asyncio
from ..abstracts.user_mode import UserMode
from src.utils import Agent

class DevMode(UserMode):

    async def _run(self):
        async with Agent() as agent:
            await agent.extract_from_remote('https://uoregon.joinhandshake.com/jobs/10093529', {})
            await agent.extract_from_remote('https://uoregon.joinhandshake.com/saved-jobs', {})

    def interact(self):
        asyncio.run(self._run())
