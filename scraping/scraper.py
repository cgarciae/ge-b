import asyncio


from python_path import PythonPath
import typer

from tqdm import tqdm


from .sites import kdcapital


def main(debug: bool = False, toy: bool = False, headless: bool = True):

    if debug:
        import ptvsd

        print("Waiting debugger...")
        ptvsd.enable_attach()
        ptvsd.wait_for_attach()
        print("Connected")

    print(asyncio.run(kdcapital.scrap(toy=toy, headless=headless)))


if __name__ == "__main__":
    typer.run(main)
