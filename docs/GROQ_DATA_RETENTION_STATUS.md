# Groq Data Retention & Zero Data Retention Status (Phase 3.4.2)
## Audit of Data Handling, Logging Windows, and Zero Data Retention Governance

**Audit Date**: 2026-11-22  
**Target Provider**: GroqCloud  
**Data Privacy Classification**: `ZDR_AVAILABLE` (Platform Feature Confirmed; Account-Level Activation Unverified)  

---

## 1. Verified Provider Data Retention Policies

| Policy Domain | GroqCloud Official Terms | Operational Impact for PromptIQ |
|---|---|---|
| **Model Training** | Groq **DOES NOT train** internal or third-party AI models on customer prompts or completions sent via the API. | **Complies** with data privacy invariants. |
| **Default Log Retention** | Prompts and completions are retained in secure system logs for **up to 30 days** solely for abuse monitoring and system reliability. | Data exists on Groq servers for 30 days unless ZDR is active. |
| **Zero Data Retention (ZDR)** | Supported via **Groq Console > Settings > Data Controls**. When enabled, zero prompt/completion data is retained in logs. | Available on Free and Developer plans. |
| **Data Residency** | Core LPU data centers are located in the United States. | Cross-border data transfer from international users to US. |
| **Operational Metadata** | Timestamps, token usage, model identifiers, and client IP addresses are logged indefinitely for billing and abuse monitoring. | Non-content metadata is retained. |

---

## 2. Four-Stage ZDR Status Hierarchy

PromptIQ strictly separates platform capability from actual account activation:

| Status Code | Meaning | Current Status in PromptIQ |
|---|---|---|
| **`ZDR_AVAILABLE`** | Provider documentation confirms ZDR feature exists on platform. | **`VERIFIED`** (Groq Console provides ZDR toggle). |
| **`ZDR_REQUESTED`** | Operator requested or attempted to toggle ZDR setting. | `UNVERIFIED` (Pending operator action). |
| **`ZDR_ENABLED`** | Operator inspected Groq Console and verified ZDR is active. | `UNVERIFIED` (Requires operator dashboard inspection). |
| **`ZDR_PROVIDER_VERIFIED`**| API response headers or cryptographic audit logs confirm zero retention. | `UNVERIFIED` (Not reported via HTTP headers). |

---

## 3. Mandatory Safety Rules for Live Testing

Because ZDR activation on the operator's account has not yet been verified in this workspace:
1. **Zero Confidential Data**: Never transmit proprietary source code, confidential business logic, or customer intellectual property.
2. **Synthetic Prompts Only**: All smoke tests and pilot workflows must use public synthetic scenarios (e.g., arithmetic calculations, fictional food-share platforms).
3. **Operator Recommendation**: Before conducting live tests, the operator should navigate to **Groq Console > Settings > Data Controls** and toggle Zero Data Retention to **ON**.
