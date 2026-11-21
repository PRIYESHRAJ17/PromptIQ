"""Abstract base class for inference adapters."""

from abc import ABC, abstractmethod

from promptiq.gateway.models import InferenceRequest, InferenceResponse


class BaseInferenceAdapter(ABC):
    """Abstract interface for all model execution adapters."""

    provider_name: str
    model_id: str

    @abstractmethod
    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Executes inference for the given request and returns a structured response."""
        pass
