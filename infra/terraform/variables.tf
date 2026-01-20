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
