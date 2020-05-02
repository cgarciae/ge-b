import os

from . import utils


workers = int(os.getenv("WORKERS", -1))
task_bucket = os.getenv("TASK_BUCKET")
task_folder = os.getenv("TASK_FOLDER")
topic_name = os.getenv("TOPIC_NAME")
api_token = os.getenv("API_TOKEN")

classifier_token = os.getenv("CLASSIFIER_TOKEN")
classifier_endpoint = os.getenv("CLASSIFIER_ENDPOINT")
