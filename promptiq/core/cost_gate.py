"""Global Cloud Cost-Eligibility Gate and Financial Invariant Enforcer.

Enforces that no billable infrastructure, paid model route, or unconstrained cloud
resource can be provisioned or invoked automatically.
"""

from typing import Any

from promptiq.core.exceptions import PromptIQException


class InfrastructureCostViolationError(PromptIQException):
    """Raised when an infrastructure service violates the zero-spend invariant."""

    def __init__(self, resource_name: str, reason: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=f"Zero-Spend Infrastructure Invariant Violation: '{resource_name}' rejected. {reason}",
            error_code="ZERO_SPEND_INFRASTRUCTURE_VIOLATION",
            status_code=403,
            details=details or {},
        )


# Comprehensive audit ledger of candidate cloud infrastructure resources
INFRASTRUCTURE_AUDIT_LEDGER: dict[str, dict[str, Any]] = {
    "google_cloud_run": {
        "service": "Google Cloud Run (Compute)",
        "free_allowance": "2,000,000 requests/month; 360,000 vCPU-seconds; 180,000 GiB-seconds",
        "billing_account_required": True,  # Credit card on file required to enable Cloud Run API
        "auto_charges_overage": True,      # Automatically charges credit card if quota is exceeded
        "native_hard_stop_available": False,  # GCP budgets alert via email/PubSub, but do not shut down service natively
        "is_zero_spend_guaranteed": False, # Risk of unexpected billing on DDoS or traffic spikes
        "approved_for_auto_provisioning": False,
        "recommendation": "Operator deployment only with custom billing-kill Cloud Function or strict rate-limiting proxy.",
    },
    "google_artifact_registry": {
        "service": "Google Artifact Registry (Container Storage)",
        "free_allowance": "0.5 GB storage per month",
        "billing_account_required": True,
        "auto_charges_overage": True,      # $0.10/GB/month auto-billed
        "native_hard_stop_available": False,
        "is_zero_spend_guaranteed": False,
        "approved_for_auto_provisioning": False,
        "recommendation": "Use external free registries (GitHub Container Registry ghcr.io free tier) or enforce image pruning.",
    },
    "google_secret_manager": {
        "service": "Google Cloud Secret Manager",
        "free_allowance": "6 active secret versions; 10,000 access operations/month",
        "billing_account_required": True,
        "auto_charges_overage": True,      # $0.06 per 10,000 operations
        "native_hard_stop_available": False,
        "is_zero_spend_guaranteed": False,
        "approved_for_auto_provisioning": False,
        "recommendation": "Inject secrets via environment variables at container startup or use free KeyVault.",
    },
    "neon_postgres": {
        "service": "Neon Serverless PostgreSQL",
        "free_allowance": "0.5 GiB storage; 1 compute branch; 190 compute hours/month (auto-suspends after 5m idle)",
        "billing_account_required": False, # Free signup without credit card
        "auto_charges_overage": False,     # Refuses connections / read-only mode upon quota exhaustion
        "native_hard_stop_available": True, # Hard stops without charging money
        "is_zero_spend_guaranteed": True,  # 100% free with strict zero-cost boundary
        "approved_for_auto_provisioning": True,
        "recommendation": "Approved primary zero-cost persistent relational database.",
    },
    "render_web_service": {
        "service": "Render Free Web Service",
        "free_allowance": "750 hours/month shared across free web services; spins down on 15m idle",
        "billing_account_required": False,
        "auto_charges_overage": False,     # Free tier services suspend when hours expire; no auto-charge
        "native_hard_stop_available": True,
        "is_zero_spend_guaranteed": True,
        "approved_for_auto_provisioning": True,
        "recommendation": "Approved zero-cost container hosting alternative.",
    },
    "render_postgres": {
        "service": "Render Free PostgreSQL",
        "free_allowance": "1 GB storage; expires 30 days after creation",
        "billing_account_required": False,
        "auto_charges_overage": False,
        "native_hard_stop_available": True,
        "is_zero_spend_guaranteed": False, # Ephemeral: 30-day deletion violates persistent memory requirement
        "approved_for_auto_provisioning": False,
        "recommendation": "Disapproved due to 30-day expiration window. Use Neon Serverless Postgres instead.",
    },
    "cloudflare_workers": {
        "service": "Cloudflare Workers / Pages",
        "free_allowance": "100,000 requests/day; 10ms CPU/request",
        "billing_account_required": False,
        "auto_charges_overage": False,     # Returns HTTP 1027 error when daily limit reached; never charges
        "native_hard_stop_available": True,
        "is_zero_spend_guaranteed": True,
        "approved_for_auto_provisioning": True,
        "recommendation": "Approved zero-cost edge proxy / rate-limiter.",
    },
}


class CostEligibilityGate:
    """Enforces zero-spend infrastructure rules at runtime and deployment."""

    @staticmethod
    def audit_resource(resource_key: str) -> dict[str, Any]:
        """Audits a specific infrastructure component against zero-spend rules."""
        info = INFRASTRUCTURE_AUDIT_LEDGER.get(resource_key.lower())
        if not info:
            raise InfrastructureCostViolationError(
                resource_name=resource_key,
                reason="Unrecognized infrastructure resource. Cannot verify zero-spend guarantee.",
            )
        return info

    @staticmethod
    def verify_resource_provisioning(resource_key: str) -> None:
        """Verifies that an infrastructure resource has a genuine hard stop and cannot incur auto-charges."""
        info = CostEligibilityGate.audit_resource(resource_key)
        if not info.get("approved_for_auto_provisioning", False):
            raise InfrastructureCostViolationError(
                resource_name=resource_key,
                reason=(
                    f"Resource requires billing account or lacks automatic spending freeze "
                    f"({info['free_allowance']}). Native hard stop: {info['native_hard_stop_available']}. "
                    f"Recommendation: {info['recommendation']}"
                ),
                details=info,
            )

    @staticmethod
    def get_full_cost_audit_report() -> dict[str, Any]:
        """Generates a complete financial risk and eligibility report for all infrastructure components."""
        approved = []
        rejected = []
        for key, details in INFRASTRUCTURE_AUDIT_LEDGER.items():
            if details["approved_for_auto_provisioning"]:
                approved.append(key)
            else:
                rejected.append(key)
        return {
            "policy": "PromptIQ Hard Zero-Spend Infrastructure Invariant ($0.00)",
            "approved_zero_cost_resources": approved,
            "rejected_or_operator_only_resources": rejected,
            "audit_ledger": INFRASTRUCTURE_AUDIT_LEDGER,
        }
