import asyncio
import typing as tp

import pyppeteer


class PagePool:
    def __init__(self, workers: int, launch_args: tp.Tuple[str] = tuple()):
        self.workers = workers
        self.queue: tp.Optional[asyncio.Queue] = None
        self.browser: tp.Optional[pyppeteer.Browser] = None
        self.launch_args = launch_args + ("--no-sandbox",)

    def get(self):

        return PageManager(self.queue, self.browser)

    async def __aenter__(self):

        self.browser = await pyppeteer.launch(headless=True, args=self.launch_args)
        self.queue = asyncio.Queue()

        for i in range(self.workers):
            self.queue.put_nowait(None)

        return self

    async def __aexit__(self, *exc_info):

        if self.browser is not None:
            await self.browser.close()


class PageManager:
    def __init__(self, queue, browser):
        self.queue = queue
        self.browser = browser
        self.page = None

    async def __aenter__(self):
        self.page = await self.queue.get()

        if self.page is None:
            self.page = await self.browser.newPage()

        return self.page

    async def __aexit__(self, *exc_info):
        self.queue.put_nowait(self.page)
