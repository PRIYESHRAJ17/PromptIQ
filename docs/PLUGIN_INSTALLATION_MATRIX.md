# PROMPTIQ PLUGIN INSTALLATION & COMPATIBILITY MATRIX
## Multi-Surface AI Agent Integration Matrix

---

## 1. Overview

PromptIQ provides native installable integration packages and an RFC-compliant Model Context Protocol (MCP) server across 6 leading agentic environments. All 6 packages share a single authoritative backend, continuous project memory, and zero-price enforcement.

---

## 2. Integration Matrix

| Agent Platform | Integration Type | Install Command / Action | Configuration File | Supported Capabilities |
|---|---|---|---|---|
| **Google Antigravity** | Native Plugin Package | `agy plugin install promptiq` (or unpack in `.gemini/plugins/`) | `manifest.json`, `rules/promptiq.md`, `skills/promptiq/SKILL.md` | Persistent Memory Sync, 21-Category Autopsy, 10 Task Families, Exact Offset Evidence, STDIO MCP |
| **Claude Code** | Native CLI Plugin | `claude plugin install promptiq-claude-code` | `.claude-plugin/plugin.json`, `skills/promptiq/SKILL.md` | Interactive slash commands (`/autopsy`, `/constitution`, `/compile`), Anthropic JSON Schema tool validation |
| **Cursor IDE** | Workspace Rules & MCP | Unpack into workspace root; add command to Cursor MCP settings | `.cursorrules`, `mcp.json` | Persistent instruction rules, context injection, code autopsy, atomic constitution diffs |
| **OpenAI Codex** | CLI & Spec Package | `npm install -g @promptiq/codex-plugin` | `plugin.json`, `codex.json`, `skills/promptiq/SKILL.md` | Instruction manifests, task archetypes, zero-price gateway routing, deterministic assertions |
| **Google Gemini CLI** | Extension Package | `gemini extension add promptiq` | `gemini-extension.json`, `GEMINI.md`, `skills/promptiq/SKILL.md` | Persistent rules directive, live constitution query, multi-pass consistency scoring |
| **Universal MCP Server** | Model Context Protocol | `python -m promptiq.mcp.server` or `npx -y @promptiq/mcp-server` | `mcp.json`, `tools.json` | 7 authoritative PromptIQ tools, RFC-compliant JSON Schemas, STDIO & SSE transports |

---

## 3. Package Distribution URLs & Checksums

| Package Name | Distributable ZIP | Size | SHA-256 Checksum |
|---|---|---|---|
| Google Antigravity | `dist/plugins/promptiq-antigravity.zip` | 3,104 bytes | `a123d2c66756ceda770a3449622fb350ee1c3f286dc82a1e6b188096736ee4a6` |
| Claude Code | `dist/plugins/promptiq-claude-code.zip` | 1,563 bytes | `591eb030402a9ae71fe85633a9e07a53b381997146d6e61b29dc4a731ee242d9` |
| Cursor IDE | `dist/plugins/promptiq-cursor.zip` | 1,711 bytes | `996f01967dedc7935c2d6f42bac1d22d2ba4c1142ada758c06f0ad528798cc05` |
| OpenAI Codex | `dist/plugins/promptiq-codex.zip` | 1,392 bytes | `a95b381d8c9e5ad819ff1fb319e838c73d0d8a8798ba444bd289f5948cf00ef0` |
| Google Gemini CLI | `dist/plugins/promptiq-gemini-cli.zip` | 1,416 bytes | `bfa2f4292a5ac30d2efe23c2daf99bdf15afe4f932750fa0e6a02ab60be4ed1a` |
| Universal MCP | `dist/plugins/promptiq-mcp.zip` | 1,459 bytes | `0609c9a37bb60d182a3b9457aaaf02d1aade6a514995637073e40846f0406f0e` |
