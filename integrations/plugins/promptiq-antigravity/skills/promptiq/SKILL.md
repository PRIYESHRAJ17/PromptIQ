---
name: promptiq
description: Direct access to PromptIQ Prompt Intelligence, Project Constitution memory, task compilers, and adversarial autopsy review. Use when optimizing or diagnosing prompts, managing project constitutions, or compiling target instructions.
---

# PromptIQ Intelligence Skill for Google Antigravity

Use this skill when you need to access persistent project memory, decompose complex user requests across 10 specialized task families, compile target-native prompt packages, or run adversarial Prompt Autopsy diagnostics.

## Available Capabilities & MCP Tools

PromptIQ exposes authoritative intelligence tools through the `promptiq` MCP server:

1. `create_project(name, description)`: Create a new PromptIQ project with an initial Project Constitution.
2. `run_discovery(project_id, goal, depth)`: Start or continue adaptive discovery for a project (`quick`, `guided`, or `deep`).
3. `get_project_constitution(project_id)`: Retrieve the canonical Project Constitution source of truth, requirements, and decisions.
4. `compile_prompt(project_id, target_environment, output_type)`: Compile the approved Constitution into target-native instructions (Antigravity, Claude Code, Cursor, Codex).
5. `review_prompt(prompt_text, target_environment)`: Execute an adversarial 18-21 category forensic autopsy and diagnostic critique.
6. `research(project_id, query, mode)`: Investigate technical documentation and record claims in the Evidence Ledger.
7. `record_checkpoint(project_id, phase, summary)`: Record a verified project milestone checkpoint for cross-agent continuity.
8. `get_context_pack(project_id, max_token_budget)`: Compile and pack project context for an external agent within a token budget.
9. `execute_agent_task(objective, task_type, max_iterations)`: Execute an objective through the PromptIQ autonomous observe-decide-act agent loop.
10. `get_quota_status()`: Verify PromptIQ zero-price guarantee, quotas, and active anti-BYOK enforcement.

## Core Architectural Invariants

1. **Canonical Truth**: Never maintain local unverified assumptions. All decisions must be recorded in the Project Constitution.
2. **Zero Price Guarantee**: Never ask the user for LLM API keys or suggest paid fallback routes.
3. **No Local Inference**: PromptIQ routes all intelligence through the hosted zero-price gateway.
4. **Adversarial Honesty**: Always provide unsparing critique in Prompt Autopsies. Never output decorative praise.
