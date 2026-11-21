# PromptIQ Security, Privacy, and Trust Policy

## 1. Threat Modeling & OWASP Top 10 GenAI Defenses

PromptIQ operates in a high-stakes AI environment where user intent, external web documentation, and untrusted files are synthesized into executable instructions. Security is a release-blocking requirement.

| Threat Category | Risk Description | PromptIQ Mitigation Strategy |
| :--- | :--- | :--- |
| **LLM01: Prompt Injection** | Untrusted content (web pages, uploaded docs) hijacking agent instructions. | **Strict Data/Instruction Separation**: External text is treated as untrusted data, never as system instructions. Delimiters, structural isolation, and adversarial sanitization applied before LLM consumption. |
| **LLM02: Sensitive Information Disclosure** | Leaking private user context, API secrets, or PII into logs or prompt outputs. | **Automated Redactor**: Regex and entropy-based redactor strips secrets, bearer tokens, API keys, and sensitive tokens from logs, exports, and traces. |
| **LLM03: Supply Chain Vulnerabilities** | Malicious third-party dependencies or compromised plugin templates. | **Manifest & Script Validation**: Target adapter manifests and configurations are verified against strict JSON schemas. No unvetted third-party runtime code execution. |
| **LLM04: Data & Model Poisoning** | Ingesting adversarial or malicious web search results. | **Evidence Ledger Provenance**: Claims require verified primary sources, publication dates, and locators. Mismatched or conflicting claims are flagged. |
| **LLM05: Improper Output Handling** | Generated prompts causing arbitrary shell/code execution in target agents. | **Least Privilege Output**: Generated packages specify read-only tool defaults and explicit approval gates for shell or file modification actions. |
| **LLM06: Excessive Agency** | Autonomous agents executing destructive operations without human consent. | **Mandatory Approval Gates**: Consequential actions (file writing, shell execution, external network calls, deployment) require explicit user sign-off. |
| **LLM07: System Prompt Leakage** | Exposing internal operational rules or sensitive gateway infrastructure. | **Separation of Concerns**: Internal orchestration prompts are isolated from public export packages; user packages only contain user-scoped context. |
| **LLM08: Vector & Embedding Weaknesses** | Vector store poisoning or cross-tenant embedding retrieval. | **Strict Relational Tenant Scoping**: All queries enforce tenant isolation at the database layer; vector indexes are strictly tenant-isolated. |
| **LLM09: Misinformation & Hallucination** | Fabricating citations, API cutoffs, or documentation facts. | **Adversarial Critique & Verification**: Prompt Autopsy and Research Engine actively challenge unverified statements. |
| **LLM10: Unbounded Consumption** | Recursive search or prompt generation loops burning rate limits. | **Capacity Governor**: Strict token/step budgets, recursion ceilings, timeouts, and circuit breakers. |

---

## 2. Multi-Tenant Isolation & Access Control

1. **Workspace Boundary**: Every entity (`Project`, `DiscoverySession`, `ProjectConstitution`, `PromptSpec`, `PromptPackage`, `Artifact`) strictly references `workspace_id`.
2. **Authorization Enforcement**: Every API endpoint and service method verifies that the authenticated user possesses active membership in the target workspace.
3. **Cross-Tenant Guard**: Service-level assertions prevent querying or modifying entities across workspaces, returning HTTP 403/404 without leaking resource existence.

---

## 3. Privacy, Data Retention, and User Rights

1. **Zero Secondary Training**: User project context, prompts, and Constitution data are never used for model training or public dataset generation.
2. **Data Minimization**: PromptIQ collects only the minimum information necessary to construct valid project instructions.
3. **Data Export & Deletion**:
   - Users can export complete project dossiers (Constitution, prompts, evidence ledger, checkpoints) in portable JSON/Markdown formats.
   - Deleting a project triggers hard deletion of project records, versions, and stored artifacts from active storage.
4. **Third-Party Provider Disclosure**: When routing inference through approved zero-price providers (e.g., Gemini Developer API, Groq), applicable provider data terms are disclosed.

---

## 4. Secret Management & Redaction Invariants

- **No Secrets in Generated Packages**: Generated instruction packages, `.cursorrules`, `CLAUDE.md`, or Antigravity manifests must never contain API keys, credentials, or personal access tokens.
- **Log Redaction**: Central structured logger automatically redacts authorization headers, passwords, JWT tokens, and common API key patterns (`AIza...`, `gsk_...`, `sk-...`, `ghp_...`).
