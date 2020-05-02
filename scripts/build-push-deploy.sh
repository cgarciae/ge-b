PROJECT_ID="machine-learning-250420"
SERVICE="portfolio-scraper"
export IMAGE="gcr.io/$PROJECT_ID/$SERVICE:0.0.1"


export API_TOKEN="466e656e18bf0bcbbca9779ce7e637e014752929b5b46235fa8fdff22580267829df0649a92a20ab88c3d6e80f32dfd75674f8a4e8b3c2c02931023920f274c63a109210af8ed947c99104ab33de107de580fbf8ddf816cded1a1bd0ddb6d6ded22c5f9f5e3fab25537e42a252f9d96dcee30fcfd8e5224828e336e7bef5d0f8771b5dc09f03646fa5aacdb2c83775a944e6e6486e5031da9fc67b2eb3315f09ff0081ad95c8b5d5fb54db6dc5e769264952b9702bbc2288ec99ce272bac3e7d62cc1f9c5d731b3fa334419cef31bb4623ee7aef5bfd4cd804b30568e3c5ab68bf4a916d6c84330ffb42355ccb26755925685cdd03bc3275be4973b5ef8a8d28"
export WORKERS="4"
export TASK_BUCKET="snappr-tasks"
export TASK_FOLDER="portfolio-scaper"
export TOPIC_NAME="projects/machine-learning-250420/topics/portfolio-scraper"
export GOOGLE_APPLICATION_CREDENTIALS="credentials.json"

export CLASSIFIER_TOKEN="466e656e18bf0bcbbca9779ce7e637e014752929b5b46235fa8fdff22580267829df0649a92a20ab88c3d6e80f32dfd75674f8a4e8b3c2c02931023920f274c63a109210af8ed947c99104ab33de107de580fbf8ddf816cded1a1bd0ddb6d6ded22c5f9f5e3fab25537e42a252f9d96dcee30fcfd8e5224828e336e7bef5d0f8771b5dc09f03646fa5aacdb2c83775a944e6e6486e5031da9fc67b2eb3315f09ff0081ad95c8b5d5fb54db6dc5e769264952b9702bbc2288ec99ce272bac3e7d62cc1f9c5d731b3fa334419cef31bb4623ee7aef5bfd4cd804b30568e3c5ab68bf4a916d6c84330ffb42355ccb26755925685cdd03bc3275be4973b5ef8a8d28"
export CLASSIFIER_ENDPOINT="https://portfolio-classifier-davhzjzb6q-ue.a.run.app/api/classify"


CONCURRENCY=1
MEMORY="2Gi"
TIMEOUT=600
#############################################################
# args
#############################################################
PUSH=true
BUILD=true
DEPLOY=true

for var in "$@"; do
    if [ $var == "--no-build" ]; then
        BUILD=false
    elif [ $var == "--no-push" ]; then
        PUSH=false
    elif [ $var == "--no-deploy" ]; then
        DEPLOY=false
    fi
done

#############################################################
# local build
#############################################################

if $BUILD; then
    docker-compose build server
fi
if $PUSH; then
    docker push $IMAGE
fi
if $DEPLOY; then
    gcloud beta run deploy \
        $SERVICE \
        --image $IMAGE \
        --allow-unauthenticated \
        --memory $MEMORY \
        --concurrency $CONCURRENCY \
        --timeout $TIMEOUT \
        --platform managed \
        --set-env-vars "API_TOKEN=${API_TOKEN},WORKERS=${WORKERS},TASK_BUCKET=${TASK_BUCKET},TASK_FOLDER=${TASK_FOLDER},TOPIC_NAME=${TOPIC_NAME},GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS},CLASSIFIER_TOKEN=$CLASSIFIER_TOKEN,CLASSIFIER_ENDPOINT=$CLASSIFIER_ENDPOINT"
fi


#############################################################
# cloud build
#############################################################

# gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE