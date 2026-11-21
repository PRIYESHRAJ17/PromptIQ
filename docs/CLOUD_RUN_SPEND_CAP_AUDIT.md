# Cloud Run Spend Cap & Automated Killswitch Audit (Phase 3.4.1)
## Critical Forensic Audit of Google Cloud Billing Latency and Spend Protection Limits

**Audit Date**: 2026-11-22  
**Target Architecture**: Google Cloud Run + Cloud Billing Alerts / Automated Killswitch  
**Classification**: `FORMAL_RETRACTION` / `REJECTED_FOR_STRICT_ZERO_COST`  

---

## 1. Executive Summary & Retraction

The Phase 3.4 delivery report claimed:
> *"The approved cloud execution target is Google Cloud Run with an Automated Spending Freeze Killswitch (a Cloud Function that terminates the Cloud Run service if billable spend exceeds $0.00 with zero financial risk)."*

A technical audit of Google Cloud Billing infrastructure, pub/sub notification pipelines, and resource tear-down semantics reveals that **this claim is technically incorrect and misleading**.

Google Cloud **does not offer an instantaneous, zero-latency $0.00 hard stop**. Unlinking billing or deleting a service programmatically is subject to telemetry delays, cannot undo charges accrued during ingestion lag, and cannot guarantee zero financial exposure.

Therefore, the claim that Cloud Run possesses a "guaranteed zero-spend killswitch terminating at $0.00" is **FORMALLY RETRACTED**. Cloud Run is **REJECTED** as a production compute runtime under PromptIQ's strict ₹0 / zero-credit-card requirement.

---

## 2. Technical Vulnerabilities of the "Automated Killswitch" Pattern

The proposed killswitch architecture relies on:
`Resource Usage` ➔ `Cloud Billing Data Aggregation` ➔ `Pub/Sub Alert` ➔ `Cloud Function` ➔ `Disable Billing / Delete Service`.

Each link in this chain introduces fatal vulnerabilities for a strict zero-dollar system:

### 2.1 The Ingestion Latency Gap (Up to 24 Hours)
- Google Cloud Billing metrics are **not real-time**. Telemetry pipelines ingest, aggregate, and rate usage with delays ranging from **several hours up to 24+ hours**.
- **The Spend Avalanche Risk**: If an unexpected surge in traffic or a runaway background job occurs, hundreds of dollars of compute can be consumed and recorded hours before the Pub/Sub alert event is ever fired.
- Setting a budget threshold at $0.01 or $1.00 will not prevent this usage from being billed.

### 2.2 In-Flight Requests Cannot Be Frozen at $0.00
- Disabling the billing account or deleting a Cloud Run service does not instantly abort connections midway through execution. In-flight requests complete or time out, accruing compute seconds that are added to the billing ledger.

### 2.3 Persistent Resources Continue Incurring Costs
- Cloud Run requires container images stored in **Google Artifact Registry** or **Container Registry**.
- Storage of container images, logs in Cloud Logging, secrets in Secret Manager, and network egress are billed independently. Unlinking billing can leave an unpaid balance or transition the project into a debt-collection state.

### 2.4 Credit Card Mandate
- Google Cloud Platform requires a **valid credit card** to activate any Cloud Billing account.
- If billable usage exceeds the free allocation, Google will charge the card automatically. There is no native cardless mode for production Cloud Run deployments.

---

## 3. Native Spend Caps vs. General Budgets

| Google Cloud Mechanism | How It Works | Does It Guarantee $0.00 Hard Stop? |
|---|---|---|
| **Cloud Billing Budget Alerts** | Sends email or Pub/Sub message when spend passes 50%, 90%, 100%. | **NO**. Informational only; services keep running. |
| **Pub/Sub DIY Killswitch** | Function calls `projects.updateBillingInfo` to detach billing. | **NO**. Defeated by billing ingestion latency; breaks project. |
| **Native Spend Caps (Preview/Select)** | Available only for specific AI APIs (Gemini API, Firebase AI). | **NO**. Does not apply to Cloud Run compute, networking, or storage. |

---

## 4. Architectural Directive for Phase 3.4.1

1. **Strictly Prohibit Provisioning**:
   - `terraform apply` must **NEVER** be executed.
   - No Google Cloud projects, billing accounts, or Cloud Run services may be provisioned.
2. **Document Cloud Run Ineligibility**:
   - Cloud Run is ineligible for an operator seeking a strictly cardless, risk-free ₹0 deployment.
   - Any deployment requiring credit card entry must be explicitly authorized by the operator with full acknowledgment of billing latency risks.
