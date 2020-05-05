import asyncio
import typing as tp

import cytoolz
import pypeln as pl
from python_path import PythonPath

from scraping import utils
import re
import json
import time

with PythonPath("."):
    from app import env


async def scrap(headless: bool):
    try:

        async with utils.PagePool(workers=8, headless=headless) as pool:

            print("Login...")
            await login(pool)

            # --------------------------------------------------------------------------
            # get product cateogory urls

            print("Getting product category urls...")
            data = await get_product_category_urls(pool=pool)
            data = cytoolz.take(1, data)

            # --------------------------------------------------------------------------
            # get search urls

            data = pl.task.flat_map(
                lambda url: get_search_urls(url, pool=pool), data, maxsize=1, workers=1
            )
            data = utils.async_take(1, data)
            data = pl.task.map(
                utils.show_progress("Getting search urls"), data, maxsize=1, workers=1
            )

            # --------------------------------------------------------------------------
            # get machine urls

            data = pl.task.flat_map(
                lambda url: get_machine_urls(url, pool=pool),
                data,
                maxsize=1,
                workers=1,
            )
            data = pl.task.map(
                utils.show_progress("Getting machine urls"), data, maxsize=1, workers=1,
            )

            # --------------------------------------------------------------------------
            # get machine data

            data = pl.task.map(
                lambda url, element_index: get_machine_data(
                    url, element_index, pool=pool
                ),
                data,
                maxsize=1,
                workers=1,
            )
            data = pl.task.map(
                utils.show_progress("Getting machine data"), data, maxsize=1, workers=1,
            )

            data = await data

            print("DONE")

            return data
    except BaseException as e:
        print(e)


async def login(pool: utils.PagePool):

    url = "https://www.kdcapital.com/login/"

    async with pool.get() as page:

        await page.goto(url)
        await page.evaluate(
            """
            document.querySelector(".woocommerce-Input--text").value = "cgarcia.e88@gmail.com";
        """
        )

        1
        await asyncio.gather(
            page.click(".woocommerce-Button"), page.waitForNavigation()
        )

        # await asyncio.sleep(10)


async def get_product_category_urls(pool: utils.PagePool) -> tp.List[str]:

    url = "https://www.kdcapital.com"

    async with pool.get() as page:
        await page.goto(url)

        urls = await utils.querySelectorAllGetProperty(
            page, ".menu-item .kd-menu-item-sub > a", "href"
        )

    return [
        url
        for url in urls
        if url.startswith("https://www.kdcapital.com/product-category/")
    ]


async def get_search_urls(url: str, pool: utils.PagePool) -> tp.List[str]:

    async with pool.get() as page:
        await page.goto(url)
        page_numbers = await utils.querySelectorAllGetProperty(
            page, "a.page-numbers", "text"
        )

        page_numbers = map(utils.maybe_int, page_numbers)
        page_numbers = filter(lambda x: x, page_numbers)
        page_numbers = list(page_numbers)
        max_pages = max(page_numbers) if page_numbers else 1

    return [url + f"page/{number}" for number in range(1, max_pages + 1)]


async def get_machine_urls(url: str, pool: utils.PagePool) -> tp.List[str]:

    # print("get_machine_urls", url)

    async with pool.get() as page:

        # raise Exception()
        await page.goto(url)

        hrefs = await utils.querySelectorAllGetProperty(
            page, "a.woocommerce-loop-product__link", "href"
        )

    return hrefs


async def get_machine_data(url: str, pool: utils.PagePool):

    # print("get_machine_data", url)

    async with pool.get() as page:
        t0 = time.time()
        await page.goto(url)

        # year, make -> brand, model, title_description, reference -> fi#, price, body tables -> description
        data = await page.evaluate(
            r"""
            () => {
                try {
                    let tds = document.querySelectorAll("table.shop_attributes > tbody > tr > td");

                    return {
                        title: document.querySelector("h1").textContent,
                        price: document.querySelector(".price").textContent,
                        images: Array.from(document.querySelectorAll(".single-product-slider .nav-product-slider .slick-slide")).map(
                            div => div.style.backgroundImage
                        ),
                        year: tds[0].textContent,

                    }
                } catch(e) {
                    return {
                        error: e.toString()
                    }
                }
            }
        """
        )

    if "error" not in data:
        data["title"] = data["title"].strip()
        data["price"] = re.sub(r"[\$, ]", "", data["price"])
        data["images"] = list({url[5:-2] for url in data["images"]})

    # await asyncio.sleep(max(11 - (time.time() - t0), 0))
    await asyncio.sleep(1)

    # print()
    # print(data)

    return data
