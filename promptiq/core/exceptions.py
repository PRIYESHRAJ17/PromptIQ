"""Domain-specific exceptions for PromptIQ."""

from typing import Any


class PromptIQException(Exception):
    """Base exception for all PromptIQ errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "PROMPTIQ_ERROR",
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code


class AuthenticationError(PromptIQException):
    def __init__(
        self,
        message: str = "Invalid credentials or expired session",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message, error_code="AUTHENTICATION_FAILED", details=details, status_code=401
        )


class TenantIsolationError(PromptIQException):
    def __init__(
        self,
        message: str = "Access denied: resource belongs to another workspace",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="TENANT_ISOLATION_VIOLATION",
            details=details,
            status_code=403,
        )


class NotFoundError(PromptIQException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with ID '{resource_id}' was not found",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "id": resource_id},
            status_code=404,
        )


class ZeroPriceViolationError(PromptIQException):
    """Raised when an operation attempts to invoke a paid route or billable provider."""

    def __init__(self, provider: str, model_id: str, reason: str = "Non-zero pricing detected"):
        super().__init__(
            message=f"Zero-Price Invariant Violation: Route '{provider}/{model_id}' is rejected ({reason}). PromptIQ strictly prohibits paid inference.",
            error_code="ZERO_PRICE_VIOLATION",
            details={"provider": provider, "model_id": model_id, "reason": reason},
            status_code=400,
        )


class BYOKViolationError(PromptIQException):
    """Raised when user-supplied API keys are detected."""

    def __init__(
        self,
        message: str = "User API keys (BYOK) are strictly prohibited. PromptIQ provides centrally managed zero-price inference.",
    ):
        super().__init__(
            message=message,
            error_code="BYOK_PROHIBITED",
            status_code=400,
        )


class CapacityExhaustedError(PromptIQException):
    """Raised when rate limits or quotas are hit."""

    def __init__(self, message: str, retry_after: int = 60, details: dict[str, Any] | None = None):
        merged_details = details or {}
        merged_details["retry_after_seconds"] = retry_after
        super().__init__(
            message=message,
            error_code="CAPACITY_EXHAUSTED",
            details=merged_details,
            status_code=429,
        )
        self.retry_after = retry_after


class ConstitutionApprovalRequiredError(PromptIQException):
    """Raised when attempting to compile an unapproved Project Constitution."""

    def __init__(
        self,
        message: str = "Project Constitution must be reviewed and approved by user before compilation.",
    ):
        super().__init__(
            message=message,
            error_code="CONSTITUTION_APPROVAL_REQUIRED",
            status_code=422,
        )


class TargetIncompatibilityError(PromptIQException):
    """Raised when target environment does not support requested capabilities."""

    def __init__(self, target: str, missing_capabilities: list[str]):
        super().__init__(
            message=f"Target '{target}' does not support required capabilities: {', '.join(missing_capabilities)}",
            error_code="TARGET_INCOMPATIBILITY",
            details={"target": target, "missing_capabilities": missing_capabilities},
            status_code=422,
        )


class VersionConflictError(PromptIQException):
    """Raised when a concurrent edit or version mismatch occurs."""

    def __init__(self, expected_version: int, actual_version: int):
        super().__init__(
            message=f"Version conflict: Expected version {expected_version}, but found {actual_version}. Please refresh.",
            error_code="VERSION_CONFLICT",
            details={"expected_version": expected_version, "actual_version": actual_version},
            status_code=409,
        )


class ConflictError(VersionConflictError):
    pass


class PrivacyPolicyViolationError(PromptIQException):
    """Raised when data sensitivity exceeds provider's allowed privacy tier."""

    def __init__(self, provider: str, model_id: str, sensitivity: str, reason: str):
        super().__init__(
            message=f"Privacy Policy Violation: Data sensitivity '{sensitivity}' cannot be routed to '{provider}/{model_id}'. Reason: {reason}",
            error_code="PRIVACY_POLICY_VIOLATION",
            details={
                "provider": provider,
                "model_id": model_id,
                "sensitivity": sensitivity,
                "reason": reason,
            },
            status_code=403,
        )


class SecurityError(PromptIQException):
    """Raised when an operation violates security policy, SSRF boundaries, or input safety."""

    def __init__(
        self,
        message: str = "Security policy violation detected",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="SECURITY_VIOLATION",
            details=details,
            status_code=403,
        )


class ValidationError(PromptIQException):
    """Raised when input parameters, payloads, or contracts fail validation."""

    def __init__(
        self,
        message: str = "Request validation failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=422,
        )


class WorkflowError(PromptIQException):
    """Raised when a background workflow or orchestration job encounters a fatal error."""

    def __init__(
        self,
        message: str = "Workflow execution failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            details=details,
            status_code=500,
        )


class ProviderError(PromptIQException):
    """Raised when an upstream AI model provider fails or returns unparseable outputs."""

    def __init__(
        self,
        provider: str,
        message: str = "Upstream provider error",
        details: dict[str, Any] | None = None,
    ):
        merged = details or {}
        merged["provider"] = provider
        super().__init__(
            message=message,
            error_code="PROVIDER_ERROR",
            details=merged,
            status_code=502,
        )
