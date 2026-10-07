data "google_secret_manager_secret" "gmail_app_password" {
  secret_id = "gmail-app-password"
  project   = var.project_id
}

resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  project   = var.project_id
  secret_id = data.google_secret_manager_secret.gmail_app_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:107755427512-compute@developer.gserviceaccount.com"
}