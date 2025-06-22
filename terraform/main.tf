# Document Generator - Terraform Infrastructure Configuration

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "gcs" {
    bucket = "terraform-state-document-generator-gen-lang-client-0695866337"
    prefix = "terraform/state"
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  access_token = var.access_token
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudsql.googleapis.com",
    "run.googleapis.com",
    "vpcaccess.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "artifactregistry.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudtasks.googleapis.com",
    "drive.googleapis.com",
    "docs.googleapis.com",
    "sheets.googleapis.com"
  ])

  service                    = each.value
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}

# Private Service Connection
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  depends_on    = [google_project_service.apis]
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
  depends_on              = [google_project_service.apis]
}

# VPC Access Connector
resource "google_vpc_access_connector" "connector" {
  name          = "${var.project_name}-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  depends_on    = [google_project_service.apis]
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-db"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_project_service.apis
  ]

  settings {
    tier              = var.db_tier
    disk_size         = var.db_disk_size
    disk_type         = "PD_SSD"
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"

    backup_configuration {
      enabled                        = var.enable_backup
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
  }
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
}

# Database User
resource "google_sql_user" "user" {
  name     = var.database_user
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

# Service Accounts managed outside Terraform
data "google_service_account" "app_service_account" {
  account_id = "${var.project_name}-app"
  project    = var.project_id
}

data "google_service_account" "deploy_service_account" {
  account_id = "${var.project_name}-deploy"
  project    = var.project_id
}

data "google_service_account" "backup_service_account" {
  account_id = "${var.project_name}-backup"
  project    = var.project_id
}

# IAM Roles for App Service Account
resource "google_project_iam_member" "app_service_account_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtasks.enqueuer"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_service_account.app_service_account.email}"
}

# IAM Roles for Deploy Service Account
resource "google_project_iam_member" "deploy_service_account_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/cloudsql.admin",
    "roles/storage.admin",
    "roles/iam.serviceAccountUser"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_service_account.deploy_service_account.email}"
}

# IAM Roles for Backup Service Account
resource "google_project_iam_member" "backup_service_account_roles" {
  for_each = toset([
    "roles/cloudsql.admin",
    "roles/storage.admin"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_service_account.backup_service_account.email}"
}

# Storage Buckets
resource "google_storage_bucket" "documents" {
  name          = "${var.project_name}-docs-${var.project_id}"
  location      = "EU"
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = var.project_name
    purpose     = "documents"
  }
}

resource "google_storage_bucket" "templates" {
  name          = "${var.project_name}-templates-${var.project_id}"
  location      = "EU"
  force_destroy = false

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    project     = var.project_name
    purpose     = "templates"
  }
}

resource "google_storage_bucket" "backups" {
  name          = "${var.project_name}-backups-${var.project_id}"
  location      = "EU"
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = var.project_name
    purpose     = "backups"
  }
}

# Artifact Registry
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = var.project_name
  description   = "Docker repository for Document Generator"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

# Secret Manager Secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "db_password_staging" {
  secret_id = "db-password-staging"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password_staging" {
  secret      = google_secret_manager_secret.db_password_staging.id
  secret_data = random_password.db_password.result
}

# JWT Secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "jwt-secret-key"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "jwt_secret_key" {
  secret      = google_secret_manager_secret.jwt_secret_key.id
  secret_data = random_password.jwt_secret.result
}

resource "google_secret_manager_secret" "jwt_secret_key_staging" {
  secret_id = "jwt-secret-key-staging"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "jwt_secret_key_staging" {
  secret      = google_secret_manager_secret.jwt_secret_key_staging.id
  secret_data = random_password.jwt_secret.result
}

# Database URL Secrets
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://${google_sql_user.user.name}:${random_password.db_password.result}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.database.name}"
}

resource "google_secret_manager_secret" "database_url_staging" {
  secret_id = "database-url-staging"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url_staging" {
  secret = google_secret_manager_secret.database_url_staging.id
  secret_data = "postgresql://${google_sql_user.user.name}:${random_password.db_password.result}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.database.name}"
}

# Google API Credentials Secret
resource "google_secret_manager_secret" "google_api_credentials" {
  secret_id = "google-api-credentials"

  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "google_api_credentials" {
  secret      = google_secret_manager_secret.google_api_credentials.id
  secret_data = jsonencode({
    type                        = "service_account"
    project_id                  = var.project_id
    private_key_id              = "placeholder"
    private_key                 = "-----BEGIN PRIVATE KEY-----\nplaceholder\n-----END PRIVATE KEY-----\n"
    client_email                = data.google_service_account.app_service_account.email
    client_id                   = "placeholder"
    auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
    token_uri                   = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/${urlencode(data.google_service_account.app_service_account.email)}"
  })
}

# Cloud Tasks Queue
resource "google_cloud_tasks_queue" "document_processing" {
  name     = "document-processing"
  location = var.region

  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 5
  }

  retry_config {
    max_attempts       = 3
    max_retry_duration = "300s"
    max_backoff        = "60s"
    min_backoff        = "5s"
    max_doublings      = 3
  }

  depends_on = [google_project_service.apis]
}

# Monitoring Alert Policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "High Error Rate - Document Generator"
  combiner     = "OR"

  conditions {
    display_name = "High error rate condition"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"document-generator-backend\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.1

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "email" {
  count        = var.enable_monitoring && var.notification_email != "" ? 1 : 0
  display_name = "Email Notification Channel"
  type         = "email"

  labels = {
    email_address = var.notification_email
  }

  depends_on = [google_project_service.apis]
}

# Outputs
output "database_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "database_private_ip" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "vpc_connector_name" {
  description = "The name of the VPC connector"
  value       = google_vpc_access_connector.connector.name
}

output "app_service_account_email" {
  description = "Email of the app service account"
  value       = data.google_service_account.app_service_account.email
}

output "deploy_service_account_email" {
  description = "Email of the deploy service account"
  value       = data.google_service_account.deploy_service_account.email
}

output "backup_service_account_email" {
  description = "Email of the backup service account"
  value       = data.google_service_account.backup_service_account.email
}

output "storage_bucket_documents" {
  description = "Name of the documents storage bucket"
  value       = google_storage_bucket.documents.name
}

output "storage_bucket_templates" {
  description = "Name of the templates storage bucket"
  value       = google_storage_bucket.templates.name
}

output "storage_bucket_backups" {
  description = "Name of the backups storage bucket"
  value       = google_storage_bucket.backups.name
}

output "artifact_registry_repository" {
  description = "Name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "cloud_tasks_queue" {
  description = "Name of the Cloud Tasks queue"
  value       = google_cloud_tasks_queue.document_processing.name
}
