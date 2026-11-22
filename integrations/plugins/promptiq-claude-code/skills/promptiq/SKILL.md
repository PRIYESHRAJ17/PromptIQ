---
name: promptiq-claude-code
description: Deep prompt intelligence, forensic autopsy, and persistent Project Constitution memory for Claude Code.
version: 1.0.0
---

# PromptIQ for Claude Code

Connects Claude Code subagents directly to the PromptIQ zero-price intelligence gateway.

## Capabilities
- Query canonical Project Constitution memory before answering architectural questions.
- Execute Prompt Autopsy to identify vagueness, hidden hallucinations, and security flaws.
- Compile and validate Anthropic-native tool calling schemas and prompt suites.

## MCP Tools
All 7 standard PromptIQ MCP tools are exposed via stdio:
- `promptiq_get_constitution`
- `promptiq_propose_constitution_change`
- `promptiq_compile_prompt`
- `promptiq_run_autopsy`
- `promptiq_search_evidence`
- `promptiq_execute_workflow`
- `promptiq_get_quota_status`
