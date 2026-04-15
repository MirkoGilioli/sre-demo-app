output "artifact_registry_repo" {
  value = google_artifact_registry_repository.repo.name
}

output "backend_sa_email" {
  value = google_service_account.backend_sa.email
}

output "region" {
  value = var.region
}
