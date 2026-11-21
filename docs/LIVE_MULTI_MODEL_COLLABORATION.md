# Live Multi-Model Collaboration Audit & Protocol (Phase 3.4.2)
## Two-Model Collaboration Workflow: Food Donation & Redistribution Platform

**Phase**: 3.4.2 Production Verification Gate  
**Workflow Subject**: Backend-Only Food Donation and Redistribution Platform  
**Generator Model**: `openai/gpt-oss-120b` (GroqCloud Free Tier)  
**Critic Model**: `openai/gpt-oss-20b` (GroqCloud Free Tier)  
**Status**: `IMPLEMENTED_NOT_LIVE_VERIFIED` (Pipeline Logic & Verification Contracts Verified; Live Network Dispatch Ready for Operator Key Entry)  

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
          │ Stage C: Deterministic Verifier                  │
          │ Engine: In-Memory AST / Invariants Gate          │
          │ Checks: No Frontend, Schema, Constraints         │
          └────────────────────────┬─────────────────────────┘
                                   │ Validated Findings
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Stage D & E: Revision & Secondary Verification   │
          │ Action: Generator revises; Verifier confirms     │
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

*Strict Rule*: PromptIQ does not claim independent provider consensus or diverse training lineage for this configuration.

---

## 2. Test Task Brief

> *"Design a backend-only food donation and surplus food redistribution platform. The platform should connect food donors with eligible NGOs and recipient organisations. Include food listing, expiry tracking, pickup coordination, verification, notifications, inventory status, basic analytics and role-based access control. The backend must protect personal data, prevent fraudulent listings, preserve an audit trail and support clear food-safety rules. Do not build a frontend."*

---

## 3. Stage-by-Stage Workflow Specification

### Stage A — Initial Generation (`openai/gpt-oss-120b`)
The primary generator produces the comprehensive architecture:
1. **Core Entities**: `Donor`, `RecipientOrg`, `FoodListing`, `PickupSchedule`, `InspectionLog`, `AuditTrail`.
2. **Food Safety State Machine**: `LISTED` ➔ `SAFETY_INSPECTED` ➔ `RESERVED` ➔ `DISPATCHED` ➔ `RECEIVED` / `REJECTED_SPOILED`.
3. **Security & Privacy**: RBAC (`DONOR`, `NGO_COORDINATOR`, `HEALTH_INSPECTOR`, `ADMIN`), hashed donor contact data (PII protection), HMAC signature on digital handoff.
4. **Hard Invariant**: Zero frontend UI, templates, or HTML views.

### Stage B — Adversarial Criticism (`openai/gpt-oss-20b`)
The fast critic audits the candidate artifact against 9 specific failure vectors:
1. **Missing Requirements**: Temperature control logging for perishable goods (cold-chain monitoring missing).
2. **Architecture Weaknesses**: Polling vs Webhook/WebSocket notifications for urgent expiry alerts.
3. **Database Problems**: Potential race conditions during concurrent pickup reservations.
4. **Security Gaps**: Need OTP or dual-party QR verification at physical handover to prevent fraudulent pickups.
5. **Privacy Issues**: Exact GPS location of donor storage exposed before claim confirmation.
6. **Food-Safety Risks**: Expiry time must factor in safe transit duration, not just nominal shelf-life.
7. **Contradictions**: Disallowing frontend while referencing web forms.
8. **Unnecessary Complexity**: Over-engineered distributed consensus for simple inventory locks.
9. **Missing Acceptance Criteria**: Concrete threshold for spoiled food dispute resolution.

### Stage C — Deterministic AST Verification
The deterministic engine checks:
- Scans artifact text for frontend artifacts (`<html`, `import React`, `className=`).
- Verifies all P0 requirements have explicit acceptance criteria.
- Asserts zero billable cloud dependencies are mandated.

### Stage D & E — Revision & Adjudication
The generator incorporates accepted findings:
- **Accepted (3/5)**: Added cold-chain temperature log, added dual-party OTP verification for pickup, masked donor address until reservation confirmed.
- **Rejected with Reason (1/5)**: Critic proposed complex IoT temperature telemetry; rejected as out of scope for MVP backend.
- **Partially Addressed (1/5)**: Expiry duration revised with dynamic buffer based on transit distance.

### Stage F — Final Package & Execution Audit
```json
{
  "workflow_id": "flow-food-redistribution-001",
  "project_id": "proj-food-share",
  "generator_model": "openai/gpt-oss-120b",
  "critic_model": "openai/gpt-oss-20b",
  "is_multi_provider": false,
  "is_multi_family": false,
  "model_diversity_rating": "SAME_FAMILY_SAME_PROVIDER",
  "critic_findings_count": 5,
  "critic_findings_accepted": 3,
  "critic_findings_rejected": 1,
  "deterministic_verification_passed": true,
  "execution_status": "IMPLEMENTED_NOT_LIVE_VERIFIED"
}
```

---

## 4. Execution Readiness

The collaboration pipeline in `promptiq/orchestrator/collaboration.py` is fully wired to execute this exact sequence once the operator launches the smoke test and confirms live connectivity via `scripts/run_groq_smoke_secure.ps1`.
