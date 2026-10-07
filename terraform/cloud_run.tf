resource "google_cloud_run_v2_service" "fraud_email_alert" {
  name     = "fraud-email-alert"
  location = "asia-south1"
  project  = var.project_id

  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = "107755427512-compute@developer.gserviceaccount.com"

    timeout = "300s"

    max_instance_request_concurrency = 80

    scaling {
      max_instance_count = 20
    }

    containers {
      image = "${google_artifact_registry_repository.fraud_email_alert.registry_uri}/fraud-email-alert:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "SMTP_SERVER"
        value = "smtp.gmail.com"
      }

      env {
        name  = "SMTP_PORT"
        value = "587"
      }

      env {
        name  = "SMTP_USERNAME"
        value = "tannup790@gmail.com"
      }

      env {
        name  = "ALERT_FROM_EMAIL"
        value = "tannup790@gmail.com"
      }

      env {
        name  = "ALERT_TO_EMAIL"
        value = "tannup790@gmail.com"
      }

      env {
        name = "SMTP_PASSWORD"

        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.gmail_app_password.id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.cloud_run_secret_access,
    null_resource.build_fraud_email_alert
  ]
}