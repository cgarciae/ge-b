# get API_TOKEN and EXPORT_DIR env app vars
source scripts/env.sh
# Copy just export model to a different folder
rm -rf export_model
cp -r $EXPORT_DIR export_model/
export EXPORT_DIR="export_model"

poetry export -f requirements.txt > requirements.txt

docker-compose build server
docker-compose up "$@" server


