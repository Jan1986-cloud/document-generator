# Document Generator - Terraform Variables

variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "europe-west4"
}

variable "zone" {
  description = "The Google Cloud zone"
  type        = string
  default     = "europe-west4-a"
}

variable "access_token" {
  description = "Temporary GCP access token for debugging"
  type        = string
  sensitive   = true
  nullable    = true
  default     = null
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "document-generator"
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "document_generator"
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "app_user"
}

variable "db_tier" {
  description = "The machine type for the Cloud SQL instance"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "The disk size for the Cloud SQL instance in GB"
  type        = number
  default     = 20
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run services"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run services"
  type        = string
  default     = "512Mi"
}

variable "enable_backup" {
  description = "Enable automated backups for Cloud SQL"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email address for monitoring notifications"
  type        = string
  default     = ""
}
