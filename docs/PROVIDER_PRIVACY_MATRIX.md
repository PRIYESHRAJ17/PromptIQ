# PromptIQ Provider Privacy Matrix & Data Governance Policy

**Version**: 3.2.0  
**Effective Date**: November 2026  
**Compliance Standard**: Zero-Data-Leakage, Least Privilege, Non-Training Enforcement  

---

## 1. Data Sensitivity Classifications

PromptIQ categorizes all project data and prompts into four strict sensitivity tiers:

| Sensitivity Tier | Definition & Typical Contents | Permitted Provider Routes |
| :--- | :--- | :--- |
| **`PUBLIC`** | Open-source specifications, public API definitions, generic software queries, tutorials. | All verified zero-price providers (Google, Groq, OpenRouter :free, Mock). |
| **`GENERAL`** | Standard development tasks, non-proprietary business requirements, generic architecture design. | Google AI Studio free tier, GroqCloud free tier, OpenRouter :free, Mock. |
| **`CONFIDENTIAL`** | Proprietary algorithms, project secrets, trade secrets, sensitive database schemas, commercial logic. | **GroqCloud free tier, Mock / Internal only.** Prohibits Google AI Studio Developer API free tier. |
| **`RESTRICTED`** | Regulated compliance data (HIPAA, PII, financial keys, cryptographic keys, air-gapped specs). | **Internal Zero-Egress Mock / Deterministic Engine ONLY.** All external cloud APIs strictly prohibited. |

---

## 2. Provider Privacy Terms & Training Policy Comparison

| Provider | Service Tier | Training Policy | Data Retention | Human Review Policy | Allows Confidential? | Allows Restricted? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Google AI Studio** | Developer API (Free) | **Allowed for Model Improvement** | Up to 30 days | **Prompts & outputs may be reviewed by human annotators** | ❌ **NO (Blocked)** | ❌ **NO (Blocked)** |
| **GroqCloud** | Free Developer Tier | **No Base Model Training** | 30 days (Abuse / Security) | Ephemeral processing; no routine human review | ✅ **YES** | ❌ **NO (Blocked)** |
| **OpenRouter** | Free Community Tier | Variable Upstream Terms | Up to 30 days | Intermediary logging dependent on upstream model host | ❌ **NO (Blocked)** | ❌ **NO (Blocked)** |
| **PromptIQ Internal** | Deterministic Engine | **Zero Retention / Zero Egress** | 0 days (In-Memory Only)| No human review; runs air-gapped on server | ✅ **YES** | ✅ **YES (Approved)** |

---

## 3. Enforcement Mechanisms

1. **`PrivacyGovernanceService` Gate**:
   - Every request submitted to `DynamicModelRouter` specifies a `DataSensitivityLevel`.
   - The router queries `PrivacyGovernanceService.filter_models_for_sensitivity(...)`.
   - If a user marks a project or task as `CONFIDENTIAL`, the Google AI Studio adapter is systematically removed from the candidate pool. Attempting to route directly to Google triggers `PrivacyPolicyViolationError`.
2. **`RESTRICTED` Airgap Guarantee**:
   - All `RESTRICTED` tasks are routed strictly to the internal deterministic engine.
   - Network egress is blocked at the network interface layer.
3. **Secret Redaction Pipeline**:
   - All prompts entering the gateway pass through `SecretRedactor`, stripping API keys, private keys, passwords, and tokens before provider dispatch.
