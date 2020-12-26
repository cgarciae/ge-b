import pulumi
import pulumi_gcp as gcp
import base64
from pathlib import Path
import subprocess


# -------------------------------------------------------------------
# utils
# -------------------------------------------------------------------

PROJECT_ID = "garesco"
IMAGE = "scraper"
IMAGE_URI = f"gcr.io/{PROJECT_ID}/{IMAGE}"
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


build = gcp.cloudbuild.Trigger(
    resource_name="build-image",
    build=gcp.cloudbuild.TriggerBuildArgs(
        images=[IMAGE_URI],
        steps=[
            gcp.cloudbuild.TriggerBuildStepArgs(
                name="gcr.io/cloud-builders/docker",
                args=["build", "-t", IMAGE_URI, "."],
            ),
            gcp.cloudbuild.TriggerBuildStepArgs(
                name="gcr.io/cloud-builders/docker",
                args=["push", IMAGE_URI],
            ),
        ],
    ),
)

bucket = gcp.storage.Bucket("scraper")

archive = pulumi.FileArchive("cloud_function")
archive_hash = get_archive_hash("cloud_function")


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
        IMAGE_URI=IMAGE_URI,
    ),
)
