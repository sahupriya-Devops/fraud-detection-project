resource "google_bigquery_dataset" "fraud_detection" {
  dataset_id = "fraud_detection"
  project    = var.project_id
  location   = "asia-south1"
}

resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.fraud_detection.dataset_id
  table_id   = "transactions"
  project    = var.project_id

  deletion_protection = false

  schema = <<EOF
[
  {
    "name": "transaction_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "user_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "amount",
    "type": "FLOAT64",
    "mode": "REQUIRED"
  },
  {
    "name": "merchant",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "location",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "status",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "fraud_reason",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "processed_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  }
]
EOF
}