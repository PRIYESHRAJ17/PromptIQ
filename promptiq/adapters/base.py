"""Abstract base class for target environment compilers and adapters with capability awareness."""

from abc import ABC, abstractmethod
from typing import Any

from promptiq.schemas.package import OutputType
from promptiq.schemas.pps import PromptSpecSchema


class BaseTargetAdapter(ABC):
    """Compiles a vendor-neutral PPS intermediate representation into target-native instruction files."""

    target_name: str
    supported_output_types: list[OutputType] = ["prompt_only", "prompt_suite", "complete_package"]
    capabilities: dict[str, Any] = {
        "context_window": 128000,
        "supports_mcp": False,
        "supports_subagents": False,
        "supports_artifacts": False,
        "supports_rules_hierarchy": False,
        "supports_tool_calling": True,
        "max_output_tokens": 4096,
        "multimodal": False,
    }

    def validate_pps_capabilities(self, pps: PromptSpecSchema) -> list[str]:
        """Evaluates whether PPS requirements, tools, or rules exceed target host capabilities."""
        warnings: list[str] = []
        caps = getattr(self, "capabilities", {})

        reqs_str = " ".join(str(r.get("text", "")) for r in pps.requirements).lower()

        # Check MCP support
        if ("mcp" in reqs_str or "mcp server" in reqs_str) and not caps.get("supports_mcp", False):
            warnings.append(
                f"Capability Warning: Target '{self.target_name}' does not natively support MCP tool servers. "
                "MCP tools will compile to external script instructions."
            )

        # Check subagents support
        if ("subagent" in reqs_str or "multi-agent" in reqs_str) and not caps.get("supports_subagents", False):
            warnings.append(
                f"Capability Warning: Target '{self.target_name}' lacks autonomous subagent delegation. "
                "Multi-agent workflows will compile to sequential multi-turn instructions."
            )

        # Check rules hierarchy support
        if pps.behavior_rules and not caps.get("supports_rules_hierarchy", False):
            warnings.append(
                f"Capability Warning: Target '{self.target_name}' lacks hierarchical workspace rule files. "
                "Behavior rules are embedded inline in system prompt."
            )

        return warnings

    @abstractmethod
    def compile(self, pps: PromptSpecSchema, output_type: OutputType) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        """Compiles PPS into native artifacts.

        Returns:
            manifest: dict metadata describing the package.
            files: dict mapping relative file paths to their complete content.
            warnings: list of limitations or unsupported features.
        """
        pass
