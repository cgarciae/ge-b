set -e

# docker args
# get API_TOKEN and EXPORT_DIR env app vars
source scripts/env.sh

# Copy just export model to a different folder
# this for not uploading to gcloud all mlruns that are heavy
rm -rf export_model
cp -r $EXPORT_DIR export_model/
export EXPORT_DIR="export_model"

# cloudrun args
CONCURRENCY=1
MEMORY="512Mi"

#############################################################
# script args
#############################################################
# Choose one, build local and push the image OR build it remote in gcloud
BUILD=false
REMOTE_BUILD=true
# Push local docker image to google image registry for deployment
PUSH=false
# Deploy to cloud run
DEPLOY=true

for var in "$@"; do
    if [ $var == "--no-build" ]; then
        BUILD=false
    elif [ $var == "--no-push" ]; then
        PUSH=false
    elif [ $var == "--no-remote-build" ]; then
        REMOTE_BUILD=false
    elif [ $var == "--no-deploy" ]; then
        DEPLOY=false
    fi
done

#############################################################
# local build
#############################################################
if $BUILD; then
    poetry export -f requirements.txt > requirements.txt
    docker-compose build --no-cache server
fi
if $PUSH; then
    docker push $IMAGE
fi
#############################################################
# cloud build
#############################################################
if $REMOTE_BUILD; then
    poetry export -f requirements.txt > requirements.txt
    gcloud builds submit --config cloudbuild.yaml \
    --substitutions _EXPORT_DIR="$EXPORT_DIR",_IMAGE="$IMAGE"
fi
#############################################################
# deploy built image
#############################################################
if $DEPLOY; then
    ENV_VARS="API_TOKEN=${API_TOKEN},EXPORT_DIR=${EXPORT_DIR}"
    
    gcloud run deploy \
        $SERVICE \
        --image $IMAGE \
        --allow-unauthenticated \
        --memory $MEMORY \
        --concurrency $CONCURRENCY \
        --platform managed \
        --set-env-vars "$ENV_VARS"
fi