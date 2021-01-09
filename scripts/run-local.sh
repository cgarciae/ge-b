

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"

python -m scraping.scraper \
    --bucket-name "scraper-3f6deee" \
    "$@"
