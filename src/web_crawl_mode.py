import asyncio
from src.agent import login_to_website
from src.shell import Shell


class WebCrawlMode(Shell):
    def __init__(self):
        super().__init__()

    def interact(self):
        asyncio.run(login_to_website("https://uoregon.joinhandshake.com/saved-jobs"))
        print("Hello! Working...")