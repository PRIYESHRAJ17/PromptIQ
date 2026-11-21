# Live Multi-Model Collaboration Audit & Protocol (Phase 3.4.2)
## Two-Model Collaboration Workflow: Food Donation & Redistribution Platform

**Phase**: 3.4.2 Production Verification Gate  
**Workflow Subject**: Backend-Only Food Donation and Redistribution Platform  
**Generator Model (Stage A & D)**: `openai/gpt-oss-120b` (GroqCloud Free Tier, Verified Smoke Req: `req_01m7zr9k96ethbpvc22gc1hddj`)  
**Critic Model (Stage B)**: `openai/gpt-oss-20b` (GroqCloud Free Tier, Verified Smoke Req: `req_01m7zrbddcea793zn4xvrhtskw`)  
**Deterministic Verifier (Stage C & E)**: PromptIQ Internal Invariants & AST Verifier Engine  
**Live Connectivity Status**: `LIVE_VERIFIED_FREE` (Both models verified via operator console & genuine HTTP 200 responses)  
**Execution Pipeline Status**: `COLLABORATION_READY`  

---

## 1. Multi-Model Topology & Mandatory Diversity Disclosure

```
       [ Task: Food Donation & Redistribution Backend Platform ]
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Stage A: Generator (OpenAI GPT-OSS 120B)         │
          │ Provider: GroqCloud (Free Tier)                  │
          │ Role: PROMPT_ENGINEER / System Architecture      │
          └────────────────────────┬─────────────────────────┘
                                   │ Candidate Specification
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Stage B: Critic (OpenAI GPT-OSS 20B)             │
          │ Provider: GroqCloud (Free Tier)                  │
          │ Role: CRITIC (Adversarial Engineering Review)    │
          └────────────────────────┬─────────────────────────┘
                                   │ Critique Findings Ledger
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Stage C: Candidate Deterministic Verification    │
          │ Engine: In-Memory Invariants Gate                │
          │ Checks: No Frontend (<html, React, CSS), Schema  │
          └────────────────────────┬─────────────────────────┘
                                   │ Validated Findings
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Stage D: Specialist Revision (GPT-OSS 120B)      │
          │ Action: Generator resolves critic findings       │
          └────────────────────────┬─────────────────────────┘
                                   │ Revised Architecture
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Stage E: Final Deterministic Verification        │
          │ Action: Deterministic check & Resolution Ledger  │
          │ Breakdown: Resolved, Rejected with Reason, Open  │
          └────────────────────────┬─────────────────────────┘
                                   │ Final Approved Package
                                   ▼
          [ Final Deliverable & Multi-Model Execution Audit ]
```

### Mandatory Architectural Disclosure:
- **`is_multi_model`**: `True` (Two distinct models participate in generation and review)
- **`is_multi_family`**: **`False`** (Both models are members of the `gpt-oss` architecture)
- **`is_multi_provider`**: **`False`** (Both execute via GroqCloud infrastructure)
- **`model_diversity_rating`**: **`SAME_FAMILY_SAME_PROVIDER`**
- **`consensus_status`**: **`same_family_intra_provider_disclosed`**

*Strict Rule*: PromptIQ does not claim independent provider consensus or diverse training lineage for this configuration. Both models share provider and family lineage, but represent distinct parameter scales (120B reasoning vs 20B fast review).

---

## 2. Test Task Brief

> *"Design a backend-only Food Donation and Surplus Food Redistribution Platform. It must connect donors with eligible NGOs and recipient organisations. Include: Food listings, Expiry tracking, Pickup coordination, Organisation verification, Notifications, Inventory management, Role-based access control, Food-safety rules, Fraud prevention, Audit history, Data privacy, Acceptance criteria. Do not create a frontend."*

---

## 3. Stage-by-Stage Workflow Specification

### Stage A — Initial Generation (`openai/gpt-oss-120b`)
The primary generator produces the comprehensive backend architecture:
1. **Core Entities**: `Donor`, `RecipientOrg`, `FoodListing`, `PickupSchedule`, `InspectionLog`, `AuditTrail`.
2. **Food Safety State Machine**: `LISTED` ➔ `SAFETY_INSPECTED` ➔ `RESERVED` ➔ `DISPATCHED` ➔ `RECEIVED` / `REJECTED_SPOILED`.
3. **Security & Privacy**: RBAC (`DONOR`, `NGO_COORDINATOR`, `HEALTH_INSPECTOR`, `ADMIN`), hashed donor contact data (PII protection), HMAC signature on digital handoff.
4. **Hard Invariant**: Zero frontend UI, templates, or HTML views.

### Stage B — Adversarial Criticism (`openai/gpt-oss-20b`)
The fast critic audits the candidate artifact against 10 specific failure vectors:
1. **Missing Requirements**: Cold-chain temperature tracking, perishability buffers.
2. **Architecture Weaknesses**: Polling vs Webhook/WebSocket notification bottlenecks.
3. **Database Problems**: Race conditions during concurrent pickup reservations.
4. **Security Vulnerabilities**: Need dual-party OTP/QR verification to prevent fraudulent pickups.
5. **Data Privacy Risks**: Precise donor address leakage before recipient confirmation.
6. **Food-Safety Omissions**: Expiry window calculation factoring transit duration.
7. **Unsupported Assumptions**: Reliance on unverified donor self-reporting.
8. **Contradictions**: Disallowing frontend while referencing web client mechanisms.
9. **Missing Acceptance Criteria**: Verifiable SLA for dispute resolution.
10. **Invariant Violations**: Verifying strictly zero frontend UI code.

### Stage C — Candidate Deterministic Verification
The deterministic engine checks `candidate_text`:
- Scans artifact text for forbidden frontend artifacts (`<html`, `import React`, `className=`).
- Asserts output is non-empty.
- Confirms candidate baseline validity before passing to revision.

### Stage D — Specialist Revision (`openai/gpt-oss-120b`)
The generator receives the original task, initial candidate architecture, and the critic autopsy findings:
- Resolves valid critic findings (e.g., adding cold-chain temperature monitoring, dual-party OTP pickup handoff, masked donor addresses, and explicit dispute resolution acceptance criteria).
- Documents rejected recommendations with technical rationale (e.g., omitting high-cost IoT hardware telemetry in favor of mobile app driver logs).
- Re-asserts backend-only constraint.

### Stage E — Final Deterministic Verification & Resolution Breakdown
The deterministic engine checks `revised_text`:
- Re-scans for forbidden frontend patterns and non-empty output.
- Classifies critic findings into:
  - **`resolved`**: Concrete mechanisms incorporated into the revised architecture.
  - **`rejected_with_reason`**: Findings evaluated and explicitly rejected with engineering rationale.
  - **`unresolved`**: Any finding not addressed in the revised architecture.

---

## 4. Operator Execution Runbook

To execute the live 5-stage collaboration workflow without persisting credentials or writing keys to disk:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_groq_collaboration_secure.ps1 -OptIn -ConfirmFreePlan
```

This runner:
1. Prompts for the Groq API key with masked input (`Read-Host -AsSecureString`).
2. Sets process environment variables in memory:
   - `$env:GROQ_API_KEY = $plainKey`
   - `$env:PROMPTIQ_OPERATOR_FREE_TIER_CONFIRMED = "true"`
   - `$env:MANAGED_INFERENCE_ALLOW_MOCK_FALLBACK = "false"`
   - `$env:MANAGED_INFERENCE_PRIMARY_ROUTE = "groq"`
3. Invokes `promptiq.orchestrator.collaboration_cli --opt-in --profile STANDARD`.
4. Executes the 5 stages and prints step-by-step metadata, request IDs, latencies, and resolution breakdown.
5. Saves the full execution record to `docs/LIVE_COLLABORATION_EXECUTION_RESULTS.json`.
6. Wipes all credential buffers and environment variables in a guaranteed `finally` block.
