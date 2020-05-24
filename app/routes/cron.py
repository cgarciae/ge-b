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


class CronRequest(BaseModel):
    ...


@router.post("/")
def start_job(task: CronRequest):
    
    
