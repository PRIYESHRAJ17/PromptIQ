---
name: promptiq
description: Direct access to PromptIQ Prompt Intelligence, Project Constitution memory, task compilers, and adversarial autopsy review.
version: 1.0.0
---

# PromptIQ Intelligence Skill for Google Antigravity

Use this skill when you need to access persistent project memory, decompose complex user requests across 10 specialized task families, compile target-native prompt packages, or run adversarial Prompt Autopsy diagnostics.

## Available Capabilities & MCP Tools

PromptIQ exposes 7 authoritative intelligence tools:

1. `promptiq_get_constitution(project_id: str)`: Fetch the canonical Project Constitution, active requirements, decisions, and supersession chains.
2. `promptiq_propose_constitution_change(project_id: str, updates: dict)`: Propose atomic updates to goals, requirements, or decisions with immutable version tracking.
3. `promptiq_compile_prompt(specification: dict, target_format: str)`: Compile a Prompt Specification into native Antigravity, Claude Code, Cursor, Codex, or Gemini instruction packages.
4. `promptiq_run_autopsy(prompt_text: str, target_environment: str)`: Execute an adversarial 21-category forensic autopsy against any prompt.
5. `promptiq_search_evidence(query: str, project_id: str)`: Query the verified evidence graph with exact character offset citations.
6. `promptiq_execute_workflow(task_type: str, parameters: dict)`: Launch a database-backed, distributed workflow execution.
7. `promptiq_get_quota_status()`: Verify zero-price status and request allowance.

## Mandatory Invariants

1. **Canonical Truth**: Never maintain local unverified assumptions. All decisions must be recorded in the Project Constitution.
2. **Zero Price Guarantee**: Never ask the user for LLM API keys or suggest paid fallback routes.
3. **No Local Inference**: PromptIQ routes all intelligence through the hosted zero-price gateway.
4. **Adversarial Honesty**: Always provide unsparing critique in Prompt Autopsies. Never output decorative praise.
