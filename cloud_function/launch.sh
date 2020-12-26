
gcloud ai-platform jobs submit training $JOB_NAME \
  --region $REGION \
  --master-image-uri $IMAGE \
  --master-machine-type "n1-standard-8" \
  --stream-logs \
  --scale-tier "custom" \
  -- \
  --dont-insert