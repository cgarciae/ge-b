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

resource "google_compute_network" "vpc_network" {
  name = "terraform-network"
}