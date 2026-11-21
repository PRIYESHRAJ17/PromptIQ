# Groq Data Retention & Zero Data Retention (ZDR) Audit (Phase 3.4.1)
## Privacy Governance, Log Retention Periods, and Zero Data Retention Verification

**Audit Date**: 2026-11-22  
**Target Provider**: GroqCloud  
**Classification**: `ZDR_AVAILABLE` (Feature exists on platform; account-level activation requires operator dashboard verification)  

---

## 1. Official Data Handling & Retention Policy

Groq's official privacy and data handling terms govern API inference requests across GroqCloud:

| Policy Area | Official GroqCloud Specification | PromptIQ Verification Status |
|---|---|---|
| **Model Training on Customer Prompts** | **Groq DOES NOT train models** on customer prompts, completions, or API inference data by default. | **VERIFIED** via Groq AI Model Terms. |
| **Default Log Retention Period** | Prompts and completions are stored in temporary security logs for **up to 30 days** solely for system reliability and abuse monitoring. | **VERIFIED** via Groq Privacy Policy. |
| **Data Residency** | Core inference data centers are located primarily in the United States, with expanding nodes in Canada and Europe. | **US Data Residency Default**. |
| **Metadata Handling** | Request metadata (timestamps, token counts, model ID, IP addresses) is retained for operational metrics and billing reconciliation. | **Retained as Operational Metadata**. |

---

## 2. Zero Data Retention (ZDR) Governance

Groq offers a dedicated **Zero Data Retention (ZDR)** setting within GroqCloud Data Controls:

- **What ZDR Does**: When enabled, Groq ceases temporary logging of prompts and completions for abuse and reliability monitoring. Data is processed strictly in-memory on LPUs during inference and discarded immediately upon response completion.
- **Console Activation**: Organization administrators can toggle ZDR via **Groq Console > Settings > Data Controls**.
- **Impact & Trade-offs**: Enabling ZDR disables certain dashboard features that rely on historical prompt logging (e.g., viewing past completions in the Groq Playground or request inspection tools).

---

## 3. Distinction of ZDR States

To prevent misleading claims regarding data privacy, PromptIQ tracks the following states:

| Classification | Meaning in PromptIQ | Current Status for PromptIQ |
|---|---|---|
| `ZDR_AVAILABLE` | The provider platform supports Zero Data Retention. | **CONFIRMED** (Groq supports ZDR in Console settings). |
| `ZDR_REQUESTED` | Operator submitted request or toggled setting in console. | `UNVERIFIED` (Pending operator action). |
| `ZDR_ENABLED` | ZDR is actively engaged for the organization. | `UNVERIFIED` (Requires operator dashboard inspection). |
| `ZDR_PROVIDER_VERIFIED` | Provider API headers or confirmation confirm active ZDR. | `UNVERIFIED`. |

---

## 4. Operational Safety Protocol for Initial Testing

Because ZDR status on the operator's individual account is currently unverified (`ZDR_AVAILABLE`, but not confirmed active):
1. **Synthetic-Only Data**: Initial smoke tests and pilot evaluations must utilize **only non-sensitive, synthetic prompts**.
2. **Zero PII / Zero Confidential IP**: No proprietary customer project code, user identities, or confidential business rules will be transmitted.
3. **Operator Recommendation**: Before dispatching any real project data through Groq, the operator should navigate to **Groq Console > Settings > Data Controls** and toggle Zero Data Retention to `ON`.
