# Fashion AI Platform - Complete GCP Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "vision.googleapis.com",
    "redis.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudfunctions.googleapis.com",
    "pubsub.googleapis.com",
    "scheduler.googleapis.com",
    "dns.googleapis.com"
  ])
  
  service = each.key
  disable_on_destroy = false
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "fashion-ai-${var.environment}"
  database_version = "POSTGRES_14"
  region          = var.region
  
  settings {
    tier = var.environment == "prod" ? "db-standard-2" : "db-f1-micro"
    
    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }
    
    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.vpc.id
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }
  
  depends_on = [google_project_service.apis]
}

# Database
resource "google_sql_database" "database" {
  name     = "fashion_ai"
  instance = google_sql_database_instance.main.name
}

# Database user
resource "google_sql_user" "user" {
  name     = "fashion_ai_user"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "fashion-ai-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "fashion-ai-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Cloud Storage Buckets
resource "google_storage_bucket" "images" {
  name     = "${var.project_id}-fashion-ai-images"
  location = "US"
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "uploads" {
  name     = "${var.project_id}-fashion-ai-uploads"
  location = "US"
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Redis Instance
resource "google_redis_instance" "cache" {
  name           = "fashion-ai-cache"
  memory_size_gb = var.environment == "prod" ? 5 : 1
  region         = var.region
  
  authorized_network = google_compute_network.vpc.id
  
  depends_on = [google_project_service.apis]
}

# Secrets
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret-key"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "fashion-ai-backend"
  display_name = "Fashion AI Backend Service Account"
}

resource "google_project_iam_member" "cloud_run_permissions" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/redis.editor",
    "roles/ml.developer"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Build Service Account permissions
resource "google_project_iam_member" "cloud_build_permissions" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

data "google_project" "project" {
  project_id = var.project_id
}

# Outputs
output "database_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "images_bucket" {
  value = google_storage_bucket.images.name
}

output "uploads_bucket" {
  value = google_storage_bucket.uploads.name
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "service_account_email" {
  value = google_service_account.cloud_run.email
}