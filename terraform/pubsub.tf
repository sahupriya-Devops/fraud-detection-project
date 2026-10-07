# ============================================================
# FRAUD DETECTION PUB/SUB
# ============================================================

resource "google_pubsub_topic" "fraud_events" {
  name    = "fraud-events"
  project = var.project_id
}

resource "google_pubsub_subscription" "fraud_processor" {
  name  = "fraud-processor"
  topic = google_pubsub_topic.fraud_events.id

  project = var.project_id
}


# ============================================================
# FRAUD ALERT PUB/SUB
# ============================================================

resource "google_pubsub_topic" "fraud_alerts" {
  name    = "fraud-alerts"
  project = var.project_id
}

resource "google_pubsub_subscription" "fraud_alert_processor" {
  name  = "fraud-alert-processor"
  topic = google_pubsub_topic.fraud_alerts.id

  project = var.project_id

  push_config {
    push_endpoint = google_cloud_run_v2_service.fraud_email_alert.uri
  }

  depends_on = [
    google_cloud_run_v2_service.fraud_email_alert
  ]
}