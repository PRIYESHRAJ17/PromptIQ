# PROMPTIQ V7 — API & CROSS-SURFACE INTEGRATION VERIFICATION

## 1. Executive Summary

PromptIQ provides a unified backend powering four distinct product surfaces:
1. **REST API** (FastAPI)
2. **MCP Server** (Model Context Protocol)
3. **Command Line Interface (CLI)**
4. **Telegram Bot Adapter**

All surfaces interact with the same underlying database, Project Constitution, memory, and execution engines.

---

## 2. Model Context Protocol (MCP) Server

PromptIQ exposes an MCP Server (`promptiq/mcp/server.py`) with 7 tools:

| MCP Tool Name | Description | Verified in Tests |
|---|---|:---:|
| `forge.create_project` | Creates a new project in the user's workspace. | YES |
| `forge.run_discovery` | Starts an adaptive discovery session with intake questions. | YES |
| `forge.compile_package` | Compiles a target-native prompt package. | YES |
| `forge.review_prompt` | Runs Prompt Autopsy critique against a candidate prompt. | YES |
| `forge.research` | Executes evidence-backed research with character offsets. | YES |
| `forge.record_checkpoint`| Commits milestone checkpoint for cross-agent handoffs. | YES |
| `forge.get_context_pack` | Packs project memory, requirements, and decisions into markdown. | YES |
| `forge.execute_agent_task`| Runs objective through the 11-stage autonomous agent loop. | YES |

---

## 3. Cross-Surface State Consistency

When state is modified via any surface, all other surfaces observe the exact same canonical state:
- A decision added via the REST API or Telegram Bot is immediately retrievable via `forge.get_context_pack` in the MCP Server.
- Checkpoints recorded by an external agent via MCP are queryable in the REST API and CLI.
- Cryptographic SHA-256 hashes guarantee cross-surface artifact identity.

---

## 4. Verification Evidence

- `tests/test_mcp_server.py` (3/3 passed).
- `tests/test_memory_consistency_v7.py` (scenario 10 verified cross-surface MCP context pack retrieval).
- `tests/test_api_v1.py` (FastAPI router endpoints).
