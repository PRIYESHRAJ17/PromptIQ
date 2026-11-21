# PromptIQ Integration & Target Compatibility Matrix

## 1. Integration Support Tiers

| Tier | Classification | Description | Delivery Format | Support Claim |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Native Plugin** | Host-specific packaged bundle adhering to official marketplace/extension specs. | Zip/tar bundle or directory structure matching host manifest. | Native only for tested host version. |
| **Tier 2** | **MCP Tools** | Remote or local Model Context Protocol (MCP) server integration. | JSON-RPC standard tools, resources, and prompt endpoints. | MCP-compatible. |
| **Tier 3** | **Portable Package** | Common portable layout containing skills, rules, and markdown instructions. | `plugin.json`, `skills/`, `rules/`, `README.md`. | Portable layout. |
| **Tier 4** | **CLI & SDK** | Programmatic access via terminal commands or Python SDK. | `promptiq` CLI and `promptiq-sdk` library. | Documented CLI/API. |
| **Tier 5** | **Manual Export** | Copy-ready prompt text, instruction files, and configuration snippets. | Markdown files and JSON configuration blocks. | Export-compatible. |

---

## 2. Target Environment Specifications

### 2.1 Google Antigravity
- **Target ID**: `google-antigravity`
- **Support Tier**: Tier 1 (Native Plugin) + Tier 2 (MCP)
- **Manifest File**: `antigravity.json` / `plugin.json`
- **Native Package Structure**:
  ```
  promptiq-antigravity/
    ├── plugin.json               # Plugin metadata, permissions, tools
    ├── skills/                   # Structured SKILL.md task workflows
    ├── agents/                   # Subagent role definitions
    ├── rules/                    # Persistent workspace instruction rules
    ├── hooks/                    # Agent lifecycle hooks
    └── README.md                 # Setup and documentation
  ```
- **Context Loading Behavior**: System prompt rules loaded at session start; skills dynamically activated upon user intent match.
- **Verification Status**: `SUPPORTED / TESTED`

### 2.2 Claude Code
- **Target ID**: `claude-code`
- **Support Tier**: Tier 1 (Native Instructions) + Tier 2 (MCP)
- **Manifest File**: `CLAUDE.md` + `.claude/`
- **Native Package Structure**:
  ```
  promptiq-claude/
    ├── CLAUDE.md                 # Root execution rules, project context, commands
    ├── .claude/
    │   ├── settings.json         # Tool permissions and approval policies
    │   └── rules/                # Scoped subsystem rules
    └── README.md
  ```
- **Context Loading Behavior**: Reads `CLAUDE.md` from root directory on startup; respects sub-directory scoped rules.
- **Verification Status**: `SUPPORTED / TESTED`

### 2.3 OpenAI Codex / ChatGPT Ecosystem
- **Target ID**: `openai-codex`
- **Support Tier**: Tier 1 (Portable Plugin) + Tier 2 (MCP)
- **Manifest File**: `ai-plugin.json` / `plugin.json`
- **Native Package Structure**:
  ```
  promptiq-codex/
    ├── .well-known/ai-plugin.json  # Manifest, auth specification, API definition
    ├── openapi.yaml               # OpenAPI contract for tool calling
    ├── skills/                    # Packaged skills
    └── README.md
  ```
- **Verification Status**: `SUPPORTED / TESTED`

### 2.4 Cursor
- **Target ID**: `cursor`
- **Support Tier**: Tier 1 (Rules & Tools) + Tier 2 (MCP)
- **Manifest File**: `.cursorrules` + `.cursor/`
- **Native Package Structure**:
  ```
  promptiq-cursor/
    ├── .cursorrules               # Legacy and primary rule instruction file
    ├── .cursor/
    │   ├── rules/                # Granular, file-pattern matched rules (.mdc)
    │   └── mcp.json              # MCP server connection definitions
    └── README.md
  ```
- **Verification Status**: `SUPPORTED / TESTED`

### 2.5 Gemini CLI
- **Target ID**: `gemini-cli`
- **Support Tier**: Tier 1 (Extension) + Tier 2 (MCP)
- **Manifest File**: `gemini-extension.json`
- **Native Package Structure**:
  ```
  promptiq-gemini-cli/
    ├── gemini-extension.json     # Extension manifest
    ├── context/                  # Custom context and system instruction files
    ├── commands/                 # User-facing CLI subcommands
    └── README.md
  ```
- **Verification Status**: `SUPPORTED / TESTED`
