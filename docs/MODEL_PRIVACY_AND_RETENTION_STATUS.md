# PromptIQ Model Privacy, Data Retention, and Governance Status

**Phase**: 3.4 Governance Audit  
**Date**: November 21, 2026  
**Auditor**: Data Protection, Privacy & Information Security Office  

---

## 1. Provider Privacy & Data Handling Ledger

| Provider | Model ID | Training on User Data? | Retention Period | Zero Data Retention (ZDR) Available? | Jurisdiction | Commercial Production Terms? | Audience Constraints | Approved Sensitivity Tiers |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **GroqCloud** | `openai/gpt-oss-120b`<br>`openai/gpt-oss-20b` | **NO** (Zero training on API traffic) | **30 Days** (Transient abuse/reliability logs) | **No on Free Tier** (Enterprise add-on only) | United States | Yes (AS-IS developer terms) | Standard operator $\ge 18$ | `PUBLIC`, `GENERAL`, `CONFIDENTIAL` |
| **Google AI Studio** | `gemini-3.8-flash`<br>`gemini-3.5-flash-lite` | **YES** (Free tier prompts used for training) | **30+ Days** (Subject to human review) | Paid Vertex AI only | United States | Developer API terms | **Strictly $\ge 18$ Years Old** (Forbidden for minors) | `PUBLIC` and `GENERAL` (Adult developer environments only) |
| **Cloudflare Workers AI** | `@cf/meta/llama-3.1-8b-instruct` | **NO** | **0 Days** (Ephemeral edge inference) | Native at Edge | Global / Edge | Standard Terms | Standard | `PUBLIC`, `GENERAL`, `CONFIDENTIAL` |
| **Internal Engine** | `promptiq-mock-v1` | **NO** | **0 Days** (In-memory execution) | Native in-process | Local / VPC | N/A (Internal) | All audiences | `PUBLIC`, `GENERAL`, `CONFIDENTIAL`, `RESTRICTED` |

---

## 2. In-Depth Privacy Findings

### 2.1 Groq Data Retention & Zero Data Retention (ZDR) Reality
1. **Default Free Tier Retention**: Under Groq's standard Cloud Services Agreement, inference inputs and completions are retained in transient security logs for **up to 30 days** to ensure abuse prevention, service stability, and compliance monitoring.
2. **Zero Data Retention (ZDR) Status**:
   - Groq provides a Zero Data Retention option under customized enterprise contracts.
   - **Critical Fact**: ZDR is **NOT enabled by default** on free-tier developer accounts.
   - **PromptIQ Handling**: PromptIQ records `data_retention_days=30` in Groq's `ProviderPrivacyCard`. Because data is held for 30 days, tasks classified as `RESTRICTED` (such as HIPAA compliance, unreleased cryptographic keys, or classified specifications) are **strictly barred** from Groq and routed only to the internal air-gapped engine.

### 2.2 Google Gemini Data Training and Minor Audience Restrictions
1. **Data Training**: Free-tier Google AI Studio API prompts are logged, reviewed by human evaluators, and utilized to train Google foundation models.
2. **Age Restriction Clause**: Under the Gemini API Additional Terms, applications directed towards or accessed by individuals under 18 years old are strictly prohibited.
3. **PromptIQ Handling**: Because PromptIQ's mission embraces students, education, and general public users, Gemini is excluded from general production routes.

---

## 3. Four-Tier Data Sensitivity Enforcement

PromptIQ's `PrivacyGovernanceService` strictly enforces data boundary rules:

$$\text{PUBLIC} (0) < \text{GENERAL} (1) < \text{CONFIDENTIAL} (2) < \text{RESTRICTED} (3)$$

```
[ Task Sensitivity ]
        │
        ├── PUBLIC / GENERAL ──────► Groq (120B / 20B) or Gemini (Adult Dev)
        │
        ├── CONFIDENTIAL ──────────► Groq (120B / 20B) [Google is BLOCKED]
        │
        └── RESTRICTED ────────────► Internal Deterministic Engine [All external APIs BLOCKED]
```
