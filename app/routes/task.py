import aiohttp
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.requests import Request
from urllib.parse import urlparse
import typing as tp

from app import params, utils

from . import shared
import asyncio
import io
import PIL.Image
import uuid
from datetime import datetime
import tzlocal
import json

router = APIRouter()


class CreateTaskRequest(BaseModel):
    url: str
    min_width: int = 800
    search_depth: int = 3
    max_images: int = 1000
    max_urls: int = 1000
    max_time: float = 60 * 15


class ClassScore(BaseModel):
    class_name: str
    score: float


class ImageScores(BaseModel):
    image_url: str
    scores: tp.List[ClassScore]
    error: str = None


class Task(BaseModel):
    url: str
    min_width: int = 800
    search_depth: int = 3
    max_images: int = 1000
    max_urls: int = 1000
    max_time: float = 60 * 15
    token: str
    status: str
    created_at: str
    last_modified: str
    images: tp.List[ImageScores] = None
    error: str = None


class PubSubTask(BaseModel):
    task: Task
    api_token: str


@router.post("/task", response_model=Task)
def create_task(task_request: CreateTaskRequest):

    # create task
    current_datetime = datetime.now(tzlocal.get_localzone()).isoformat()
    token = str(uuid.uuid4())

    task = Task(
        url=task_request.url,
        min_width=task_request.min_width,
        search_depth=task_request.search_depth,
        max_images=task_request.max_images,
        max_urls=task_request.max_urls,
        max_time=task_request.max_time,
        token=token,
        status="created",
        created_at=current_datetime,
        last_modified=current_datetime,
    )

    task_json = json.dumps(task.dict()).encode("utf-8")

    # store task state
    bucket = shared.storage_client.get_bucket(params.task_bucket)
    task_blob = bucket.blob(f"{params.task_folder}/{token}.json")
    task_blob.upload_from_string(task_json)

    # push task
    pubsub_task = PubSubTask(task=task, api_token=params.api_token)
    pubsub_data = json.dumps(pubsub_task.dict()).encode("utf-8")
    shared.pubsub_publisher.publish(topic=params.topic_name, data=pubsub_data)

    return task


@router.get("/task", response_model=Task)
def get_task(token: str):

    # store task state
    bucket = shared.storage_client.get_bucket(params.task_bucket)
    task_blob = bucket.get_blob(f"{params.task_folder}/{token}.json")
    task_json = task_blob.download_as_string()

    task = Task(**json.loads(task_json))

    return task
