# PROMPTIQ AGENTS AND WORKSPACE RULES

## CORE PROJECT INVARIANTS (MANDATORY & NON-NEGOTIABLE)

1. **STRICTLY NO WEBSITE FRONTEND**:
   - The website frontend is strictly out of scope. Do not build UI, HTML/React/Next.js pages, CSS, components, mockups, or shells until explicitly authorized by the user.
   - All backend APIs, schemas, and contracts must fully support the future frontend without backend redesign.

2. **ZERO-PRICE & NO BYOK / NO USER API KEYS**:
   - PromptIQ is 100% free to users.
   - Never ask users for OpenAI, Anthropic, Gemini, Groq, OpenRouter, or search API keys.
   - Never implement a user-facing API key input or BYOK configuration.
   - No paid inference routes and no paid fallback routes. Any route with non-zero pricing must be rejected.
   - If zero-price capacity is exhausted, queue or pause with clear communication; never switch to a paid route.

3. **NO LOCAL INFERENCE**:
   - Official PromptIQ is a centrally hosted intelligence service. Do not require users to install Ollama, llama.cpp, or use local GPUs.

4. **CENTRALLY MANAGED HOSTED INFERENCE**:
   - One managed internal model service powers Website API, Telegram Bot, MCP Server, CLI, SDK, and integrations.
   - Same internal model release and quality across all product surfaces.
   - Server-side credentials only (managed by operator).

5. **SHARED BACKEND & PERSISTENT PROJECT MEMORY**:
   - All surfaces (Website API, Telegram Bot, MCP/Plugin) share identity, projects, Project Constitution, discovery state, Prompt Specification, evidence, evaluations, and checkpoints.
   - Changes from any surface update the shared canonical project record with provenance, versioning, conflict checks, and audit trails.

6. **ADAPTIVE DISCOVERY & PROJECT CONSTITUTION**:
   - Conversational-first discovery (Quick, Guided, Deep).
   - Never re-ask questions already answered in conversation, files, or approved state.
   - Canonical source of truth is the immutable, versioned Project Constitution with strict provenance: `user_provided`, `file_extracted`, `connected_source`, `inferred`, `research_backed`, `unknown`, `conflicting`.

7. **PROMPT INTELLIGENCE & NATIVE COMPILATION**:
   - Compile PromptIQ Prompt Specification (PPS) to target-native formats: Prompt-only, Prompt Suite, or Complete Native Instruction Package (Antigravity, Claude Code, OpenAI Codex, Cursor, Gemini CLI, etc.).
   - Model and host/environment registries are strictly separated.

8. **ADVERSARIAL CRITIQUE & PROMPT AUTOPSY**:
   - Strict critical review with actionable findings, severity levels, evidence, impact, and corrections. No unearned praise or decorative agent theatre.

9. **RESEARCH WITH EVIDENCE LEDGER**:
   - Zero hallucinations or fake citations. All factual claims must track publisher, URL, date, locator, support status, confidence rationale, and contradictory evidence.

10. **SECURITY, PRIVACY & LEAST PRIVILEGE**:
    - Untrusted external inputs are sanitized.
    - Tenant isolation and row-level authorization.
    - Read-only by default. Explicit approval required for file writes, execution, deployments, or external messages.
    - Never log secrets or private user data.

11. **VERIFICATION & CODE QUALITY**:
    - Mandatory automated testing: unit, integration, contract, zero-price enforcement, tenant isolation.
    - Static analysis (ruff, pytest) and independent code review.
    - No false completion claims. Proof of functionality required.
