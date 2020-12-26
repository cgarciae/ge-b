import os

import datetime
from googleapiclient import discovery


def main(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    Example:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        print(pubsub_message)
    """

    # cmd = r"""
    # gcloud ai-platform jobs submit training $JOB_NAME \
    #     --region us-central1 \
    #     --master-image-uri {image} \
    #     --master-machine-type "n1-standard-8" \
    #     --stream-logs \
    #     --scale-tier "custom" \
    #     --
    # """.format(
    #     image=image
    # )

    (
        discovery.build("ml", "v1", cache_discovery=False)
        .projects()
        .jobs()
        .create(
            parent="projects/garesco",
            body=dict(
                jobId=f"scraping_{datetime.datetime.now().strftime('%y%m%d_%H%M%S')}",
                trainingInput=dict(
                    scaleTier="CUSTOM",
                    region="us-central1",
                    masterType="n1-standard-4",
                    masterConfig=dict(
                        imageUri=os.environ["IMAGE_URI"],
                    ),
                    args=[],
                ),
            ),
        )
        .execute()
    )