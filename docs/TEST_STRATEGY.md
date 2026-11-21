# PromptIQ Comprehensive Test Strategy

## 1. Quality Philosophy & Testing Hierarchy

Testing in PromptIQ is a release-blocking quality gate. Code is not declared complete because it compiles or because an agent asserts it works. Every requirement, invariant, security boundary, and compilation adapter must be verified by automated tests.

```
                    ┌────────────────────────┐
                    │  End-to-End Workflows  │
                    ├────────────────────────┤
                    │ Integration & Security │
                    ├────────────────────────┤
                    │ API Contracts & Schemas│
                    ├────────────────────────┤
                    │  Unit & Domain Logic   │
                    └────────────────────────┘
```

---

## 2. Mandatory Test Categories & Verification Gates

### 2.1 Unit Tests
- **Domain Logic**: Pydantic schema validation, PPS compilation rules, token estimation, diff generation.
- **Coverage**: Core business logic in `promptiq/core/`, `promptiq/compiler/`, `promptiq/discovery/`, and `promptiq/critic/`.

### 2.2 Integration & Database Tests
- **Persistence**: Relational CRUD operations, immutable versioning, foreign keys, and cascading behavior using SQLite in-memory and PostgreSQL.
- **Transactions**: Ensuring multi-step constitution edits and prompt compilations commit atomically.

### 2.3 Authentication & Tenant Isolation Tests
- **Isolation Verification**: Creating two separate workspaces; verifying User A in Workspace A cannot read, edit, or delete any entity belonging to Workspace B.
- **Token Verification**: Expiration handling, signature tampering rejection, and permission scoping.

### 2.4 Zero-Price Model Gateway & Governance Tests
- **Mandatory Invariants Tested**:
  1. *No User API Key Accepted*: Validating that request payloads with user API keys are rejected or ignored.
  2. *Zero BYOK Configuration*: Confirming no user profile field or API setting allows user inference keys.
  3. *Paid Route Rejection*: Testing that any model route with non-zero pricing triggers an immediate rejection exception.
  4. *No Paid Fallback*: Simulating provider outage; confirming the system pauses or queues without calling a paid endpoint.
  5. *Capacity Governor Exhaustion*: Simulating rate-limit exhaustion; verifying graceful queueing and retry-after headers.
  6. *Deterministic Mock Adapter*: Ensuring 100% of test suite runs without external network calls.

### 2.5 Cross-Surface State Synchronization Tests
- **Shared Memory**: Verifying that a project initiated via Telegram Bot or MCP server is immediately retrievable and editable via the REST API with consistent version history.

### 2.6 Target Compiler & Compatibility Tests
- **Manifest Conformance**: Compiling PPS into Antigravity, Claude Code, OpenAI Codex, Cursor, and Gemini CLI targets; verifying output against host schemas.
- **Requirement Preservation**: Verifying that 100% of confirmed requirements from the Constitution are mapped to output instructions.

### 2.7 Security & Redaction Tests
- **Secret Redaction**: Passing strings containing AWS keys, JWTs, and API tokens through the logger and serializer; asserting complete redaction.
- **Injection Sanitization**: Testing malicious markdown payloads designed to override system instructions.

---

## 3. Test Execution Matrix

All tests run via:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

Automated test files:
- `tests/test_api_contracts.py`
- `tests/test_auth_and_tenancy.py`
- `tests/test_zero_price_gateway.py`
- `tests/test_discovery.py`
- `tests/test_discovery_task_paths.py`
- `tests/test_software_discovery.py`
- `tests/test_constitution.py`
- `tests/test_constitution_versioning.py`
- `tests/test_pps_schema.py`
- `tests/test_compiler_modes.py`
- `tests/test_adapters.py`
- `tests/test_registries.py`
- `tests/test_critic_autopsy.py`
- `tests/test_research_engine.py`
- `tests/test_orchestrator.py`
- `tests/test_eval_lab.py`
- `tests/test_project_memory.py`
- `tests/test_telegram_bot.py`
- `tests/test_mcp_server.py`
- `tests/test_cli_sdk.py`
- `tests/test_security.py`
- `tests/test_observability.py`
- `tests/test_capacity_governor.py`
- `tests/test_cross_surface_sync.py`
