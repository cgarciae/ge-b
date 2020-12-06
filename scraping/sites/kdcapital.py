import asyncio
import json
import re
import string
import time
import traceback
import typing as tp
from pathlib import Path

import cytoolz
import httpx
import pypeln as pl
from python_path import PythonPath
from scraping import utils
from tqdm.std import tqdm

with PythonPath("."):
    from app import env


class CategoryUrl(tp.NamedTuple):
    category: str
    url: str


TIMEOUT = 10


async def scrap(toy: bool, headless: bool):
    try:
        categories = json.loads(Path("categories.json").read_text())

        async with utils.PagePool(workers=8, headless=headless) as pool:

            print("Login...")
            await login(pool)

            # --------------------------------------------------------------------------
            # get product cateogory urls

            # print("Getting product category urls...")
            data = [
                x
                async for x in get_product_category_urls(
                    pool=pool, categories=categories
                )
            ]

            if toy:
                data = cytoolz.drop(2, data)
                data = cytoolz.take(1, data)

            # --------------------------------------------------------------------------
            # get search urls

            data = pl.task.flat_map(
                lambda url: get_search_urls(url, pool=pool),
                data,
                maxsize=1,
                workers=1,
                timeout=60,
            )
            if toy:
                data = utils.async_take(1, data)

            data = pl.task.map(
                utils.show_progress("Getting search urls"),
                data,
                maxsize=1,
                workers=1,
                timeout=60,
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
                timeout=60,
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
                timeout=60,
            )
            data = pl.task.filter(
                lambda x: "error" not in x, data, maxsize=1, workers=1,
            )
            data = pl.task.map(
                utils.show_progress("Getting machine data"), data, maxsize=1, workers=1,
            )

            data = await data

        body = dict(apiKey="<TOKEN-APP>", machines=data)

        with open(Path("body.json"), "w") as f:
            json.dump(body, f, indent=2)

        async with httpx.AsyncClient(timeout=None) as client:
            client: httpx.AsyncClient

            r = await client.post(
                url="http://escoti.com/machine/bulkScrappingMachine", json=body,
            )

            r.raise_for_status()

            Path("resp.txt").write_text(r.text)

        return data
    except BaseException as e:
        print(e)


async def scrap_sequential(
    toy: bool, headless: bool, body_path: tp.Optional[Path] = None
):
    try:
        if body_path is None:
            categories = json.loads(Path("categories.json").read_text())

            async with utils.PagePool(workers=2, headless=headless) as pool:

                print("Login...")
                await login(pool)

                # --------------------------------------------------------------------------
                # get product cateogory urls

                # print("Getting product category urls...")
                data = []

                category_bar = tqdm(desc="Categories")
                search_url_bar = tqdm(desc="Search Urls")
                machine_url_bar = tqdm(desc="Machine Urls")
                machine_data_bar = tqdm(desc="Machine Data")
                good_machine_bar = tqdm(desc="Good Machines")

                async for category_url in get_product_category_urls(
                    pool=pool, categories=categories
                ):
                    category_bar.update()
                    # print("get_product_category_urls")

                    for search_url in await get_search_urls(category_url, pool=pool):
                        search_url_bar.update()
                        # print("get_search_urls")

                        for machine_url in await get_machine_urls(
                            search_url, pool=pool
                        ):
                            machine_url_bar.update()
                            # print("get_machine_urls")

                            try:
                                machine_data = await asyncio.wait_for(
                                    get_machine_data(machine_url, pool=pool), timeout=30
                                )
                                machine_data_bar.update()
                                # print("get_machine_data")

                                if "error" not in machine_data:
                                    good_machine_bar.update()
                                    data.append(machine_data)
                            except:
                                print("ERROR: get_machine_data")

            body = dict(apiKey="<TOKEN-APP>", machines=data)

            with open(Path("body.json"), "w") as f:
                json.dump(body, f, indent=2)
        else:
            body = json.loads(body_path.read_text())
            data = body["machines"]

        def update_machine(machine):
            machine["eti"] = (
                machine["eti"]
                .replace(" ", "")[:10]
                .translate(str.maketrans("", "", string.punctuation))
            )
            return machine

        data = map(update_machine, data)
        data = filter(lambda machine: machine["images"], data)
        data = list(data)

        body = dict(apiKey="<TOKEN-APP>", machines=data)

        async with httpx.AsyncClient(timeout=None) as client:
            client: httpx.AsyncClient

            r = await client.post(
                url="http://escoti.com/machine/bulkScrappingMachine", json=body,
            )

            r.raise_for_status()

            Path("resp.txt").write_text(r.text)

        return data
    except BaseException as e:
        print(e)
        traceback.print_exc()


async def login(pool: utils.PagePool):

    url = "https://www.kdcapital.com/login/"

    async with pool.get() as page:

        await page.goto(url)
        await page.evaluate(
            """
            document.querySelector(".woocommerce-Input--text").value = "cgarcia.e88@gmail.com";
        """
        )

        await asyncio.gather(
            page.click(".woocommerce-Button"), page.waitForNavigation()
        )

        # await asyncio.sleep(10)


async def get_product_category_urls(
    pool: utils.PagePool, categories: tp.Dict[str, str]
) -> tp.AsyncIterable[CategoryUrl]:
    t0 = time.time()
    url = "https://www.kdcapital.com"

    async with pool.get() as page:
        await page.goto(url)

        urls = await utils.querySelectorAllGetProperty(
            page, ".menu-item .kd-menu-item-sub > a", "href"
        )

    await asyncio.sleep(max(TIMEOUT - (time.time() - t0), 0))

    for url in urls:
        if url.startswith("https://www.kdcapital.com/product-category/"):
            kdc_category = url.replace(
                "https://www.kdcapital.com/product-category/", ""
            )

            category = categories.get(kdc_category, "Other / Miscellaneous")

            # print("kdc_category", kdc_category)
            # print("category", category)

            yield CategoryUrl(category, url)


async def get_search_urls(
    inputs: CategoryUrl, pool: utils.PagePool
) -> tp.List[CategoryUrl]:
    t0 = time.time()
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

    await asyncio.sleep(max(TIMEOUT - (time.time() - t0), 0))

    return [
        CategoryUrl(category, url + f"page/{number}")
        for number in range(1, max_pages + 1)
    ]


async def get_machine_urls(
    inputs: CategoryUrl, pool: utils.PagePool
) -> tp.List[CategoryUrl]:
    t0 = time.time()
    category, url = inputs.category, inputs.url
    # print("get_machine_urls", url)

    async with pool.get() as page:

        # raise Exception()
        await page.goto(url)

        hrefs: tp.List[str] = await utils.querySelectorAllGetProperty(
            page, "a.woocommerce-loop-product__link", "href"
        )

    await asyncio.sleep(max(TIMEOUT - (time.time() - t0), 0))

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
            "productStatus":  int(TIMEOUT) [In production: 1, Connected to power: 2, In warehouse: 3]
            "deliveryTime": string(10)          
            "creationYear": int(TIMEOUT)         
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
    # print("get_machine_data start")
    async with pool.get() as page:
        t0 = time.time()
        # print("get_machine_data before goto")
        await asyncio.wait_for(page.goto(url, timeout=30_000), timeout=30)
        # print("get_machine_data after goto")

        # year, make -> brand, model, title_description, reference -> fi#, price, body tables -> description
        data = await page.evaluate(
            r"""
            () => {
                try {
                    let tds = document.querySelectorAll("table.shop_attributes > tbody > tr > td");
                    var description = Array.from(
                        document
                        .querySelectorAll("table.shop_attributes > tbody")
                    )
                    .slice(1)
                    .flatMap(
                        elem => Array.from(elem.querySelectorAll("tr"))
                    )
                    .map(
                        elem => `${elem.children[0].textContent}: ${elem.children[1].textContent}`
                    )
                    .join("<br>");

                    return {
                        name: `${document.querySelector("h1").textContent} ${tds[3].textContent}`,
                        description: description,
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
        # print("get_machine_data after evaluate")

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
        data["condition"] = "Used"
        # data["productStatus"] = "In production"
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
        data["country"] = "United States"

    await asyncio.sleep(max(TIMEOUT - (time.time() - t0), 0))
    # print("get_machine_data after sleep")
    # await asyncio.sleep(1)

    # print()
    # print(json.dumps(data, indent=2))

    return data
