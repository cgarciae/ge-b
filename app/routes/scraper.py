import aiohttp
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.requests import Request
from urllib.parse import urlparse
import typing as tp
import time

from app import params, utils

from . import shared
import asyncio
import io
import PIL.Image

router = APIRouter()


class ScrapeRequest(BaseModel):
    url: str
    min_width: int = 800
    search_depth: int = 3
    max_images: int = 1000
    max_urls: int = 1000
    max_time: float = 60 * 15


class ImageInfo(BaseModel):
    src: str
    width: int
    height: int


class ScrapeResponse(BaseModel):
    data: tp.List[ImageInfo]
    error: str = None


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(task_request: ScrapeRequest) -> ScrapeResponse:

    visited = set()
    known_images = set()
    t0 = time.time()
    output_images = []

    async with utils.PagePool(
        workers=params.workers,
    ) as pool, aiohttp.ClientSession() as session:

        try:
            await asyncio.wait_for(
                find_images(
                    url=task_request.url,
                    max_urls=task_request.max_urls,
                    min_width=task_request.min_width,
                    level=task_request.search_depth,
                    visited=visited,
                    known_images=known_images,
                    max_images=task_request.max_images,
                    host=urlparse(task_request.url).netloc,
                    pool=pool,
                    session=session,
                    t0=t0,
                    max_time=task_request.max_time,
                    output_images=output_images,
                ),
                timeout=task_request.max_time,
            )

        except asyncio.exceptions.TimeoutError as e:
            pass

    return ScrapeResponse(data=output_images)


async def find_images(
    url,
    max_urls,
    min_width,
    level,
    visited,
    known_images,
    max_images,
    host,
    pool,
    session,
    t0,
    max_time,
    output_images,
):

    if (
        url in visited
        or len(known_images) > max_images
        or len(visited) >= max_urls
        or time.time() - t0 > max_time
    ):
        return

    visited.add(url)

    async with pool.get() as page:

        # search for images
        try:
            await page.goto(url)
        except:
            return

        # get image urls
        images = await page.querySelectorAllEval("img", "(xs) => xs.map(x => x.src)")
        images = images or []
        images = [image for image in images if image not in known_images]

        if len(images) + len(known_images) > max_images:
            n_images = max_images - len(known_images)
            images = images[:n_images]

        known_images.update(images)

        # load image info
        for task in asyncio.as_completed(
            [
                asyncio.create_task(get_image_info(src, session))
                for src in images
                if src and time.time() - t0 < max_time
            ]
        ):
            image = await task

            if image is not None and image.width >= min_width:
                output_images.append(image)

        # explore links
        if level > 0:
            urls = await page.querySelectorAllEval("a", "(xs) => xs.map(x => x.href)")
            urls = urls or []
            urls = filter(lambda url: urlparse(url).netloc == host, urls)
        else:
            urls = []

    tasks = [
        asyncio.create_task(
            find_images(
                url=url,
                max_urls=max_urls,
                min_width=min_width,
                level=level - 1,
                visited=visited,
                known_images=known_images,
                max_images=max_images,
                host=host,
                pool=pool,
                session=session,
                t0=t0,
                max_time=max_time,
                output_images=output_images,
            )
        )
        for url in urls
    ]

    await asyncio.gather(*tasks)


async def get_image_info(src: str, session: aiohttp.ClientSession) -> ImageInfo:

    try:
        async with session.get(src) as response:

            try:
                response.raise_for_status()
            except:
                return None

            contents = await response.read()

        buffer = io.BytesIO(contents)
        image = PIL.Image.open(buffer)

        return ImageInfo(src=src, width=image.size[0], height=image.size[1])
    except:
        return None


################################
# patch pyppeteer
################################


def patch_pyppeteer():
    import pyppeteer.connection

    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method


patch_pyppeteer()
