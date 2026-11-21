"""Environment Registry service defining host capabilities and manifest rules."""

from typing import Any

from promptiq.schemas.registry import EnvironmentRecordSchema

CURATED_ENVIRONMENTS: list[dict[str, Any]] = [
    {
        "id": "google-antigravity",
        "host": "google-antigravity",
        "surface": "agent",
        "supported_formats": ["plugin.json", "skills", "rules", "agents", "hooks"],
        "manifest_schema": {"required_keys": ["name", "version", "description", "skills", "rules"]},
        "supported_tools": ["run_command", "read_file", "write_file", "edit_file", "call_mcp_tool"],
        "precedence_rules": ["system_instructions", "workspace_rules", "skill_instructions"],
        "verification_status": "tested",
    },
    {
        "id": "claude-code",
        "host": "claude-code",
        "surface": "cli",
        "supported_formats": ["CLAUDE.md", ".claude/settings.json", ".claude/rules"],
        "manifest_schema": {"root_file": "CLAUDE.md"},
        "supported_tools": ["Bash", "FileEdit", "GlobTool", "GrepTool"],
        "precedence_rules": ["CLAUDE.md", "scoped_rules"],
        "verification_status": "tested",
    },
    {
        "id": "cursor",
        "host": "cursor",
        "surface": "ide",
        "supported_formats": [".cursorrules", ".cursor/rules/*.mdc", ".cursor/mcp.json"],
        "manifest_schema": {"root_file": ".cursorrules"},
        "supported_tools": ["terminal", "editor", "mcp"],
        "precedence_rules": [".cursorrules", "mdc_rules"],
        "verification_status": "tested",
    },
    {
        "id": "openai-codex",
        "host": "openai-codex",
        "surface": "agent",
        "supported_formats": ["ai-plugin.json", "openapi.yaml", "skills"],
        "manifest_schema": {"required_keys": ["schema_version", "name_for_model", "description_for_model"]},
        "supported_tools": ["mcp", "openapi_endpoints"],
        "precedence_rules": ["manifest", "skill_instructions"],
        "verification_status": "tested",
    },
    {
        "id": "gemini-cli",
        "host": "gemini-cli",
        "surface": "cli",
        "supported_formats": ["gemini-extension.json", "context", "commands"],
        "manifest_schema": {"required_keys": ["name", "version", "context_files"]},
        "supported_tools": ["shell", "context_provider"],
        "precedence_rules": ["extension_context", "user_prompt"],
        "verification_status": "tested",
    },
]


class EnvironmentRegistryService:
    """Manages target execution host rules and supported format specifications."""

    @staticmethod
    def list_environments() -> list[EnvironmentRecordSchema]:
        return [EnvironmentRecordSchema(**env) for env in CURATED_ENVIRONMENTS]

    @staticmethod
    def get_environment(host: str) -> EnvironmentRecordSchema | None:
        for env in CURATED_ENVIRONMENTS:
            if env["host"] == host or env["id"] == host:
                return EnvironmentRecordSchema(**env)
        return None
