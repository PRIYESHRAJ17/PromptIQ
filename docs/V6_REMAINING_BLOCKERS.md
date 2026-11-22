# PROMPTIQ V6 — REMAINING BLOCKERS AND ENVIRONMENTAL CONSTRAINTS

## Executive Overview

PromptIQ enforces uncompromising honesty regarding operational realities. This document outlines the two remaining blockers that prevent full public cloud deployment and live PostgreSQL daemon testing on this workstation.

---

## 1. Blocker 1: Public Cloud Production Hosting

### Status: `BLOCKED`

### Root Cause
1. **Zero-Price Invariant Conflict**:
   - PromptIQ mandates that the platform must operate at **strictly ₹0 cost** with zero risk of incurring unexpected billing charges.
2. **Provider Card Requirement**:
   - Leading cloud container hosting platforms (Google Cloud Run, AWS App Runner, Fly.io, Railway) require credit card registration to provision compute or enforce billing accounts, exposing the project to the risk of surprise usage overages.
3. **Cardless Free-Tier Compute Limitations**:
   - Free-tier hosts that do not require credit cards (e.g. Render free tier, Koyeb hobby tier, Vercel serverless) have severe operational constraints:
     - Ephemeral sleep cycles (50s cold boots).
     - Strict execution timeouts (10-30s), incompatible with multi-model collaboration debates and research retrieval loops.
     - Outbound connection restrictions or background process termination.
4. **Resolution Path**:
   - Cloud deployment remains blocked until an enterprise sponsorship or isolated cardless cloud environment with hard budget-kill switches ($0.00 hard limit) is configured.

---

## 2. Blocker 2: Local PostgreSQL Live Daemon Execution

### Status: `BLOCKED (ENVIRONMENTAL)`

### Root Cause
1. **Workstation Environment**:
   - The developer environment is Windows 11 without a running PostgreSQL Windows service.
   - Network probe `Test-NetConnection 127.0.0.1 -Port 5432` confirms port 5432 is closed (connection refused).
2. **Absence of Docker Runtime**:
   - Docker Desktop / Docker CLI is not installed or available on this system (`docker : The term 'docker' is not recognized`).
3. **Dialect Verification vs Live Verification**:
   - Alembic migrations, PostgreSQL 16 dialect compilation, and SQLAlchemy schema constructs have been verified through automated unit tests.
   - However, a live TCP socket connection to a running PostgreSQL 16 server cannot be established on this machine without external software installation.
4. **Resolution Path**:
   - The platform cleanly supports SQLite (via `aiosqlite`) for development and local testing.
   - Live PostgreSQL socket verification will occur in a dedicated CI/CD pipeline equipped with a PostgreSQL service container.

---

## 3. Policy on Simulated Mocks

In accordance with PromptIQ core invariants:
- **No mock or fake connection is ever presented as a live PostgreSQL test.**
- Both blockers are recorded with full technical rationale and transparent status.
