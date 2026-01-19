provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "iam" {
  project = var.project_id
  service = "iam.googleapis.com"
}

resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  project = var.project_id
  service = "secretmanager.googleapis.com"
}

resource "google_service_account" "dbt_runner" {
  account_id   = "dbt-runner"
  display_name = "dbt runner"
  project      = var.project_id

  depends_on = [google_project_service.iam]
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_iam_member" "dbt_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_project_iam_member" "dbt_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_storage_bucket" "project" {
  name                        = var.project_bucket_name
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true

  depends_on = [google_project_service.storage]
}

resource "google_storage_bucket_iam_member" "dbt_runner_object_viewer" {
  bucket = google_storage_bucket.project.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.dbt_runner.email}"
}
