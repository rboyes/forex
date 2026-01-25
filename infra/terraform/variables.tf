variable "project_id" {
  type        = string
  description = "GCP project id."
  default     = "forex-20260115"
}

variable "region" {
  type        = string
  description = "GCP region for regional resources."
  default     = "europe-west2"
}

variable "location" {
  type        = string
  description = "BigQuery dataset location."
  default     = "europe-west2"
}

variable "project_bucket_name" {
  type        = string
  description = "GCS bucket name for project."
  default     = "forex-20260115"
}

variable "staging_dataset_id" {
  type        = string
  description = "BigQuery dataset id for staging tables."
  default     = "staging"
}

variable "presentation_dataset_id" {
  type        = string
  description = "BigQuery dataset id for presentation tables."
  default     = "presentation"
}

variable "wif_pool_id" {
  type        = string
  description = "Workload Identity Pool id for GitHub Actions."
  default     = "github-pool"
}

variable "wif_repository" {
  type        = string
  description = "GitHub repository allowed to impersonate service accounts."
  default     = "rboyes/forex"
}

variable "terraform_runner_service_account_email" {
  type        = string
  description = "Service account email used by the Terraform GitHub Actions workflow."
  default     = "terraform-runner@forex-20260115.iam.gserviceaccount.com"
}

variable "api_runner_service_account_id" {
  type        = string
  description = "Service account id for the Cloud Run API service."
  default     = "api-runner"
}

variable "api_service_name" {
  type        = string
  description = "Cloud Run service name for the API."
  default     = "forex-api"
}

variable "artifact_registry_repo_name" {
  type        = string
  description = "Artifact Registry repo for container images."
  default     = "forex"
}

variable "api_container_image" {
  type        = string
  description = "Container image URI for the API (optional; defaults to the Artifact Registry repo)."
  default     = "gcr.io/cloudrun/hello"
}

variable "api_invoker_service_account_id" {
  type        = string
  description = "Service account id allowed to invoke the private Cloud Run service."
  default     = "api-invoker"
}
