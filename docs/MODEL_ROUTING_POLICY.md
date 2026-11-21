# PromptIQ Model Routing Policy & Selection Algorithm

**Version**: 3.2.0  
**Status**: ACTIVE  
**Engine**: `DynamicModelRouter` (`promptiq.orchestrator.router`)

---

## 1. Routing Decision Pipeline

The PromptIQ Dynamic Model Router evaluates candidate models using a multi-stage constraint satisfaction pipeline:

```
[Inbound Task Request]
         │
         ▼
[Stage 1: Role Matching] ──────► Filter by capabilities (reasoning, tools, context window)
         │
         ▼
[Stage 2: Privacy Filter] ─────► Filter by DataSensitivityLevel (Google free tier excluded for CONFIDENTIAL)
         │
         ▼
[Stage 3: Family Separation] ──► Filter out Generator family (Critic.family != Generator.family)
         │
         ▼
[Stage 4: Circuit Breaker] ────► Check provider pause state (429 / upstream downtime)
         │
         ▼
[Stage 5: Quota & Token Cap] ──► Check sliding window RPM, RPD, TPM, TPD ceilings
         │
         ▼
[Selected Model Record] ───────► Dispatch to provider adapter ($0 guaranteed)
```

---

## 2. Mandatory Structural Constraints

### 2.1 The Critic Independence Invariant
To prevent **confirmation bias** and shared model family blind spots, the Independent Critic role MUST NOT belong to the same model family as the generating model:

$$\text{ModelFamily}(\text{Critic}) \neq \text{ModelFamily}(\text{Generator})$$

- If Generator is **Groq Llama** (`llama-3.3-70b-versatile`), the Critic must be **Google Gemini** (`gemini-3.8-flash`) or **Groq Qwen** (`qwen-2.5-coder-32b`).
- If Generator is **Google Gemini**, the Critic must be **Groq Llama** or **Groq Qwen**.
- In offline deterministic test environments, independent specialized prompts and assertion rules enforce this separation.

### 2.2 Fail-Closed Zero-Price Invariant
If all eligible zero-price models for a specific role have reached their rate limit or daily token ceiling:
1. **The router MUST NOT fall back to any paid provider** (e.g. OpenAI, Anthropic, or billable Vertex AI).
2. **The router raises `CapacityExhaustedError`** with an explicit `retry_after` timestamp.
3. The affected workflow pauses safely, preserving all user state and draft artifacts.

---

## 3. Quota Ceiling Thresholds

The router evaluates model-specific quotas before dispatching requests:

| Model ID | Provider | RPM Cap | RPD Cap | TPM Cap | TPD Cap | Header Inspection Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `gemini-3.8-flash` | Google | 15 | 1,500 | 1,000,000 | 10,000,000 | `retry-after` on HTTP 429 |
| `gemini-3.5-flash-lite` | Google | 30 | 1,500 | 1,000,000 | 10,000,000 | `retry-after` on HTTP 429 |
| `llama-3.3-70b-versatile` | Groq | 30 | 1,000 | 12,000 | 100,000 | `x-ratelimit-remaining-tokens < 500` trips breaker |
| `llama-3.1-8b-instant` | Groq | 30 | 14,400 | 6,000 | 500,000 | `x-ratelimit-remaining-requests == 0` trips breaker |
| `qwen-2.5-coder-32b` | Groq | 30 | 1,000 | 6,000 | 100,000 | `x-ratelimit-remaining-tokens < 500` trips breaker |
