import pyppeteer
import asyncio
from scraping.scraper import kdcapital
from scraping import utils


async def main():

    url = "https://www.kdcapital.com/product-category/plastic-machinery/plastic-injection-molding/"

    async with utils.PagePool(workers=1, headless=False) as pool:
        await kdcapital.login(pool)

        search_urls = await kdcapital.get_search_urls(
            kdcapital.CategoryUrl(category="", url=url), pool=pool
        )

        print(search_urls)


async def main2():
    browser = await pyppeteer.launch(headless=False)

    page = await browser.newPage()

    await page.goto("https://www.kdcapital.com/login/")

    # await page.evaluate(
    #     """() => document.querySelector("#client_email").value = "cgarcia.e88@gmail.com" """
    # )
    button_value = await page.evaluate(
        """() => {
            button = document.querySelector(".woocommerce-Button")
            return button.value
        }
        """
    )

    print(button_value)

    # await page.click(".woocommerce-Button")

    await asyncio.sleep(3.0)

    await browser.close()


asyncio.run(main())
