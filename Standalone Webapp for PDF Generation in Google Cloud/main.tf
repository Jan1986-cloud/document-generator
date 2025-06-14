# Document Generatie App - Terraform Configuration
# Infrastructure as Code voor Google Cloud Platform

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
  
  # Backend configuratie voor state opslag
  backend "gcs" {
    bucket = "terraform-state-document-generator"
    prefix = "terraform/state"
  }
}

# Provider configuratie
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Lokale variabelen
locals {
  app_name = "document-generator"
  labels = {
    app         = local.app_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Random password voor database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Google Cloud APIs activeren
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudsql.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "docs.googleapis.com",
    "sheets.googleapis.com",
    "drive.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtasks.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com"
  ])
  
  service = each.value
  project = var.project_id
  
  disable_dependent_services = false
  disable_on_destroy        = false
}

# Service Accounts
resource "google_service_account" "app_service_account" {
  account_id   = "${local.app_name}-app"
  display_name = "Document Generator Application"
  description  = "Service account voor de Document Generator applicatie"
  project      = var.project_id
}

resource "google_service_account" "deploy_service_account" {
  account_id   = "${local.app_name}-deploy"
  display_name = "Document Generator Deployment"
  description  = "Service account voor deployment van Document Generator"
  project      = var.project_id
}

resource "google_service_account" "backup_service_account" {
  account_id   = "${local.app_name}-backup"
  display_name = "Document Generator Backup"
  description  = "Service account voor backups van Document Generator"
  project      = var.project_id
}

# IAM rollen voor application service account
resource "google_project_iam_member" "app_service_account_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/cloudtasks.enqueuer"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# IAM rollen voor deployment service account
resource "google_project_iam_member" "deploy_service_account_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin",
    "roles/cloudsql.admin"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deploy_service_account.email}"
}

# IAM rollen voor backup service account
resource "google_project_iam_member" "backup_service_account_roles" {
  for_each = toset([
    "roles/cloudsql.admin",
    "roles/storage.admin"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.backup_service_account.email}"
}

# VPC Netwerk
resource "google_compute_network" "vpc_network" {
  name                    = "${local.app_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
  
  depends_on = [google_project_service.apis]
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${local.app_name}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
  project       = var.project_id
  
  private_ip_google_access = true
}

# Firewall rules
resource "google_compute_firewall" "allow_internal" {
  name    = "${local.app_name}-allow-internal"
  network = google_compute_network.vpc_network.name
  project = var.project_id
  
  allow {
    protocol = "tcp"
  }
  
  allow {
    protocol = "udp"
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = ["10.0.0.0/24"]
}

# VPC Access Connector voor Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "${local.app_name}-connector"
  region        = var.region
  project       = var.project_id
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc_network.name
  
  depends_on = [google_project_service.apis]
}

# Cloud SQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "${local.app_name}-db"
  database_version = "POSTGRES_14"
  region           = var.region
  project          = var.project_id
  
  deletion_protection = var.environment == "production" ? true : false
  
  settings {
    tier                        = var.db_tier
    availability_type           = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type                   = "PD_SSD"
    disk_size                   = var.db_disk_size
    disk_autoresize             = true
    disk_autoresize_limit       = 100
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }
    
    maintenance_window {
      day          = 7  # Sunday
      hour         = 4
      update_track = "stable"
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
    
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc_network.id
      enable_private_path_for_google_cloud_services = true
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Private Service Connection voor Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${local.app_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

# Database gebruiker
resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
  project  = var.project_id
}

# Secret Manager voor database wachtwoord
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-app-password"
  project   = var.project_id
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Cloud Storage Buckets
resource "google_storage_bucket" "documents" {
  name          = "${local.app_name}-docs-${var.project_id}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "production"
  
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
  
  labels = local.labels
}

resource "google_storage_bucket" "templates" {
  name          = "${local.app_name}-templates-${var.project_id}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  labels = local.labels
}

resource "google_storage_bucket" "backups" {
  name          = "${local.app_name}-backups-${var.project_id}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
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
  
  labels = local.labels
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = local.app_name
  description   = "Docker repository voor Document Generator applicatie"
  format        = "DOCKER"
  project       = var.project_id
  
  labels = local.labels
  
  depends_on = [google_project_service.apis]
}

# Cloud Tasks Queue
resource "google_cloud_tasks_queue" "document_generation" {
  name     = "document-generation"
  location = var.region
  project  = var.project_id
  
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

# Monitoring Notification Channel (Email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notifications"
  type         = "email"
  project      = var.project_id
  
  labels = {
    email_address = var.notification_email
  }
  
  depends_on = [google_project_service.apis]
}

# Alerting Policy voor hoge error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate"
  project      = var.project_id
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run Error Rate"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05  # 5% error rate
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"  # 30 minutes
  }
  
  depends_on = [google_project_service.apis]
}

# Outputs
output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud Region"
  value       = var.region
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "app_service_account_email" {
  description = "Application service account email"
  value       = google_service_account.app_service_account.email
}

output "deploy_service_account_email" {
  description = "Deployment service account email"
  value       = google_service_account.deploy_service_account.email
}

output "storage_bucket_documents" {
  description = "Documents storage bucket name"
  value       = google_storage_bucket.documents.name
}

output "storage_bucket_templates" {
  description = "Templates storage bucket name"
  value       = google_storage_bucket.templates.name
}

output "storage_bucket_backups" {
  description = "Backups storage bucket name"
  value       = google_storage_bucket.backups.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "vpc_connector_name" {
  description = "VPC Access Connector name"
  value       = google_vpc_access_connector.connector.name
}

