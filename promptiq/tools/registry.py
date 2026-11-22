"""PromptIQ Autonomous Tool Registry, Permissions, and Execution Layer."""

import asyncio
import inspect
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from promptiq.core.logging import logger


class PermissionLevel(StrEnum):
    READ_ONLY = "read_only"
    REVERSIBLE_MODIFICATION = "reversible_modification"
    EXTERNAL_COMMUNICATION = "external_communication"
    IRREVERSIBLE_MODIFICATION = "irreversible_modification"
    DESTRUCTIVE = "destructive"


# Permission hierarchy rank (higher rank means higher authority)
PERMISSION_HIERARCHY: dict[PermissionLevel, int] = {
    PermissionLevel.READ_ONLY: 1,
    PermissionLevel.REVERSIBLE_MODIFICATION: 2,
    PermissionLevel.EXTERNAL_COMMUNICATION: 3,
    PermissionLevel.IRREVERSIBLE_MODIFICATION: 4,
    PermissionLevel.DESTRUCTIVE: 5,
}


class RiskTier(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolExecutionMode(StrEnum):
    REAL = "real"
    SANDBOXED = "sandboxed"
    SIMULATED = "simulated"
    MOCKED = "mocked"


class ToolDefinition(BaseModel):
    tool_id: str
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.READ_ONLY
    risk_tier: RiskTier = RiskTier.LOW
    timeout_seconds: float = 10.0
    retry_policy: dict[str, Any] = Field(
        default_factory=lambda: {"max_retries": 1, "backoff_seconds": 0.5}
    )
    idempotent: bool = True
    execution_mode: ToolExecutionMode = ToolExecutionMode.REAL


class ToolCallResult(BaseModel):
    tool_id: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    provenance: ToolExecutionMode = ToolExecutionMode.REAL
    state_delta: dict[str, Any] | None = None


class ToolRegistry:
    """Central registry and permission enforcement gateway for agent tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}

    def register_tool(
        self,
        tool_def: ToolDefinition,
        handler: Callable,
    ) -> None:
        """Registers a tool definition and its execution handler."""
        self._tools[tool_def.tool_id] = tool_def
        self._handlers[tool_def.tool_id] = handler
        logger.info(
            f"Registered tool '{tool_def.tool_id}' with permission '{tool_def.permission_level.value}'"
        )

    def get_tool(self, tool_id: str) -> ToolDefinition | None:
        """Retrieves tool definition by ID."""
        return self._tools.get(tool_id)

    def list_tools(
        self,
        permission_filter: PermissionLevel | None = None,
    ) -> list[ToolDefinition]:
        """Lists registered tools, optionally filtered by permission."""
        if not permission_filter:
            return list(self._tools.values())
        max_rank = PERMISSION_HIERARCHY.get(permission_filter, 1)
        return [
            t
            for t in self._tools.values()
            if PERMISSION_HIERARCHY.get(t.permission_level, 1) <= max_rank
        ]

    def check_permission(
        self,
        tool: ToolDefinition,
        granted_permissions: list[PermissionLevel],
    ) -> tuple[bool, str | None]:
        """Verifies if the granted permissions are sufficient for the tool."""
        req_rank = PERMISSION_HIERARCHY.get(tool.permission_level, 5)
        highest_granted_rank = max(
            [PERMISSION_HIERARCHY.get(p, 0) for p in granted_permissions] or [0]
        )

        if highest_granted_rank < req_rank:
            return (
                False,
                f"Permission denied: Tool '{tool.tool_id}' requires '{tool.permission_level.value}', but caller only possesses {[p.value for p in granted_permissions]}",
            )
        return True, None

    async def execute_tool(
        self,
        tool_id: str,
        inputs: dict[str, Any],
        caller_permissions: list[PermissionLevel],
        context: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        """Executes a tool with strict permission checks, timeout, and result provenance."""
        start_time = time.perf_counter()
        tool = self._tools.get(tool_id)
        if not tool:
            return ToolCallResult(
                tool_id=tool_id,
                success=False,
                error=f"Tool '{tool_id}' is not registered in ToolRegistry",
                duration_ms=0.0,
                provenance=ToolExecutionMode.REAL,
            )

        handler = self._handlers.get(tool_id)
        if not handler:
            return ToolCallResult(
                tool_id=tool_id,
                success=False,
                error=f"No execution handler registered for tool '{tool_id}'",
                duration_ms=0.0,
                provenance=tool.execution_mode,
            )

        # 1. Enforce permission boundary
        allowed, reason = self.check_permission(tool, caller_permissions)
        if not allowed:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"Tool execution blocked: {reason}")
            return ToolCallResult(
                tool_id=tool_id,
                success=False,
                error=reason,
                duration_ms=round(duration_ms, 2),
                provenance=tool.execution_mode,
            )

        # 2. Execute handler with timeout and error handling
        try:
            if inspect.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(inputs, context=context),
                    timeout=tool.timeout_seconds,
                )
            else:
                # Synchronous handler wrapped in timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(handler, inputs, context=context),
                    timeout=tool.timeout_seconds,
                )

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_id=tool_id,
                success=True,
                output=result,
                duration_ms=round(duration_ms, 2),
                provenance=tool.execution_mode,
            )

        except TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Tool '{tool_id}' timed out after {tool.timeout_seconds}s")
            return ToolCallResult(
                tool_id=tool_id,
                success=False,
                error=f"Execution timed out after {tool.timeout_seconds} seconds",
                duration_ms=round(duration_ms, 2),
                provenance=tool.execution_mode,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception(f"Tool '{tool_id}' failed with exception: {exc}")
            return ToolCallResult(
                tool_id=tool_id,
                success=False,
                error=str(exc),
                duration_ms=round(duration_ms, 2),
                provenance=tool.execution_mode,
            )


# Global singleton tool registry
tool_registry = ToolRegistry()
