# Terraform Variables voor Document Generatie App

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  validation {
    condition     = length(var.project_id) > 0
    error_message = "Project ID mag niet leeg zijn."
  }
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "europe-west4"
  validation {
    condition = contains([
      "europe-west1", "europe-west2", "europe-west3", "europe-west4",
      "europe-west6", "europe-central2", "us-central1", "us-east1"
    ], var.region)
    error_message = "Region moet een geldige Google Cloud region zijn."
  }
}

variable "zone" {
  description = "Google Cloud Zone"
  type        = string
  default     = "europe-west4-a"
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment moet development, staging, of production zijn."
  }
}

variable "db_name" {
  description = "Database naam"
  type        = string
  default     = "document_generator"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database naam moet beginnen met een letter en mag alleen letters, cijfers en underscores bevatten."
  }
}

variable "db_user" {
  description = "Database gebruikersnaam"
  type        = string
  default     = "app_user"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_user))
    error_message = "Database gebruikersnaam moet beginnen met een letter en mag alleen letters, cijfers en underscores bevatten."
  }
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
  validation {
    condition = contains([
      "db-f1-micro", "db-g1-small", "db-n1-standard-1", "db-n1-standard-2",
      "db-n1-standard-4", "db-n1-standard-8", "db-n1-standard-16"
    ], var.db_tier)
    error_message = "Database tier moet een geldige Cloud SQL tier zijn."
  }
}

variable "db_disk_size" {
  description = "Database disk grootte in GB"
  type        = number
  default     = 10
  validation {
    condition     = var.db_disk_size >= 10 && var.db_disk_size <= 1000
    error_message = "Database disk grootte moet tussen 10 en 1000 GB zijn."
  }
}

variable "notification_email" {
  description = "Email adres voor monitoring notificaties"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.notification_email))
    error_message = "Notification email moet een geldig email adres zijn."
  }
}

variable "domain_name" {
  description = "Custom domain naam voor de applicatie (optioneel)"
  type        = string
  default     = ""
}

variable "ssl_certificate_name" {
  description = "Naam van het SSL certificaat (optioneel)"
  type        = string
  default     = ""
}

variable "enable_cdn" {
  description = "Enable Cloud CDN voor static assets"
  type        = bool
  default     = false
}

variable "min_instances" {
  description = "Minimum aantal Cloud Run instances"
  type        = number
  default     = 0
  validation {
    condition     = var.min_instances >= 0 && var.min_instances <= 10
    error_message = "Minimum instances moet tussen 0 en 10 zijn."
  }
}

variable "max_instances" {
  description = "Maximum aantal Cloud Run instances"
  type        = number
  default     = 10
  validation {
    condition     = var.max_instances >= 1 && var.max_instances <= 100
    error_message = "Maximum instances moet tussen 1 en 100 zijn."
  }
}

variable "cpu_limit" {
  description = "CPU limit per Cloud Run instance"
  type        = string
  default     = "1000m"
  validation {
    condition     = can(regex("^[0-9]+m?$", var.cpu_limit))
    error_message = "CPU limit moet een geldig formaat hebben (bijv. 1000m of 1)."
  }
}

variable "memory_limit" {
  description = "Memory limit per Cloud Run instance"
  type        = string
  default     = "512Mi"
  validation {
    condition     = can(regex("^[0-9]+(Mi|Gi)$", var.memory_limit))
    error_message = "Memory limit moet een geldig formaat hebben (bijv. 512Mi of 1Gi)."
  }
}

variable "request_timeout" {
  description = "Request timeout in seconden"
  type        = number
  default     = 300
  validation {
    condition     = var.request_timeout >= 1 && var.request_timeout <= 3600
    error_message = "Request timeout moet tussen 1 en 3600 seconden zijn."
  }
}

variable "enable_backup" {
  description = "Enable automatische database backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Aantal dagen om backups te bewaren"
  type        = number
  default     = 30
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention moet tussen 1 en 365 dagen zijn."
  }
}

variable "enable_monitoring" {
  description = "Enable monitoring en alerting"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Log level voor de applicatie"
  type        = string
  default     = "INFO"
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level moet DEBUG, INFO, WARNING, ERROR, of CRITICAL zijn."
  }
}

variable "enable_cors" {
  description = "Enable CORS voor de API"
  type        = bool
  default     = true
}

variable "cors_origins" {
  description = "Toegestane CORS origins"
  type        = list(string)
  default     = ["*"]
}

variable "jwt_secret_key" {
  description = "Secret key voor JWT tokens (wordt automatisch gegenereerd als leeg)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "session_timeout" {
  description = "Session timeout in minuten"
  type        = number
  default     = 60
  validation {
    condition     = var.session_timeout >= 5 && var.session_timeout <= 1440
    error_message = "Session timeout moet tussen 5 en 1440 minuten zijn."
  }
}

variable "max_file_size" {
  description = "Maximum bestandsgrootte voor uploads in MB"
  type        = number
  default     = 10
  validation {
    condition     = var.max_file_size >= 1 && var.max_file_size <= 100
    error_message = "Maximum file size moet tussen 1 en 100 MB zijn."
  }
}

variable "enable_rate_limiting" {
  description = "Enable rate limiting voor API endpoints"
  type        = bool
  default     = true
}

variable "rate_limit_requests" {
  description = "Aantal requests per minuut per IP"
  type        = number
  default     = 100
  validation {
    condition     = var.rate_limit_requests >= 10 && var.rate_limit_requests <= 1000
    error_message = "Rate limit moet tussen 10 en 1000 requests per minuut zijn."
  }
}

variable "google_oauth_client_id" {
  description = "Google OAuth Client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_oauth_client_secret" {
  description = "Google OAuth Client Secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "smtp_server" {
  description = "SMTP server voor email verzending"
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP poort"
  type        = number
  default     = 587
  validation {
    condition     = var.smtp_port > 0 && var.smtp_port <= 65535
    error_message = "SMTP poort moet tussen 1 en 65535 zijn."
  }
}

variable "smtp_username" {
  description = "SMTP gebruikersnaam"
  type        = string
  default     = ""
  sensitive   = true
}

variable "smtp_password" {
  description = "SMTP wachtwoord"
  type        = string
  default     = ""
  sensitive   = true
}

variable "from_email" {
  description = "Van email adres voor uitgaande emails"
  type        = string
  default     = ""
  validation {
    condition = var.from_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.from_email))
    error_message = "From email moet een geldig email adres zijn of leeg."
  }
}

variable "enable_debug" {
  description = "Enable debug mode (alleen voor development)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags om toe te voegen aan alle resources"
  type        = map(string)
  default     = {}
}

