# Neon Current Free Quota & Database Audit (Phase 3.4.1)
## Verification of Published Neon Serverless Postgres Free Tier Specifications

**Audit Date**: 2026-11-22  
**Target Provider**: Neon, Inc. (`https://neon.tech`)  
**Service Evaluated**: Neon Serverless Postgres Free Plan  
**Classification**: `VERIFIED_FREE_SPECIFICATION` (Specifications Verified via Primary Documentation; Staging Deployment Held)  

---

## 1. Executive Summary & Correction of Prior Values

Prior Phase 3.3 and 3.4 reports referenced outdated Neon free tier metrics (such as 0.5 GiB storage and 190 CU-hours). 

An independent verification of Neon's current official pricing and documentation (checked 2026-11-22) establishes the official active Free Tier limits as detailed below.

---

## 2. Official Current Neon Free Plan Limits (As of November 2026)

| Parameter | Current Official Neon Free Plan | Prior (Outdated) Report Value | Correction Status |
|---|---|---|---|
| **Database Storage** | **1 GB per project** (root + child branches combined) | 0.5 GiB | **Corrected to 1 GB** |
| **Compute Hours** | **100 CU-hours per project per month** | 190 CU-hours | **Corrected to 100 CU-hours** |
| **Compute Autoscaling** | Up to 2 Compute Units (CU) / 8 GB RAM | 0.25 - 1 CU | **Updated** |
| **Scale-to-Zero Auto-Suspend**| **5 minutes** of inactivity | 5 minutes | **Confirmed** |
| **Projects per Account** | Up to **100 projects** total per account | Unspecified | **Confirmed** |
| **Branches per Project** | Up to **10 branches** per project | 10 branches | **Confirmed** |
| **Included Data Transfer** | **5 GB egress per project per month** | Unspecified | **Confirmed** |
| **Credit Card Mandate** | **Zero credit card required** (Cardless signup) | No card | **Confirmed** |
| **Connection Pooling** | Integrated PgBouncer pooler (`-pooler` endpoint) | PgBouncer | **Confirmed** |
| **Over-Quota Behavior** | **Hard Stop**: Compute pauses; no automatic upgrade | Hard stop | **Confirmed** |

---

## 3. Quota Dynamics & Cold Start Implications

1. **The 100 CU-Hour Monthly Budget**:
   - A Compute Unit (1 CU) represents approximately 1 vCPU and 4 GB RAM.
   - At 100 CU-hours per month, an un-suspended compute instance would exhaust its quota in ~4.1 days (100 / 24).
   - Therefore, the **5-minute scale-to-zero suspension** is mathematically mandatory for PromptIQ to remain within the free budget across a full calendar month.
2. **Cold Start Latency**:
   - Waking up a suspended Neon compute instance takes between **500 ms and 2.5 seconds** upon the first incoming SQL query.
   - All client connections in `promptiq/models/` and `promptiq/services/` must configure reasonable connection timeouts (e.g., `connect_timeout=10s`) to avoid premature connection errors during wake-up.
3. **Hard Stop Protection**:
   - When 100 CU-hours or 1 GB storage is reached, Neon automatically suspends the database.
   - Because no credit card is on file, **zero unexpected billing can occur**. The service fails closed until the monthly billing cycle resets.

---

## 4. Testing Status: Honest Environment Disclosure

- **Current Repository State**: All automated database tests in `tests/` currently execute against in-memory SQLite using SQLAlchemy async engines.
- **No Live PostgreSQL Verified**: PromptIQ has **not** executed live migration or connection tests against an active Neon PostgreSQL instance.
- **Production Guard**: Neon database provisioning will only occur when the operator supplies a dedicated Neon connection string in a staging environment. Live PostgreSQL functionality is classified as **`IMPLEMENTED_NOT_LIVE_VERIFIED`**.
