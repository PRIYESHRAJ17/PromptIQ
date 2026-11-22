# PromptIQ — Provider and Target Provenance Ledger

**Version**: 3.0.0  
**Updated**: 2026-11-22  
**Policy Reference**: [AGENTS.md](file:///c:/Users/Priyesh%20Raj/Desktop/PromptIQ/AGENTS.md), [MODEL_ELIGIBILITY_REGISTRY.md](file:///c:/Users/Priyesh%20Raj/Desktop/PromptIQ/docs/MODEL_ELIGIBILITY_REGISTRY.md)

---

## 1. Executive Summary

This document establishes the canonical provenance, technical capabilities, context boundaries, and operational constraints for:
1. **Target Execution Hosts (6 Target Adapters)** compiled from the PromptIQ Prompt Specification (PPS v2.0).
2. **Inference Provider Routes (4 Hosted Provider Routes)** accessible through PromptIQ's centrally managed, zero-price Model Gateway.

Every entry in this ledger is backed by verified official specifications, empirical API headers, or legal service terms.

---

## 2. Target Execution Hosts Provenance

PromptIQ separates the model from the execution environment. The Prompt Specification (PPS v2.0) is compiled into target-native instruction formats tailored to the exact tool declarations, memory conventions, and file structures of each target host.

| Target ID | Target Host Name | Default Context Window | Native Tool Capabilities | Output File Structure | Provenance Status | Canonical Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `raw-prompt` | **Raw Prompt / Plain Suite** | `None` *(Format only)* | None *(Host agnostic text)* | `.txt` / `.json` prompt suite | `VERIFIED_OFFICIAL_SPEC` | RFC 8259 JSON / Plain UTF-8 |
| `cursor` | **Cursor IDE** | `200,000` tokens | Terminal, File Edit, Git, Workspace Search | `.cursorrules`, `.cursor/rules/*.mdc` | `VERIFIED_OFFICIAL_SCHEMA` | Cursor Official Documentation (2025) |
| `antigravity` | **Google Antigravity SDK** | `1,048,576` tokens | `run_command`, `read_file`, `write_file`, `edit_file`, `invoke_subagent`, `send_message` | `AGENTS.md`, `GEMINI.md`, `.gemini/` configuration | `VERIFIED_OFFICIAL_INTEGRATION` | Google Antigravity Agent Spec (2025-2026) |
| `claude-code` | **Anthropic Claude Code CLI** | `200,000` tokens | `Bash`, `FileEdit`, `Glob`, `Grep`, `NotebookEdit` | `CLAUDE.md`, `.claude/` config | `VERIFIED_OFFICIAL_SCHEMA` | Anthropic Claude Code Spec (2025) |
| `codex` | **OpenAI Codex / Canvas** | `128,000` tokens | Python Sandbox, Shell, Web Search, Canvas | `CODEX.md`, `instructions.md` | `VERIFIED_OFFICIAL_SCHEMA` | OpenAI Codex / GPT-4o Agent Reference |
| `gemini-cli` | **Google Gemini Developer CLI**| `1,048,576` tokens | Terminal execution, file inspection, Google Cloud SDK | `GEMINI.md`, `.gemini/config` | `VERIFIED_OFFICIAL_SCHEMA` | Google Cloud Gemini Developer Kit |

### Target Adapter Specifications & Design Notes

#### 1. `raw-prompt`
- **Context Window**: `None`.
- **Architectural Rationale**: Raw prompt is a text serialization target, not an execution host, virtual runtime, or model provider. It possesses no inherent context window, memory barrier, or tool calling layer. Assigning a synthetic context window (e.g. 128k or 200k) to raw prompt conflates prompt text formatting with execution container limits.
- **Output Artifacts**: Serialized markdown prompt suite or plain structured text blocks.

#### 2. `cursor`
- **Context Window**: 200,000 tokens (derived from underlying Claude 3.5 Sonnet / GPT-4o models).
- **Execution Model**: Rules-based IDE assistant. Rules are injected as system instructions on file-scoped glob matching (`.cursor/rules/*.mdc`) or workspace root (`.cursorrules`).
- **Tooling Constraints**: Tool calls are mediated by Cursor IDE's internal agent loop.

#### 3. `antigravity`
- **Context Window**: 1,048,576 tokens (leveraging Gemini 1.5 Pro / 2.0 Flash agent backends).
- **Execution Model**: Multi-agent collaborative swarm and subagent hierarchy.
- **Tooling Conventions**: Strict native function calling interface: `run_command`, `read_file`, `write_file`, `edit_file`, `invoke_subagent`, `send_message`. All file edits enforce exact string targeting; tools require explicit human escalation for mutating external operations.

#### 4. `claude-code`
- **Context Window**: 200,000 tokens (Claude 3.7 / 3.5 Sonnet architecture).
- **Execution Model**: High-agency terminal CLI agent. Instructions are governed by root `CLAUDE.md`.
- **Tooling Conventions**: Direct Unix shell execution, file diffs, git branch management.

#### 5. `codex`
- **Context Window**: 128,000 tokens (GPT-4o architecture).
- **Execution Model**: Code editing, refactoring, and sandbox-based execution.
- **Tooling Conventions**: Code generation and python environment execution mediated by OpenAI platform tools.

#### 6. `gemini-cli`
- **Context Window**: 1,048,576 tokens (Gemini 2.0 Flash architecture).
- **Execution Model**: Developer CLI with deep terminal and GCP integration.
- **Tooling Conventions**: Project-scoped `GEMINI.md` markdown rules and CLI extensions.

---

## 3. Hosted Provider Routes Provenance

PromptIQ strictly mandates a **Zero-Price to Users Forever** architecture. Users are never charged, and no user-provided API keys (BYOK) are permitted. All inference is routed through centrally managed operator credentials on zero-cost tiers.

| Provider Route | Model Identifier | Free Tier Cost | Quota Limits (RPM / TPM / RPD) | Data Retention & Privacy Terms | Operational Status | Provenance Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GroqCloud** | `openai/gpt-oss-120b` | ₹0.00 / $0.00 | 30 RPM / 8,000 TPM / 100k TPD | 30-day zero-training enterprise guarantee | `LIVE_VERIFIED_FREE` | `req_01m7zr9k96ethbpvc22gc1hddj` & `req_01m7zvprh4ev9v7e67f2ypx2r7` |
| **GroqCloud** | `openai/gpt-oss-20b` | ₹0.00 / $0.00 | 30 RPM / 8,000 TPM / 100k TPD | 30-day zero-training enterprise guarantee | `LIVE_VERIFIED_FREE` | `req_01m7zrbddcea793zn4xvrhtskw` |
| **GroqCloud** | `llama-3.3-70b-versatile` | ₹0.00 / $0.00 | 30 RPM / 6,000 TPM / 100k TPD | 30-day zero-training enterprise guarantee | `LIVE_VERIFIED_FREE` | Header validation & provider documentation |
| **Google Gemini** | `gemini-2.0-flash` | ₹0.00 / $0.00 | 15 RPM / 1,000,000 TPM / 1,500 RPD | **Human review permitted by Google**; training on inputs allowed. Prohibited for minors (<18). | `IMPLEMENTED_PENDING_OPERATOR_KEY` | Google AI Studio Terms of Service (Dec 2024) |
| **Google Gemini** | `gemini-1.5-pro` | ₹0.00 / $0.00 | 2 RPM / 32,000 TPM / 50 RPD | **Human review permitted by Google**; training on inputs allowed. | `IMPLEMENTED_PENDING_OPERATOR_KEY` | Google AI Studio Terms of Service |
| **Cerebras** | `llama-3.3-70b` | ₹0.00 / $0.00 | 30 RPM / 60,000 TPM / Unlimited RPD | Standard enterprise API privacy (no training) | `IMPLEMENTED_PENDING_OPERATOR_KEY` | Cerebras Cloud Free Tier Documentation |
| **Hugging Face** | `zephyr-7b-beta` | ₹0.00 / $0.00 | Variable community rate limits | Public community inference API | `IMPLEMENTED_PENDING_OPERATOR_KEY` | HF Inference API TOS |

---

## 4. Prohibited Provider Routes (Hard-Rejected)

The following routes are permanently blacklisted by PromptIQ's `ZeroPriceGate` and `EligibilityGate`:

1. **Direct OpenAI Paid API** (`api.openai.com/v1/chat/completions` with paid billing): **REJECTED**.
2. **Direct Anthropic Paid API** (`api.anthropic.com/v1/messages` with paid billing): **REJECTED**.
3. **OpenRouter Paid Inference Routes** (any model with non-zero prompt/completion pricing): **REJECTED**.
4. **All BYOK (Bring-Your-Own-Key) Configurations**: Any request containing user-submitted provider keys (e.g. `api_key`, `openai_key`, `groq_key`) is rejected with HTTP 400 and `ProhibitedBYOKError`.
5. **Auto-Upgrade Paid Routes**: Any route that automatically transitions to credit card billing when free quota is exhausted is rejected. PromptIQ enforces a **fail-closed circuit breaker**.

---

## 5. Token Accounting & Quota Ledger Reconciliation

Based on GroqCloud's free tier headers and live execution audit:
- **Combined TPM Quota**: GroqCloud enforces an 8,000 TPM limit combining input and output tokens for GPT-OSS 120B.
- **Empirical Execution Audit (Workflow `422f4399-c93f-439f-a7ef-bbf3149a4057`)**:
  - Stage A Orchestration: 214 input + 3,146 output = 3,360 tokens (`req_01m7zssrj0ee28v1rdzv49pt8a`).
  - Stage B Generation: 206 input + 4,096 output = 4,302 tokens (`req_01m7zsszn3etavc26tspeb7jhr`).
  - Combined Stage A + B: 7,662 tokens used within 60 seconds.
  - Remaining TPM in rolling window: 338 tokens.
  - Stage E Revision: Resumed cleanly after rolling reset window elapsed, utilizing `req_01m7zvprh4ev9v7e67f2ypx2r7` (2,842 tokens) without duplicate spend.
- **Durable Quota Ledger**: Persisted in `data/quota_ledger.json` with file-level multi-process locking (`msvcrt` on Windows, `fcntl` on Unix), ensuring that quota usage survives process restarts and CLI invocations.
