source scripts/env.sh

JOB_NAME="photographer_app_cron_$(date +%s)"
REGION="us-east1"

gcloud ai-platform jobs submit training $JOB_NAME \
  --region $REGION \
  --master-image-uri $IMAGE \
  --master-machine-type "n1-standard-8" \
  --stream-logs \
  --scale-tier "custom" \
  -- \
  --dont-insert