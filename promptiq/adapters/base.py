"""Abstract base class for target environment compilers and adapters."""

from abc import ABC, abstractmethod
from typing import Any

from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class BaseTargetAdapter(ABC):
    """Compiles a vendor-neutral PPS intermediate representation into target-native instruction files."""

    target_name: str
    supported_output_types: list[OutputType] = ["prompt_only", "prompt_suite", "complete_package"]

    @abstractmethod
    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        """
        Compiles PPS into native artifacts.
        Returns:
            manifest: dict metadata describing the package.
            files: dict mapping relative file paths to their complete content.
            warnings: list of limitations or unsupported features.
        """
        pass
