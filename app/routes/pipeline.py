import asyncio
import base64
import io
import json
import typing as tp
import uuid
from datetime import datetime
from urllib.parse import urlparse

import aiohttp
import PIL.Image
import tzlocal
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import params, utils

from . import scraper, shared, task as task_mod

router = APIRouter()


@router.post("/pipeline", response_model=task_mod.Task)
async def pipeline(body: dict = Body(...)):

    pubsub_task = task_mod.PubSubTask(
        **json.loads(base64.b64decode(body["message"]["data"]))
    )

    if pubsub_task.api_token != params.api_token:
        return JSONResponse(status_code=401, content=dict(message="Unauthorized"))

    task = pubsub_task.task

    # update task
    task_bucket = shared.storage_client.get_bucket(params.task_bucket)

    # scrape
    print("Scrapping.....")
    task.status = "scrapping"
    update_task(task, task_bucket)

    try:
        scrape_response = await scraper.scrape(
            scraper.ScrapeRequest(
                url=task.url,
                min_width=task.min_width,
                search_depth=task.search_depth,
                max_images=task.max_images,
                max_urls=task.max_urls,
                max_time=task.max_time,
            )
        )

        # classify
        print("Classifying....")
        task.status = "classifying"
        update_task(task, task_bucket)

        async with aiohttp.ClientSession() as session:

            image_scores = await asyncio.gather(
                *[
                    asyncio.create_task(
                        classify(image_url=image_info.src, session=session,)
                    )
                    for image_info in scrape_response.data
                ]
            )

        task.images = image_scores
        task.status = "done"
        update_task(task, task_bucket)

        return task

    except BaseException as e:
        print("Error....")
        task.error = str(e)
        task.status = "error"
        update_task(task, task_bucket)

        raise


async def classify(
    image_url: str, session: aiohttp.ClientSession
) -> task_mod.ImageScores:
    headers = dict(Authorization=f"Bearer {params.classifier_token}")
    data = dict(image_url=image_url)

    async with session.post(
        params.classifier_endpoint, json=data, headers=headers
    ) as response:

        try:
            response.raise_for_status()
        except BaseException as e:
            return task_mod.ImageScores(
                image_url=image_url, scores=[], error=f"Error for {image_url} : {e}",
            )

        return task_mod.ImageScores(**await response.json())


def update_task(task, bucket):

    task.last_modified = datetime.now(tzlocal.get_localzone()).isoformat()
    task_json = json.dumps(task.dict()).encode("utf-8")
    task_blob = bucket.get_blob(f"{params.task_folder}/{task.token}.json")
    task_blob.upload_from_string(task_json)
