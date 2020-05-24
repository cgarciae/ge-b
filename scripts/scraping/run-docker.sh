# get API_TOKEN and EXPORT_DIR env app vars
source scripts/env.sh

poetry export -f requirements.txt > requirements.txt

docker-compose build server
docker-compose run server --dont-insert


