resource "null_resource" "build_fraud_email_alert" {

  triggers = {
    app_hash = sha256(
      join(
        "",
        [
          filesha256("${path.module}/../email-alert/app.py"),
          filesha256("${path.module}/../email-alert/Dockerfile"),
          filesha256("${path.module}/../email-alert/requirements.txt")
        ]
      )
    )
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/../email-alert"

    command = "gcloud builds submit --project=${var.project_id} --region=asia-south1 --tag=asia-south1-docker.pkg.dev/${var.project_id}/fraud-email-alert/fraud-email-alert:latest ."
  }

  depends_on = [
    google_artifact_registry_repository.fraud_email_alert
  ]
}