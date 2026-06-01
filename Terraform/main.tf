terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = "terraform-demo-498018"
  region  = "us-central1"
  zone    = "us-central1-c"
}



resource "google_storage_bucket" "demo-bucket-storage" {
  name                        = "terraform-demo-498018-demo-bucket"
  location                    = "US"
  force_destroy               = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}


resource "google_bigquery_dataset" "demo-dataset" {
  dataset_id    = var.bg_dataset_name
  friendly_name = "big Query demo data"
  description   = "This is a test description"
  location      = var.location

}