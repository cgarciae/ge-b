set -e

# docker args
# get API_TOKEN and EXPORT_DIR env app vars
source scripts/env.sh

SUBSTITUTIONS="_EXPORT_DIR=$EXPORT_DIR,_IMAGE=$IMAGE"

#############################################################
# script args
#############################################################
# Choose one, build local and push the image OR build it remote in gcloud
BUILD=true
REMOTE_BUILD=false
PUSH=false


for var in "$@"; do
    if [ $var == "--no-build" ]; then
        BUILD=false
    elif [ $var == "--no-push" ]; then
        PUSH=false
    elif [ $var == "--remote-build" ]; then
        REMOTE_BUILD=true
    fi
done

#############################################################
# build
#############################################################
poetry export -f requirements.txt > requirements.txt

if $REMOTE_BUILD; then
    gcloud builds submit -t $IMAGE
elif $BUILD; then
    docker-compose build --no-cache server
fi
if $PUSH; then
    docker push $IMAGE
fi
