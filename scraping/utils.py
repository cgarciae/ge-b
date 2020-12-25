import asyncio
import typing as tp

import pyppeteer
from tqdm import tqdm


async def async_take(n, aiterable):

    i = 0

    async for x in aiterable:
        if i < n:
            yield x
            i += 1
        else:
            break


def show_progress(msg: str):

    bar = tqdm(desc=msg)

    def _update_bar(x):
        bar.update()
        return x

    return _update_bar


class PagePool:
    def __init__(
        self,
        workers: int,
        headless: bool = True,
        timeout: int = 100_000,
        args: tp.Tuple[str] = tuple(),
    ):
        self.semaphore = asyncio.Semaphore(workers)
        self.browser: tp.Optional[pyppeteer.Browser] = None
        self.headless = headless
        self.timeout = timeout
        self.args = args + ("--no-sandbox",)

    def get(self) -> "PageManager":

        return PageManager(self.semaphore, self.browser, timeout=self.timeout)

    async def __aenter__(self):

        self.browser = await pyppeteer.launch(
            headless=self.headless, args=self.args, dumpio=True, timeout=self.timeout,
        )

        return self

    async def __aexit__(self, *exc_info):

        if self.browser is not None:
            await self.browser.close()


class PageManager:
    def __init__(
        self,
        semaphore: asyncio.Semaphore,
        browser: pyppeteer.browser.Browser,
        timeout: int,
    ):
        self.semaphore = semaphore
        self.browser = browser
        self.page: tp.Optional[pyppeteer.Page] = None
        self.timeout = timeout

    async def __aenter__(self) -> pyppeteer.page.Page:

        await self.semaphore.acquire()

        self.page = await self.browser.newPage()
        self.page.setDefaultNavigationTimeout(self.timeout)

        return self.page

    async def __aexit__(self, *exc_info):
        await self.page.close()
        self.semaphore.release()


def maybe_int(value: str):

    try:
        return int(value)
    except ValueError:
        return None


async def querySelectorAllGetProperty(page, selector, property):
    return await page.querySelectorAllEval(
        selector, f"(xs) => xs.map(x => x.{property})"
    )
