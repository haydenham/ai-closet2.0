# Scalable Backend Module for Fashion AI Platform
# This module creates a highly scalable, well-documented backend infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Variables with comprehensive documentation
variable "project_id" {
  description = "GCP Project ID where resources will be created"
  type        = string
  validation {
    condition     = length(var.project_id) > 0
    error_message = "Project ID cannot be empty."
  }
}

variable "region" {
  description = "Primary GCP region for resource deployment"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod) - affects resource sizing and configuration"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "app_name" {
  description = "Application name used for resource naming and tagging"
  type        = string
  default     = "fashion-ai"
}

# Local values for environment-specific configurations
locals {
  # Environment-specific scaling configurations
  scaling_config = {
    dev = {
      min_instances        = 0
      max_instances        = 10
      cpu_limit           = "1"
      memory_limit        = "2Gi"
      db_tier            = "db-f1-micro"
      redis_memory_gb    = 1
      enable_ha          = false
      backup_retention   = 7
    }
    staging = {
      min_instances        = 1
      max_instances        = 50
      cpu_limit           = "2"
      memory_limit        = "4Gi"
      db_tier            = "db-standard-1"
      redis_memory_gb    = 2
      enable_ha          = false
      backup_retention   = 14
    }
    prod = {
      min_instances        = 2
      max_instances        = 1000
      cpu_limit           = "4"
      memory_limit        = "8Gi"
      db_tier            = "db-standard-4"
      redis_memory_gb    = 10
      enable_ha          = true
      backup_retention   = 30
    }
  }
  
  current_config = local.scaling_config[var.environment]
  
  # Common labels for all resources
  common_labels = {
    environment = var.environment
    application = var.app_name
    managed_by  = "terraform"
    team        = "platform"
  }
}

# VPC Network with proper CIDR allocation for scalability
resource "google_compute_network" "vpc" {
  name                    = "${var.app_name}-vpc-${var.environment}"
  auto_create_subnetworks = false
  description            = "VPC network for ${var.app_name} ${var.environment} environment"
  
  # Enable flow logs for monitoring and debugging
  enable_ula_internal_ipv6 = false
}

# Subnet with sufficient IP range for scaling
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.app_name}-subnet-${var.environment}"
  ip_cidr_range = var.environment == "prod" ? "10.0.0.0/20" : "10.0.0.0/24"  # More IPs for prod
  region        = var.region
  network       = google_compute_network.vpc.id
  description   = "Primary subnet for ${var.app_name} ${var.environment}"
  
  # Enable private Google access for Cloud SQL and other services
  private_ip_google_access = true
  
  # Enable flow logs for network monitoring
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling       = 0.5
    metadata           = "INCLUDE_ALL_METADATA"
  }
}

# Cloud SQL instance with high availability and read replicas for production
resource "google_sql_database_instance" "main" {
  name             = "${var.app_name}-db-${var.environment}"
  database_version = "POSTGRES_14"
  region          = var.region
  
  settings {
    tier                        = local.current_config.db_tier
    availability_type          = local.current_config.enable_ha ? "REGIONAL" : "ZONAL"
    disk_type                  = "PD_SSD"
    disk_size                  = var.environment == "prod" ? 100 : 20
    disk_autoresize           = true
    disk_autoresize_limit     = var.environment == "prod" ? 500 : 100
    
    # Backup configuration with environment-specific retention
    backup_configuration {
      enabled                        = true
      start_time                    = "03:00"
      location                      = var.region
      point_in_time_recovery_enabled = local.current_config.enable_ha
      backup_retention_settings {
        retained_backups = local.current_config.backup_retention
        retention_unit   = "COUNT"
      }
    }
    
    # Network configuration for security
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                              = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
    }
    
    # Performance and monitoring settings
    database_flags {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
    
    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking more than 1 second
    }
    
    # Connection limits based on environment
    database_flags {
      name  = "max_connections"
      value = var.environment == "prod" ? "200" : "100"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length    = 1024
      record_application_tags = true
      record_client_address  = true
    }
  }
  
  # Deletion protection for production
  deletion_protection = var.environment == "prod"
  
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Read replica for production workloads
resource "google_sql_database_instance" "read_replica" {
  count = var.environment == "prod" ? 2 : 0
  
  name                 = "${var.app_name}-db-replica-${count.index + 1}-${var.environment}"
  master_instance_name = google_sql_database_instance.main.name
  region              = var.region
  database_version    = "POSTGRES_14"
  
  replica_configuration {
    failover_target = false
  }
  
  settings {
    tier              = local.current_config.db_tier
    availability_type = "ZONAL"
    disk_type        = "PD_SSD"
    disk_size        = 50
    disk_autoresize  = true
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.app_name}-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Redis instance with high availability for production
resource "google_redis_instance" "cache" {
  name           = "${var.app_name}-cache-${var.environment}"
  memory_size_gb = local.current_config.redis_memory_gb
  region         = var.region
  
  # High availability for production
  tier                    = local.current_config.enable_ha ? "STANDARD_HA" : "BASIC"
  authorized_network      = google_compute_network.vpc.id
  connect_mode           = "PRIVATE_SERVICE_ACCESS"
  
  # Redis configuration for performance
  redis_version     = "REDIS_6_X"
  display_name     = "${var.app_name} Cache ${var.environment}"
  
  # Maintenance window
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }
  
  labels = local.common_labels
}

# Cloud Storage buckets with proper lifecycle management
resource "google_storage_bucket" "images" {
  name     = "${var.project_id}-${var.app_name}-images-${var.environment}"
  location = "US"
  
  # Lifecycle management for cost optimization
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
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
  
  # CORS configuration for web access
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  # Versioning for production
  versioning {
    enabled = var.environment == "prod"
  }
  
  labels = local.common_labels
}

resource "google_storage_bucket" "uploads" {
  name     = "${var.project_id}-${var.app_name}-uploads-${var.environment}"
  location = "US"
  
  # Shorter lifecycle for user uploads
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.common_labels
}

# Service account with minimal required permissions
resource "google_service_account" "backend" {
  account_id   = "${var.app_name}-backend-${var.environment}"
  display_name = "${var.app_name} Backend Service Account (${var.environment})"
  description  = "Service account for ${var.app_name} backend services in ${var.environment}"
}

# IAM roles with principle of least privilege
resource "google_project_iam_member" "backend_permissions" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/redis.editor",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# Monitoring and alerting
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "${var.app_name} High Latency (${var.environment})"
  combiner     = "OR"
  
  conditions {
    display_name = "High response latency"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 2.0
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = []  # Add notification channels as needed
  
  alert_strategy {
    auto_close = "1800s"
  }
}

# Outputs with comprehensive information
output "database_connection_name" {
  description = "Cloud SQL connection name for application configuration"
  value       = google_sql_database_instance.main.connection_name
}

output "database_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "redis_host" {
  description = "Redis instance host for application configuration"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

output "images_bucket_name" {
  description = "Name of the images storage bucket"
  value       = google_storage_bucket.images.name
}

output "uploads_bucket_name" {
  description = "Name of the uploads storage bucket"
  value       = google_storage_bucket.uploads.name
}

output "service_account_email" {
  description = "Email of the backend service account"
  value       = google_service_account.backend.email
}

output "vpc_network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "Name of the primary subnet"
  value       = google_compute_subnetwork.subnet.name
}

output "read_replica_connection_names" {
  description = "Connection names of read replicas (production only)"
  value       = [for replica in google_sql_database_instance.read_replica : replica.connection_name]
}