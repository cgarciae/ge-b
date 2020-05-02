#############################################################
# args
#############################################################
PROJECT_ID="machine-learning-250420"
SERVICE="portfolio-scraper"
export IMAGE="gcr.io/$PROJECT_ID/$SERVICE:0.0.1"


export API_TOKEN="466e656e18bf0bcbbca9779ce7e637e014752929b5b46235fa8fdff22580267829df0649a92a20ab88c3d6e80f32dfd75674f8a4e8b3c2c02931023920f274c63a109210af8ed947c99104ab33de107de580fbf8ddf816cded1a1bd0ddb6d6ded22c5f9f5e3fab25537e42a252f9d96dcee30fcfd8e5224828e336e7bef5d0f8771b5dc09f03646fa5aacdb2c83775a944e6e6486e5031da9fc67b2eb3315f09ff0081ad95c8b5d5fb54db6dc5e769264952b9702bbc2288ec99ce272bac3e7d62cc1f9c5d731b3fa334419cef31bb4623ee7aef5bfd4cd804b30568e3c5ab68bf4a916d6c84330ffb42355ccb26755925685cdd03bc3275be4973b5ef8a8d28"
export WORKERS="5"
export TASK_BUCKET="snappr-tasks"
export TASK_FOLDER="portfolio-scaper"
export TOPIC_NAME="projects/machine-learning-250420/topics/portfolio-scraper"
export GOOGLE_APPLICATION_CREDENTIALS="credentials.json"

export CLASSIFIER_TOKEN="466e656e18bf0bcbbca9779ce7e637e014752929b5b46235fa8fdff22580267829df0649a92a20ab88c3d6e80f32dfd75674f8a4e8b3c2c02931023920f274c63a109210af8ed947c99104ab33de107de580fbf8ddf816cded1a1bd0ddb6d6ded22c5f9f5e3fab25537e42a252f9d96dcee30fcfd8e5224828e336e7bef5d0f8771b5dc09f03646fa5aacdb2c83775a944e6e6486e5031da9fc67b2eb3315f09ff0081ad95c8b5d5fb54db6dc5e769264952b9702bbc2288ec99ce272bac3e7d62cc1f9c5d731b3fa334419cef31bb4623ee7aef5bfd4cd804b30568e3c5ab68bf4a916d6c84330ffb42355ccb26755925685cdd03bc3275be4973b5ef8a8d28"
export CLASSIFIER_ENDPOINT="https://portfolio-classifier-davhzjzb6q-ue.a.run.app/api/classify"

docker-compose up "$@" server


