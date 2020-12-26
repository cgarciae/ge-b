import pulumi
import pulumi_gcp as gcp
import base64
from pathlib import Path
import subprocess


# -------------------------------------------------------------------
# utils
# -------------------------------------------------------------------


def archive_folder(folder_path: str) -> pulumi.AssetArchive:
    assets = {}
    for file in Path(folder_path).iterdir():
        assets[file.name] = pulumi.FileAsset(path=file)

    return pulumi.AssetArchive(assets=assets)


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

bucket = gcp.storage.Bucket("scraper")

archive = archive_folder("cloud_function")

archive = gcp.storage.BucketObject(
    "launcher-archive",
    name=f"launcher-archive",
    bucket=bucket.name,
    source=archive,
)

fxn = gcp.cloudfunctions.Function(
    "launcher-function",
    entry_point="main",
    runtime="python38",
    source_archive_bucket=bucket.name,
    source_archive_object=archive.name,
    event_trigger=gcp.cloudfunctions.FunctionEventTriggerArgs(
        event_type="google.pubsub.topic.publish",
        resource=topic.id,
    ),
)
