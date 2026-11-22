"""Built-in real and sandboxed tools for PromptIQ agent execution."""

import re
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

import httpx

from promptiq.core.logging import logger
from promptiq.core.security import SecurityError, validate_and_sanitize_url
from promptiq.tools.registry import (
    PermissionLevel,
    RiskTier,
    ToolDefinition,
    ToolExecutionMode,
    tool_registry,
)


# ---------------------------------------------------------------------------
# 1. Filesystem Read Tool
# ---------------------------------------------------------------------------
def _filesystem_read_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    file_path_str = inputs.get("file_path")
    if not file_path_str:
        raise ValueError("Parameter 'file_path' is required")

    path = Path(file_path_str).resolve()
    # Path traversal protection: ensure inside workspace or cwd
    allowed_root = Path.cwd().resolve()
    if context and "allowed_root" in context:
        allowed_root = Path(context["allowed_root"]).resolve()

    try:
        path.relative_to(allowed_root)
    except ValueError:
        raise PermissionError(
            f"Access to path '{file_path_str}' is outside permitted workspace root"
        )

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path_str}")
    if not path.is_file():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path_str}")

    max_bytes = inputs.get("max_bytes", 500_000)
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read(max_bytes)

    return {
        "file_path": str(path),
        "content": content,
        "size_bytes": path.stat().st_size,
        "truncated": path.stat().st_size > max_bytes,
    }


FILESYSTEM_READ_TOOL = ToolDefinition(
    tool_id="filesystem_read",
    name="Filesystem Read",
    description="Reads file contents from within the authorized workspace with strict path traversal checks.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 500000},
        },
        "required": ["file_path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "content": {"type": "string"},
            "size_bytes": {"type": "integer"},
            "truncated": {"type": "boolean"},
        },
    },
    permission_level=PermissionLevel.READ_ONLY,
    risk_tier=RiskTier.LOW,
    timeout_seconds=5.0,
    execution_mode=ToolExecutionMode.REAL,
)


# ---------------------------------------------------------------------------
# 2. Filesystem Write Tool
# ---------------------------------------------------------------------------
def _filesystem_write_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    file_path_str = inputs.get("file_path")
    content = inputs.get("content", "")
    if not file_path_str:
        raise ValueError("Parameter 'file_path' is required")

    path = Path(file_path_str).resolve()
    allowed_root = Path.cwd().resolve()
    if context and "allowed_root" in context:
        allowed_root = Path(context["allowed_root"]).resolve()

    try:
        path.relative_to(allowed_root)
    except ValueError:
        raise PermissionError(f"Path traversal blocked: '{file_path_str}' is outside allowed root")

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "file_path": str(path),
        "bytes_written": len(content.encode("utf-8")),
        "created": True,
    }


FILESYSTEM_WRITE_TOOL = ToolDefinition(
    tool_id="filesystem_write",
    name="Filesystem Write",
    description="Writes text or code artifacts to an authorized workspace path with path traversal protection.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["file_path", "content"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "bytes_written": {"type": "integer"},
            "created": {"type": "boolean"},
        },
    },
    permission_level=PermissionLevel.REVERSIBLE_MODIFICATION,
    risk_tier=RiskTier.MEDIUM,
    timeout_seconds=5.0,
    execution_mode=ToolExecutionMode.REAL,
)


# ---------------------------------------------------------------------------
# 3. Subprocess Execution Tool
# ---------------------------------------------------------------------------
ALLOWED_BINARIES = {"git", "python", "pytest", "pip", "ruff", "bandit"}


def _subprocess_exec_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    command_args = inputs.get("command_args")
    if not command_args or not isinstance(command_args, list):
        raise ValueError("Parameter 'command_args' must be a non-empty list of command arguments")

    binary = command_args[0].lower()
    # Normalize Windows .exe or path
    binary_name = Path(binary).name.lower().replace(".exe", "")
    if binary_name not in ALLOWED_BINARIES:
        raise PermissionError(
            f"Execution of binary '{binary}' is prohibited. Allowed: {sorted(ALLOWED_BINARIES)}"
        )

    timeout = float(inputs.get("timeout_seconds", 10.0))
    cwd = context.get("cwd") if context else str(Path.cwd())

    proc = subprocess.run(  # nosec B603
        command_args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "success": proc.returncode == 0,
    }


SUBPROCESS_EXEC_TOOL = ToolDefinition(
    tool_id="subprocess_exec",
    name="Subprocess Execution",
    description="Executes whitelisted local CLI commands (git, python, pytest, etc.) with timeout bounds.",
    input_schema={
        "type": "object",
        "properties": {
            "command_args": {"type": "array", "items": {"type": "string"}},
            "timeout_seconds": {"type": "number", "default": 10.0},
        },
        "required": ["command_args"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "exit_code": {"type": "integer"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "success": {"type": "boolean"},
        },
    },
    permission_level=PermissionLevel.REVERSIBLE_MODIFICATION,
    risk_tier=RiskTier.HIGH,
    timeout_seconds=15.0,
    execution_mode=ToolExecutionMode.REAL,
)


# ---------------------------------------------------------------------------
# 4. Git Inspection Tool
# ---------------------------------------------------------------------------
def _git_inspect_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    subcommand = inputs.get("subcommand", "status")
    allowed_subcommands = {"status", "log", "diff", "branch", "rev-parse"}
    if subcommand not in allowed_subcommands:
        raise ValueError(
            f"Subcommand '{subcommand}' not allowed. Permitted: {sorted(allowed_subcommands)}"
        )

    args = ["git", subcommand]
    if subcommand == "log":
        args.extend(["-n", str(inputs.get("limit", 5)), "--oneline"])
    elif subcommand == "diff" and inputs.get("staged"):
        args.append("--staged")

    proc = subprocess.run(  # nosec B603
        args,
        capture_output=True,
        text=True,
        timeout=5.0,
        check=False,
    )

    return {
        "subcommand": subcommand,
        "exit_code": proc.returncode,
        "output": proc.stdout if proc.returncode == 0 else proc.stderr,
        "success": proc.returncode == 0,
    }


GIT_INSPECT_TOOL = ToolDefinition(
    tool_id="git_inspect",
    name="Git Repository Inspection",
    description="Inspects local Git repository state (status, log, diff, branch).",
    input_schema={
        "type": "object",
        "properties": {
            "subcommand": {
                "type": "string",
                "enum": ["status", "log", "diff", "branch", "rev-parse"],
            },
            "limit": {"type": "integer", "default": 5},
            "staged": {"type": "boolean", "default": False},
        },
    },
    output_schema={
        "type": "object",
        "properties": {
            "subcommand": {"type": "string"},
            "exit_code": {"type": "integer"},
            "output": {"type": "string"},
            "success": {"type": "boolean"},
        },
    },
    permission_level=PermissionLevel.READ_ONLY,
    risk_tier=RiskTier.LOW,
    timeout_seconds=5.0,
    execution_mode=ToolExecutionMode.REAL,
)


# ---------------------------------------------------------------------------
# 5. Data Transformation Tool
# ---------------------------------------------------------------------------
def _data_transform_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    records = inputs.get("data", [])
    if not isinstance(records, list):
        raise ValueError("Input 'data' must be a list of records")

    operation = inputs.get("operation", "summary")
    field = inputs.get("field")

    if operation == "count":
        return {"operation": "count", "count": len(records)}

    if operation == "filter":
        match_value = inputs.get("value")
        filtered = [r for r in records if isinstance(r, dict) and r.get(field) == match_value]
        return {"operation": "filter", "field": field, "count": len(filtered), "results": filtered}

    if operation == "summary":
        values = [
            r.get(field)
            for r in records
            if isinstance(r, dict) and isinstance(r.get(field), (int, float))
        ]
        if not values:
            return {
                "operation": "summary",
                "field": field,
                "count": 0,
                "mean": 0.0,
                "min": None,
                "max": None,
            }
        return {
            "operation": "summary",
            "field": field,
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
        }

    raise ValueError(f"Unsupported operation '{operation}'. Use 'count', 'filter', or 'summary'")


DATA_TRANSFORM_TOOL = ToolDefinition(
    tool_id="data_transform",
    name="Data Transformation & Analysis",
    description="Performs deterministic filtering, counting, and aggregation summaries over structured datasets.",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array", "items": {"type": "object"}},
            "operation": {"type": "string", "enum": ["count", "filter", "summary"]},
            "field": {"type": "string"},
            "value": {},
        },
        "required": ["data", "operation"],
    },
    output_schema={"type": "object"},
    permission_level=PermissionLevel.READ_ONLY,
    risk_tier=RiskTier.LOW,
    timeout_seconds=5.0,
    execution_mode=ToolExecutionMode.REAL,
)


# ---------------------------------------------------------------------------
# 6. HTTP Fetch Tool (SSRF Safe)
# ---------------------------------------------------------------------------
async def _http_fetch_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    url = inputs.get("url")
    if not url:
        raise ValueError("Parameter 'url' is required")

    # Strict SSRF enforcement
    try:
        validated_url = validate_and_sanitize_url(url)
    except SecurityError as err:
        raise PermissionError(f"SSRF policy blocked request to target URL '{url}': {err}")

    timeout = float(inputs.get("timeout_seconds", 5.0))
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        resp = await client.get(validated_url)
        return {
            "url": url,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text[:50000],
            "truncated": len(resp.text) > 50000,
        }


HTTP_FETCH_TOOL = ToolDefinition(
    tool_id="http_fetch",
    name="SSRF-Safe HTTP Client",
    description="Fetches external web resources with strict 31-vector SSRF blocking.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "timeout_seconds": {"type": "number", "default": 5.0},
        },
        "required": ["url"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "status_code": {"type": "integer"},
            "body": {"type": "string"},
        },
    },
    permission_level=PermissionLevel.EXTERNAL_COMMUNICATION,
    risk_tier=RiskTier.MEDIUM,
    timeout_seconds=10.0,
    execution_mode=ToolExecutionMode.REAL,
)


# ---------------------------------------------------------------------------
# 7. Validator Execution Tool
# ---------------------------------------------------------------------------
def _validator_exec_handler(
    inputs: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    content = inputs.get("content", "")
    assertions = inputs.get("assertions", [])
    results: list[dict[str, Any]] = []

    passed_count = 0
    for assertion in assertions:
        a_type = assertion.get("type", "contains")
        target = assertion.get("target", "")
        negate = assertion.get("negate", False)

        passed = False
        if a_type == "contains":
            passed = target in content
        elif a_type == "regex":
            passed = bool(re.search(target, content))
        elif a_type == "length_min":
            passed = len(content) >= int(target)
        elif a_type == "length_max":
            passed = len(content) <= int(target)

        if negate:
            passed = not passed

        if passed:
            passed_count += 1

        results.append(
            {
                "assertion": assertion,
                "passed": passed,
                "reason": "OK"
                if passed
                else f"Assertion failed: {a_type} {target} (negate={negate})",
            }
        )

    all_passed = passed_count == len(assertions)
    return {
        "total_assertions": len(assertions),
        "passed_count": passed_count,
        "failed_count": len(assertions) - passed_count,
        "all_passed": all_passed,
        "results": results,
    }


VALIDATOR_EXEC_TOOL = ToolDefinition(
    tool_id="validator_exec",
    name="Assertion & Schema Validator",
    description="Runs deterministic regex, length, and containment checks against deliverables.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "assertions": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["content", "assertions"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "total_assertions": {"type": "integer"},
            "passed_count": {"type": "integer"},
            "all_passed": {"type": "boolean"},
        },
    },
    permission_level=PermissionLevel.READ_ONLY,
    risk_tier=RiskTier.LOW,
    timeout_seconds=3.0,
    execution_mode=ToolExecutionMode.REAL,
)


def register_builtin_tools():
    """Registers all standard built-in tools into the global tool registry."""
    tool_registry.register_tool(FILESYSTEM_READ_TOOL, _filesystem_read_handler)
    tool_registry.register_tool(FILESYSTEM_WRITE_TOOL, _filesystem_write_handler)
    tool_registry.register_tool(SUBPROCESS_EXEC_TOOL, _subprocess_exec_handler)
    tool_registry.register_tool(GIT_INSPECT_TOOL, _git_inspect_handler)
    tool_registry.register_tool(DATA_TRANSFORM_TOOL, _data_transform_handler)
    tool_registry.register_tool(HTTP_FETCH_TOOL, _http_fetch_handler)
    tool_registry.register_tool(VALIDATOR_EXEC_TOOL, _validator_exec_handler)
    logger.info("Registered all 7 built-in agent execution tools into ToolRegistry")


# Auto-register on import
register_builtin_tools()
