import base64
import subprocess
from pathlib import Path

import pulumi
import pulumi_gcp as gcp
import pulumi_docker as docker

# -------------------------------------------------------------------
# constants
# -------------------------------------------------------------------

PROJECT_ID = "garesco"
LAUCHER_PATH = "launcher"


# -------------------------------------------------------------------
# utils
# -------------------------------------------------------------------


def archive_folder(folder_path: str) -> pulumi.AssetArchive:
    assets = {}
    for file in Path(folder_path).iterdir():
        assets[file.name] = pulumi.FileAsset(path=file)

    return pulumi.AssetArchive(assets=assets)


def get_archive_hash(folder_path: str) -> str:
    return run(
        f"find {folder_path} -type f -print0 | sort -z | xargs -0 sha1sum | sha1sum"
    ).split()[0][-8:]


def run(cmd: str) -> str:
    return subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
    ).stdout.decode("utf-8")


def to_b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


# -------------------------------------------------------------------
# config
# -------------------------------------------------------------------

image = docker.Image(
    "image",
    image_name=f"gcr.io/{PROJECT_ID}/scraper:latest",
    build=docker.DockerBuild(
        context=".",
    ),
)

topic = gcp.pubsub.Topic("scraper")

job = gcp.cloudscheduler.Job(
    resource_name="scraper",
    schedule="0 9 * * SUN",
    pubsub_target=gcp.cloudscheduler.JobPubsubTargetArgs(
        topic_name=topic.id,
        data=to_b64("test"),
    ),
    time_zone="America/Bogota",
)

bucket = gcp.storage.Bucket(
    "scraper",
    storage_class="REGIONAL",
    location="us-central1",
    force_destroy=True,
)

archive = pulumi.FileArchive(LAUCHER_PATH)
archive_hash = get_archive_hash(LAUCHER_PATH)


archive = gcp.storage.BucketObject(
    f"launcher-archive",
    name=f"launcher-archive",
    bucket=bucket.name,
    source=archive,
)


function = gcp.cloudfunctions.Function(
    f"launcher-function-{archive_hash}",
    entry_point="main",
    runtime="python38",
    source_archive_bucket=bucket.name,
    source_archive_object=archive.name,
    event_trigger=gcp.cloudfunctions.FunctionEventTriggerArgs(
        event_type="google.pubsub.topic.publish",
        resource=topic.id,
    ),
    environment_variables=dict(
        IMAGE_URI=image.image_name,
        BUCKET_NAME=bucket.name,
        _ARCHIVE_HASH=archive_hash,
    ),
)
