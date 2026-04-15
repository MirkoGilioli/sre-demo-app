terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtrace.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 6. Service Account for Cloud Build
resource "google_service_account" "cloudbuild_sa" {
  account_id   = "sre-demo-cloudbuild-sa"
  display_name = "SRE Demo Cloud Build Service Account"
}

# 7. IAM Permissions for Cloud Build Service Account
resource "google_project_iam_member" "cb_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

resource "google_project_iam_member" "cb_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

resource "google_project_iam_member" "cb_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# Allow Cloud Build to act as the Backend Service Account
resource "google_service_account_iam_member" "cb_as_backend" {
  service_account_id = google_service_account.backend_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# 2. Firestore Database (Native Mode)
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "sre-demo"
  location_id = "nam5" # Multi-region or pick one
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.services]
}


# 3. Artifact Registry for Docker Images
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "sre-demo-images"
  format        = "DOCKER"

  depends_on = [google_project_service.services]
}

# 4. Service Account for Backend
resource "google_service_account" "backend_sa" {
  account_id   = "sre-demo-backend-sa"
  display_name = "SRE Demo Backend Service Account"
}

# 4b. Service Account for Frontend
resource "google_service_account" "frontend_sa" {
  account_id   = "sre-demo-frontend-sa"
  display_name = "SRE Demo Frontend Service Account"
}

# ... (IAM permissions for backend)

# Allow Cloud Build to act as the Frontend Service Account
resource "google_service_account_iam_member" "cb_as_frontend" {
  service_account_id = google_service_account.frontend_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# 5. IAM Permissions for Backend Service Account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}
