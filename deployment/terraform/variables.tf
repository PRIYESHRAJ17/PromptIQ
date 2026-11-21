variable "gcp_project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region for Cloud Run deployment (us-central1, us-east1, etc.)"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "Full Docker image URI (e.g. gcr.io/PROJECT/promptiq-backend:latest)"
  type        = string
}
