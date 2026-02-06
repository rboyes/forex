provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
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

resource "google_project_service" "bigquery" {
  project = var.project_id
  service = "bigquery.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  project = var.project_id
  service = "secretmanager.googleapis.com"
}

resource "google_project_service" "cloudasset" {
  project = var.project_id
  service = "cloudasset.googleapis.com"
}

resource "google_project_service" "run" {
  project = var.project_id
  service = "run.googleapis.com"
}

resource "google_project_service" "artifactregistry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
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

resource "google_service_account" "api_runner" {
  account_id   = var.api_runner_service_account_id
  display_name = "api runner"
  project      = var.project_id

  depends_on = [google_project_service.iam]
}

resource "google_service_account" "api_invoker" {
  account_id   = var.api_invoker_service_account_id
  display_name = "api invoker"
  project      = var.project_id

  depends_on = [google_project_service.iam]
}

resource "google_project_iam_member" "api_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api_runner.email}"
}

resource "google_bigquery_dataset_iam_member" "api_presentation_viewer" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.presentation.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.api_runner.email}"
}

resource "google_service_account_iam_member" "dbt_runner_wif_user" {
  service_account_id = google_service_account.dbt_runner.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${var.wif_pool_id}/attribute.repository/${var.wif_repository}"
}

data "google_service_account" "terraform_runner" {
  project    = var.project_id
  account_id = split("@", var.terraform_runner_service_account_email)[0]
}

resource "google_service_account_iam_member" "terraform_runner_wif_user" {
  service_account_id = data.google_service_account.terraform_runner.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${var.wif_pool_id}/attribute.repository/${var.wif_repository}"
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

resource "google_storage_bucket_iam_member" "dbt_runner_object_admin" {
  bucket = google_storage_bucket.project.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_bigquery_dataset" "staging" {
  dataset_id = var.staging_dataset_id
  project    = var.project_id
  location   = var.location

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "presentation" {
  dataset_id = var.presentation_dataset_id
  project    = var.project_id
  location   = var.location

  depends_on = [google_project_service.bigquery]
}

resource "google_artifact_registry_repository" "api" {
  location      = var.region
  repository_id = var.artifact_registry_repo_name
  format        = "DOCKER"
  project       = var.project_id

  depends_on = [google_project_service.artifactregistry]
}

locals {
  api_container_image = var.api_container_image != "" ? var.api_container_image : "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo_name}/${var.api_service_name}:latest"
}

resource "google_cloud_run_v2_service" "api" {
  name     = var.api_service_name
  location = var.region
  project  = var.project_id

  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.api_runner.email

    containers {
      image = local.api_container_image
    }
  }

  depends_on = [google_project_service.run]
}

resource "google_cloud_run_v2_service_iam_member" "api_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api_invoker.email}"
}

# API Gateway resources
resource "google_project_service" "apigateway" {
  project = var.project_id
  service = "apigateway.googleapis.com"
}

resource "google_project_service" "servicemanagement" {
  project = var.project_id
  service = "servicemanagement.googleapis.com"
}

resource "google_project_service" "servicecontrol" {
  project = var.project_id
  service = "servicecontrol.googleapis.com"
}

resource "google_api_gateway_api" "forex_api" {
  provider     = google-beta
  project      = var.project_id
  api_id       = "forex-api"
  display_name = "Forex TWI API"

  depends_on = [google_project_service.apigateway]
}

resource "google_api_gateway_api_config" "forex_api_config" {
  provider             = google-beta
  project              = var.project_id
  api                  = google_api_gateway_api.forex_api.api_id
  api_config_id_prefix = "forex-api-config-"
  display_name         = "Forex API Config"

  openapi_documents {
    document {
      path = "openapi.yaml"
      contents = base64encode(templatefile("${path.module}/../../api/openapi.yaml", {
        backend_url  = google_cloud_run_v2_service.api.uri
        backend_host = trimprefix(google_cloud_run_v2_service.api.uri, "https://")
      }))
    }
  }

  gateway_config {
    backend_config {
      google_service_account = google_service_account.api_runner.email
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    google_project_service.servicemanagement,
    google_project_service.servicecontrol
  ]
}

resource "google_api_gateway_gateway" "forex_gateway" {
  provider   = google-beta
  project    = var.project_id
  region     = var.region
  gateway_id = "forex-gateway"
  api_config = google_api_gateway_api_config.forex_api_config.id

  display_name = "Forex API Gateway"

  depends_on = [google_api_gateway_api_config.forex_api_config]
}

# Allow API Gateway service account to invoke Cloud Run
resource "google_cloud_run_v2_service_iam_member" "api_gateway_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api_runner.email}"
}
