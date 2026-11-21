terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Secret Manager Resources for Operator Credentials
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "promptiq-jwt-secret"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "promptiq-neon-db-url"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "promptiq-gemini-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "groq_key" {
  secret_id = "promptiq-groq-key"
  replication {
    auto {}
  }
}

# 2. Cloud Run Service (Scales to 0 when idle = ₹0 cost)
resource "google_cloud_run_v2_service" "backend" {
  name     = "promptiq-backend"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0 # Enforces zero-cost when idle
      max_instance_count = 5
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      env {
        name  = "PROMPTIQ_ENV"
        value = "production"
      }
      env {
        name  = "ENFORCE_ZERO_PRICE_ONLY"
        value = "true"
      }
      env {
        name  = "MANAGED_INFERENCE_PRIMARY_ROUTE"
        value = "gemini"
      }

      env {
        name = "PROMPTIQ_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPERATOR_GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 5
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds = 30
      }
    }
  }
}

# 3. Allow Public Unauthenticated Access (for REST API & Telegram Webhook)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
