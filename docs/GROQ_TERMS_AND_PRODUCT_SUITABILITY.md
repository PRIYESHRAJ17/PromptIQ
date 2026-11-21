# Groq Services Agreement & Product Suitability Assessment (Phase 3.4.1)
## Analysis of Commercial Terms, "Consumer Use" Restrictions, and Public Application Eligibility

**Audit Date**: 2026-11-22  
**Target Provider**: Groq, Inc.  
**Applicable Documents**: Groq Services Agreement, AI Model Terms, Website Terms of Use, Privacy Policy  
**Classification**: `REVIEW_REQUIRED` (Public Production) / `PERMITTED` (Internal Development & Operator Evaluation)  

---

## 1. The Core Contractual Clause

The **Groq Services Agreement** governs access to GroqCloud and its AI Model APIs. It contains the following explicit restriction:

> *"Cloud Services and the AI Model Services under this Agreement are not for consumer use."*

Simultaneously, the Agreement defines and permits the distribution of services through Customer Applications:
- **"Customer Application"**: *"means Customer's applications, products, or services in which Customer may integrate the Cloud Services and AI Model Services as permitted by the Agreement."*
- **"End Users"**: *"means the end users of a Customer Application who are authorized by Customer to access or use the Cloud Services and AI Model Services through the application."*

This creates a critical legal distinction that must be rigorously analyzed before deploying PromptIQ to the general public.

---

## 2. Evaluation of PromptIQ's Target Audience

PromptIQ is designed as a Universal Prompt Intelligence and Project Engineering Platform. Its target audience encompasses:
1. **Software Developers & Engineers**: Designing production-grade prompts and agent suites.
2. **Founders & Product Managers**: Architecting project specifications and technical constitutions.
3. **Researchers & Academics**: Evaluating prompt behavior and cross-agent interoperability.
4. **Students (Higher Education / Technical)**: Learning prompt engineering and software design.
5. **General Public / Consumers / Minors**: Exploring prompt generation and chat interactions.

---

## 3. Detailed Legal & Risk Investigation

| Investigation Angle | Contractual Finding | PromptIQ Risk & Eligibility Impact |
|---|---|---|
| **1. Does PromptIQ qualify as an eligible "Customer"?** | Yes. PromptIQ operates as an independent software entity integrating Groq APIs via backend server-side credentials into a "Customer Application". | Eligible as a developer/business entity. |
| **2. Does free public access change the assessment?** | Potentially. Providing an unauthenticated or public-facing service can be interpreted as distributing the service to "consumers" rather than enterprise/developer users. | Raises ambiguity regarding consumer exposure. |
| **3. Are downstream consumer End Users permitted?** | Ambiguous. While the agreement permits "End Users" accessing a "Customer Application", the overarching limitation that services are "not for consumer use" could be violated if the primary End Users are retail consumers using the app for personal, non-professional purposes. | **HIGH AMBIGUITY**; requires provider clarification. |
| **4. Can students use the application?** | Higher-education students acting in an academic or developer capacity are typically classified as researchers/learners. However, general students using the tool for casual personal tasks fall under consumer use. | Conditionally acceptable for technical students; prohibited for general consumer tasks. |
| **5. Do under-18 users create a restriction?** | Yes. Minors are legally classified as consumers. Unlike enterprise users, minors cannot enter commercial contracts. Deploying Groq-backed PromptIQ to minors without age gates risks violating the "not for consumer use" covenant. | **STRICT PROHIBITION FOR MINORS** without formal age verification. |
| **6. Is separate written permission required?** | For public, un-gated consumer deployment, commercial redistribution terms usually require an enterprise agreement or written amendment from Groq Sales. | Required before unrestricted public release. |
| **7. Model License Restrictions** | GPT-OSS models are open-weights (Apache 2.0 compatible), permitting commercial and research use. The restriction originates from Groq's hosting agreement, not the underlying model weights. | Model weights are permissive; hosting terms are restrictive. |
| **8. Free-Tier vs. Developer-Tier Terms** | Both Free and Developer tiers operate under the same overarching Groq Services Agreement. Upgrading to a paid tier does not automatically waive the "not for consumer use" clause. | Tier upgrade does not resolve the legal ambiguity. |

---

## 4. Formal Eligibility Verdict

In accordance with PromptIQ's policy of avoiding legal guesswork:

1. **Internal Development, Synthetic Benchmarks & Operator Testing**:
   - Status: **`PERMITTED`**
   - Justification: The operator is a software developer building and testing technical applications, strictly complying with the developer purpose of GroqCloud.
2. **Public Production Deployment (Unrestricted Public Audience)**:
   - Status: **`REVIEW_REQUIRED` (HELD / UNAPPROVED)**
   - Justification: Groq terms state services are "not for consumer use". Deploying an open public platform that serves students, minors, and casual consumer users without age or business verification poses contractual compliance risk.
3. **Resolution Path**:
   - Operator must obtain written confirmation from Groq support/sales clarifying whether a free developer-focused tool with educational access qualifies under "Customer Application with End Users".
   - Alternatively, PromptIQ must implement a professional/developer attestation gate in production user authentication, excluding casual consumer or minor usage from Groq routes.
