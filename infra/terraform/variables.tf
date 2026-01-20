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

variable "raw_dataset_id" {
  type        = string
  description = "BigQuery dataset id for raw external tables."
  default     = "raw"
}

variable "presentation_dataset_id" {
  type        = string
  description = "BigQuery dataset id for presentation tables."
  default     = "presentation"
}
