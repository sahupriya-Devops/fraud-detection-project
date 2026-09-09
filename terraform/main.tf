data "google_project" "current" {
  project_id = var.project_id
}

resource "google_pubsub_topic" "fraud_events" {
  name    = "fraud-events"
  project = var.project_id
}

resource "google_pubsub_subscription" "fraud_processor" {
  name  = "fraud-processor"
  topic = google_pubsub_topic.fraud_events.id

  project = var.project_id
}