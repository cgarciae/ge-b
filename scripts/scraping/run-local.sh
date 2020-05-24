# get API_TOKEN and EXPORT_DIR env app vars
source scripts/scraping/env.sh

python -m scraping.scraper "$@"