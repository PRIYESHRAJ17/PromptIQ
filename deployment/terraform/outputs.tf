output "service_url" {
  description = "Public HTTPS URL of the deployed PromptIQ Cloud Run backend"
  value       = google_cloud_run_v2_service.backend.uri
}

output "telegram_webhook_url" {
  description = "Public URL to register with Telegram Bot API (setWebhook)"
  value       = "${google_cloud_run_v2_service.backend.uri}/api/v1/telegram/webhook"
}

output "remote_mcp_url" {
  description = "Public URL for remote MCP tool invocations"
  value       = "${google_cloud_run_v2_service.backend.uri}/api/v1/mcp/rpc"
}
