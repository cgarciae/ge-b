import asyncio
import typing as tp

import cytoolz
import pypeln as pl
from python_path import PythonPath

from scraping import utils
import re
import json
import time
import httpx

with PythonPath("."):
    from app import env


class CategoryUrl(tp.NamedTuple):
    category: str
    url: str


async def scrap(toy: bool, headless: bool):
    try:

        async with utils.PagePool(workers=8, headless=headless) as pool:

            print("Login...")
            await login(pool)

            # --------------------------------------------------------------------------
            # get product cateogory urls

            print("Getting product category urls...")
            data = [x async for x in get_product_category_urls(pool=pool)]

            if toy:
                data = cytoolz.take(1, data)

            # --------------------------------------------------------------------------
            # get search urls

            data = pl.task.flat_map(
                lambda url: get_search_urls(url, pool=pool), data, maxsize=1, workers=1
            )
            if toy:
                data = utils.async_take(1, data)

            data = pl.task.map(
                utils.show_progress("Getting search urls"), data, maxsize=1, workers=1
            )

            if toy:
                data = utils.async_take(1, data)

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

            if toy:
                data = utils.async_take(1, data)

            # --------------------------------------------------------------------------
            # get machine data

            data = pl.task.map(
                lambda url: get_machine_data(url, pool=pool),
                data,
                maxsize=1,
                workers=1,
            )
            data = pl.task.filter(
                lambda x: "error" not in x, data, maxsize=1, workers=1,
            )
            data = pl.task.map(
                utils.show_progress("Getting machine data"), data, maxsize=1, workers=1,
            )

            data = await data

        print("DONE")

        async with httpx.AsyncClient(timeout=None) as client:
            client: httpx.AsyncClient

            r = await client.post(
                url="http://escoti.com/machine/bulkScrappingMachine",
                json=dict(apiKey="<TOKEN-APP>", machines=data),
            )

            r.raise_for_status()

            print("text", r.text)

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


async def get_product_category_urls(
    pool: utils.PagePool,
) -> tp.AsyncIterable[CategoryUrl]:

    url = "https://www.kdcapital.com"

    async with pool.get() as page:
        await page.goto(url)

        urls = await utils.querySelectorAllGetProperty(
            page, ".menu-item .kd-menu-item-sub > a", "href"
        )

    for url in urls:
        if url.startswith("https://www.kdcapital.com/product-category/"):
            print(
                "category",
                url.replace("https://www.kdcapital.com/product-category/", ""),
            )
            yield CategoryUrl(url, url)


async def get_search_urls(
    inputs: CategoryUrl, pool: utils.PagePool
) -> tp.List[CategoryUrl]:
    category, url = inputs.category, inputs.url

    async with pool.get() as page:
        await page.goto(url)
        page_numbers = await utils.querySelectorAllGetProperty(
            page, "a.page-numbers", "text"
        )

        page_numbers = map(utils.maybe_int, page_numbers)
        page_numbers = filter(lambda x: x, page_numbers)
        page_numbers = list(page_numbers)
        max_pages = max(page_numbers) if page_numbers else 1

    return [
        CategoryUrl(category, url + f"page/{number}")
        for number in range(1, max_pages + 1)
    ]


async def get_machine_urls(
    inputs: CategoryUrl, pool: utils.PagePool
) -> tp.List[CategoryUrl]:
    category, url = inputs.category, inputs.url
    # print("get_machine_urls", url)

    async with pool.get() as page:

        # raise Exception()
        await page.goto(url)

        hrefs: tp.List[str] = await utils.querySelectorAllGetProperty(
            page, "a.woocommerce-loop-product__link", "href"
        )

    return [CategoryUrl(category, url) for url in hrefs]


async def get_machine_data(inputs: CategoryUrl, pool: utils.PagePool):
    category, url = inputs.category, inputs.url

    """
    {
        apiKey: "<TOKEN-APP>",
        machines:[{
            "name": string(200)         
            "description":  string
            "salePrice": float          
            "condition": int(1) [New : 1, Used : 0]
            "productStatus":  int(11) [In production: 1, Connected to power: 2, In warehouse: 3]
            "deliveryTime": string(10)          
            "creationYear": int(11)         
            "factory": string(100)          
            "model": string(100)            
            "reference": string(100)            
            "capacity": float           
            "tonnage": float            
            "timeOperation": float          
            "power": float          
            "screwDiameter": float
            "eti": string(100),
            "mailScrapping": string(100),           
            "images": Array[String]
        }]
    }
    """

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
                        name: document.querySelector("h1").textContent,
                        description: tds[3].textContent,
                        salePrice: document.querySelector(".price").textContent,
                        creationYear: tds[0].textContent,
                        factory: tds[1].textContent,
                        model: tds[2].textContent,
                        reference: tds[4].textContent,
                        images: Array.from(document.querySelectorAll(".single-product-slider .nav-product-slider .slick-slide")).map(
                            div => div.style.backgroundImage
                        ),

                    }
                } catch(e) {
                    return {
                        error: e.toString()
                    }
                }
            }
        """
        )

    def parse_float(s):
        try:
            return float(s)
        except:
            return 0.0

    def parse_int(s):
        try:
            return int(s)
        except:
            return 0

    if "error" not in data:
        data["name"] = data["name"].strip()
        data["description"] = data["description"].strip()
        data["salePrice"] = parse_float(
            re.sub(r"[\$, ]", "", data["salePrice"]).strip()
        )
        data["condition"] = 0  # Used
        data["productStatus"] = 0
        data["deliveryTime"] = ""
        data["creationYear"] = parse_int(data["creationYear"])
        data["factory"] = data["factory"].strip()
        data["model"] = data["model"].strip()
        data["reference"] = data["reference"].strip()

        # TODO: implement these
        # --------------------------------
        data["capacity"] = 0.0
        data["tonnage"] = 0.0
        data["timeOperation"] = 0.0
        data["power"] = 0.0
        data["screwDiameter"] = 0.0
        # --------------------------------

        data["eti"] = data["reference"]
        data["mailScrapping"] = "kdcapital"
        data["images"] = list({url[5:-2] for url in data["images"]})

        # category / url
        data["category"] = category
        data["linkRef"] = url

    # await asyncio.sleep(max(11 - (time.time() - t0), 0))
    await asyncio.sleep(1)

    # print()
    # print(json.dumps(data, indent=2))

    return data
