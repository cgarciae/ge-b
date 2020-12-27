
JOB_NAME="scraping_$(date +%s)"
IMAGE="gcr.io/garesco/scraper"

gcloud ai-platform jobs submit training $JOB_NAME \
    --region us-central1 \
    --master-image-uri $IMAGE \
    --master-machine-type "n1-standard-4" \
    --stream-logs \
    --scale-tier "custom" \
    --
    python -m scraping.scraper