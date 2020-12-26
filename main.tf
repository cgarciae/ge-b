terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "3.5.0"
    }
  }
  backend "gcs" {
    bucket  = "garesco-tf-state"
    prefix  = "terraform/state"
  }
}

provider "google" {

  credentials = file("credentials.json")

  project = "garesco"
  region  = "us-central1"
  zone    = "us-central1-c"
}

resource "google_pubsub_topic" "scraper_topic" {
  name = "scraper"
}

resource "google_cloud_scheduler_job" "scraper_job" {
  name        = "scraper"
  schedule    = "0 9 * * SUN"

  pubsub_target {
    # topic.id is the topic's full resource name.
    topic_name = google_pubsub_topic.scraper_topic.id
    data       = base64encode("test")
  }
}