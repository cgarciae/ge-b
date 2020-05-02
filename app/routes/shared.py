from starlette.templating import Jinja2Templates

from app import params
import google.auth
from google.cloud import pubsub_v1, storage


templates = Jinja2Templates(directory="app/templates")

gcloud_credentials, gcloud_project = google.auth.default()

pubsub_publisher = pubsub_v1.PublisherClient(credentials=gcloud_credentials)
storage_client = storage.Client(credentials=gcloud_credentials)

