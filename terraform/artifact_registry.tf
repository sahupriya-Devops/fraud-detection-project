resource "google_artifact_registry_repository" "fraud_email_alert" {
  project       = var.project_id
  location      = "asia-south1"
  repository_id = "fraud-email-alert"
  description   = "Docker repository for fraud email alert service"
  format        = "DOCKER"

  docker_config {
    immutable_tags = false
  }
}