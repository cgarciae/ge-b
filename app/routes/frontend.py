import io

from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.requests import Request


from . import shared

router = APIRouter()


@router.get("/")
async def read_item(request: Request):
    return shared.templates.TemplateResponse("upload.html", {"request": request})


@router.post("/upload")
async def upload_item(request: Request, *, file: UploadFile = File(...)):
    # import tensorflow as tf
    # import rawpy
    # import yaml
    # import cv2
    # import pickle
    # import pandas as pd

    # model = tf.keras.models.load_model(f"{model_path}/saved_model")

    # with open(f"{model_path}/label_encoder.pkl", "rb") as f:
    #     label_encoder = pickle.load(f)

    # with open(f"{model_path}/training/params.yml", "r") as f:
    #     params = yaml.safe_load(f)

    # print(await request.form())
    contents = await file.read()

    payload = automl.types.ExamplePayload(
        image=automl.types.Image(image_bytes=contents)
    )

    response = shared.automl_client.predict(
        shared.model_full_id, payload, {"score_threshold": "0.5"}
    )

    print(type(response.payload[0].display_name), response.payload[0])

    payload = response.payload[0]

    return shared.templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "class_name": payload.display_name,
            "score": f"{int(payload.classification.score * 100)}%",
        },
    )
