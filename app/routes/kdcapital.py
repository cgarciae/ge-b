import time
import typing as tp

from fastapi import APIRouter, Depends
import httpx
from pydantic import BaseModel
from python_path import PythonPath
import asyncio
from app import env
import cytoolz

with PythonPath("."):
    from scraping.scraper import kdcapital
    from scraping import utils as scraper_utils


router = APIRouter()

print(env.app_host)

# ----------------------------------------------------------------
# main
# ----------------------------------------------------------------


class MainRequest(BaseModel):
    limit: int = 0
    debug: bool = False
    headless: bool = True
    workers: int = 8


@router.post("/")
async def main(task: MainRequest):
    async with scraper_utils.PagePool(
        workers=task.workers, headless=task.headless
    ) as pool:

        if task.debug:
            import ptvsd

            print("Waiting debugger...")
            ptvsd.enable_attach()
            ptvsd.wait_for_attach()
            print("Connected")

        await kdcapital.login(pool)

        urls = await kdcapital.get_product_category_urls(pool)

    # --------------------------------------------------------------
    # search urls

    if task.limit:
        urls = urls[:1]

    urls = await asyncio.gather(
        *(
            fetch_search_urls(
                SearchUrlsRequest(url=url, headless=task.headless, workers=task.workers)
            )
            for url in urls
        )
    )

    urls = list(cytoolz.concat(urls))

    # --------------------------------------------------------------
    # machine urls

    if task.limit:
        urls = urls[:1]

    urls = await asyncio.gather(
        *(
            fetch_machine_urls(
                task=MachineUrlsRequest(
                    url=url, headless=task.headless, workers=task.workers
                )
            )
            for url in urls
        )
    )

    urls = list(cytoolz.concat(urls))

    # --------------------------------------------------------------
    # machine data

    if task.limit:
        urls = urls[: task.limit]

    batches = cytoolz.partition_all(3, urls)

    data = await asyncio.gather(
        *(
            fetch_machine_data(
                task=MachineDataRequest(
                    urls=list(urls), headless=task.headless, workers=task.workers
                )
            )
            for urls in batches
        )
    )

    data = list(cytoolz.concat(data))

    return data


# ----------------------------------------------------------------
# search urls
# -----------------------------------------------------------------


class SearchUrlsRequest(BaseModel):
    url: str
    limit: int = 0
    headless: bool = True
    workers: int = 8


@router.post("/search-urls")
async def search_urls(task: SearchUrlsRequest):
    async with scraper_utils.PagePool(
        workers=task.workers, headless=task.headless
    ) as pool:

        await kdcapital.login(pool)

        urls = await kdcapital.get_search_urls(url=task.url, pool=pool)

    return urls


async def fetch_search_urls(task: SearchUrlsRequest):

    async with httpx.AsyncClient(timeout=None) as client:

        r = await client.post(
            f"{env.app_host}/api/kdcapital/search-urls", json=task.dict(), timeout=None
        )

        r.raise_for_status()

        return r.json()


# ----------------------------------------------------------------
# machine urls
# -----------------------------------------------------------------


class MachineUrlsRequest(BaseModel):
    url: str
    limit: int = 0
    headless: bool = True
    workers: int = 8


@router.post("/machine-urls")
async def machine_urls(task: MachineUrlsRequest):
    async with scraper_utils.PagePool(
        workers=task.workers, headless=task.headless
    ) as pool:

        await kdcapital.login(pool)

        urls = await kdcapital.get_machine_urls(url=task.url, pool=pool)

    return urls


async def fetch_machine_urls(task: MachineUrlsRequest):

    async with httpx.AsyncClient(timeout=None) as client:

        r = await client.post(
            f"{env.app_host}/api/kdcapital/machine-urls", json=task.dict(), timeout=None
        )

        r.raise_for_status()

        return r.json()


# ----------------------------------------------------------------
# machine urls
# -----------------------------------------------------------------


class MachineDataRequest(BaseModel):
    urls: tp.List[str]
    limit: int = 0
    headless: bool = True
    workers: int = 8


@router.post("/machine-data")
async def machine_data(task: MachineDataRequest):
    async with scraper_utils.PagePool(
        workers=task.workers, headless=task.headless
    ) as pool:

        await kdcapital.login(pool)

        data = await asyncio.gather(
            *(kdcapital.get_machine_data(url=url, pool=pool) for url in task.urls)
        )

    return data


async def fetch_machine_data(task: MachineDataRequest):

    async with httpx.AsyncClient(timeout=None) as client:

        r = await client.post(
            f"{env.app_host}/api/kdcapital/machine-data", json=task.dict(), timeout=None
        )

        r.raise_for_status()

        return r.json()
