output "dbt_service_account_email" {
  description = "Email for the dbt runner service account."
  value       = google_service_account.dbt_runner.email
}

output "project_bucket_name" {
  description = "GCS bucket for project."
  value       = google_storage_bucket.project.name
}

output "api_service_account_email" {
  description = "Email for the API runner service account."
  value       = google_service_account.api_runner.email
}

output "api_service_name" {
  description = "Cloud Run API service name."
  value       = google_cloud_run_v2_service.api.name
}

output "api_invoker_service_account_email" {
  description = "Email for the API invoker service account."
  value       = google_service_account.api_invoker.email
}

output "api_gateway_url" {
  description = "Public URL for the API Gateway."
  value       = google_api_gateway_gateway.forex_gateway.default_hostname
}

output "cloud_run_url" {
  description = "Direct Cloud Run service URL."
  value       = google_cloud_run_v2_service.api.uri
}
