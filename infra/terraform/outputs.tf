output "dbt_service_account_email" {
  description = "Email for the dbt runner service account."
  value       = google_service_account.dbt_runner.email
}

output "project_bucket_name" {
  description = "GCS bucket for project."
  value       = google_storage_bucket.project.name
}
