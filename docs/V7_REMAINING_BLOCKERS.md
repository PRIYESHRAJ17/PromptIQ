# PROMPTIQ V7 — REMAINING BLOCKERS & ARCHITECTURAL DISCLOSURES

## 1. Executive Summary

In adherence to PromptIQ's non-negotiable principle of **absolute factual honesty and zero false completion claims**, this document records the remaining blockers, environment limitations, and architectural non-deliverables that prevent PromptIQ from achieving a 10.0 score.

---

## 2. Active External Blockers

### 2.1 Cloud Production Deployment (`BLOCKED`)
- **Status**: `BLOCKED` (Score: 1.0 / 10).
- **Root Cause**: The prompt and project constitution dictate that PromptIQ must be 100% free to users with centrally hosted infrastructure. However, reputable cloud platforms (AWS, GCP, Azure, Fly.io) require credit cards for container execution or terminate free tier VMs arbitrarily. To prevent accidental paid billing or violation of the ₹0 user invariant, live cloud production deployment remains blocked until a zero-cost, cardless hosting envelope is formally contracted.
- **Remediation Plan**: Identify grant-funded community infrastructure or dedicated cardless zero-price sponsors.

### 2.2 Local PostgreSQL Live Daemon (`BLOCKED`)
- **Status**: `BLOCKED / NOT TESTED ON LIVE DAEMON` (Score: 5.5 / 10).
- **Root Cause**: The developer workstation environment lacks an active PostgreSQL service listening on port 5432 and lacks a running Docker daemon.
- **Verified Mitigation**:
  - All database models, foreign keys, and JSONB columns are compiled and verified against the PostgreSQL 16 dialect using SQLAlchemy.
  - Alembic migrations `0001_initial_schema`, `0002_user_and_workspace_quotas`, and `0003_pg16_hardening` compile cleanly.
  - Development and automated integration test suites execute against the asynchronous SQLite engine (`aiosqlite`).
- **Remediation Plan**: Provision a containerized PostgreSQL 16 service in a CI environment with Docker support.

---

## 3. Explicit Invariant Exclusions (Out of Scope by Design)

### 3.1 Strictly No Website Frontend
- **Status**: `EXCLUDED BY INVARIANT`.
- **Constraint**: The Project Constitution explicitly forbids generating React, Next.js, HTML, CSS, frontend UI components, or dashboards until the backend achieves release readiness. All backend APIs, schemas, and MCP tools are structured to support future frontend client consumption without architectural rework.

### 3.2 Anti-BYOK & Zero User API Keys
- **Status**: `EXCLUDED BY INVARIANT`.
- **Constraint**: Never prompt users for API keys. Zero paid inference routes. No user-facing BYOK interfaces.

### 3.3 Zero Local Inference
- **Status**: `EXCLUDED BY INVARIANT`.
- **Constraint**: PromptIQ is a hosted cloud service; local Ollama, llama.cpp, or local GPU dependencies are rejected.
