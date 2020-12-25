import asyncio
import typing as tp
from pathlib import Path

import typer

from .sites import kdcapital


def main(
    body_path: tp.Optional[Path] = None,
    debug: bool = False,
    toy: bool = False,
    headless: bool = True,
):

    if debug:
        import debugpy

        print("Waiting debugger...")
        debugpy.listen(5678)
        debugpy.wait_for_client()

    asyncio.run(
        kdcapital.scrap_sequential(toy=toy, headless=headless, body_path=body_path)
    )


if __name__ == "__main__":
    typer.run(main)
