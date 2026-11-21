# PromptIQ Database Feasibility and Architecture Report
## Evaluation of Cloud Database Backends for Zero-Spend, Laptop-Independent Persistence

**Revision**: 2026.11-v3.3  
**Date**: November 21, 2026  
**Auditor**: Database Architecture & Reliability Engineering Group  

---

## 1. Database Backend Comparative Evaluation

| Metric / Dimension | Neon Serverless Postgres | Supabase | Cloudflare D1 | Turso (libSQL) |
| :--- | :--- | :--- | :--- | :--- |
| **SQL Engine** | PostgreSQL 16+ (Standard) | PostgreSQL 15+ (Standard) | SQLite-compatible (Edge) | libSQL (SQLite fork) |
| **Storage Quota (Free)** | **0.5 GiB** (Hard cap) | 500 MB (Hard cap) | 5 GB | 9 GB |
| **Compute Quota (Free)** | **190 CU-hours/month** | 2 Projects | 5M reads, 100k writes/day | 1B row reads/month |
| **Credit Card Required?**| **No** (Cardless registration) | No (Cardless registration)| No (Cardless registration) | No (Cardless registration) |
| **Overage Behavior** | **Hard stop** (Refuses conn) | Hard stop | Hard stop | Hard stop |
| **Inactivity Policy** | Scales compute to 0; wakes on connection | **PAUSES project after 7 days idle** | Always active at edge | Always active at edge |
| **ORM / Protocol** | `asyncpg` / PostgreSQL wire | `asyncpg` / PostgreSQL wire | Cloudflare HTTP/D1 API | HTTP / libSQL client |
| **Feasibility Verdict** | **`APPROVED PRIMARY`** | **`REJECTED`** (7-day pause) | **`EDGE CACHE ONLY`** | **`FEASIBLE ALTERNATIVE`** |

---

## 2. In-Depth Analysis of Selected Primary: Neon Serverless Postgres

### 2.1 Why Supabase Was Rejected
While Supabase offers standard PostgreSQL, its free tier enforces a strict **7-day inactivity pause policy**. If an application or specific project does not receive database queries for seven consecutive days, the database instance is completely shut down and must be manually restored via the Supabase web dashboard. This policy directly violates PromptIQ's core requirement of **laptop-independent 24/7 service availability**.

### 2.2 Why Cloudflare D1 Was Deprioritized for Primary Storage
Cloudflare D1 is an exceptional distributed SQLite edge database. However, PromptIQ's entire persistence layer is built on SQLAlchemy 2.0 with `asyncpg`, leveraging advanced relational schemas, complex foreign key constraints, and transactional unit-of-work patterns. Migrating primary storage to D1 would require replacing the database engine with SQLite-specific SQL dialects and a non-standard HTTP-based driver, creating significant regression risk. D1 remains approved as an edge session cache.

### 2.3 Production Configuration for Neon
Neon's compute nodes automatically suspend after 5 minutes of inactivity to conserve compute hours. When a new incoming request connects, the compute node wakes up within 400–600ms.

To prevent connection drops or stale pooling errors during compute suspension:
1. **Connection Pre-Ping (`pool_pre_ping=True`)**:
   Tests the socket with a lightweight `SELECT 1` before handing the connection to the application. If the connection was terminated during idle compute sleep, SQLAlchemy transparently establishes a fresh connection.
2. **Short Pool Recycle (`pool_recycle=300`)**:
   Forces connections to recycle every 5 minutes, preventing firewall timeouts.
3. **Conservative Pool Sizing**:
   `pool_size=5`, `max_overflow=10` to avoid exhausting Neon's free tier connection limits.

---

## 3. Database Schema, Migration, and Rollback Strategy

### 3.1 Migration Management via Alembic
All database schema changes are managed through version-controlled Alembic migrations under `promptiq/db/migrations/`:
- Automatic migration execution during application startup or CI deployment:
  ```bash
  alembic upgrade head
  ```
- Reversible migration downgrade scripts for zero-downtime rollback:
  ```bash
  alembic downgrade -1
  ```

### 3.2 Data Integrity and Backup
1. **Neon Point-in-Time Recovery**: Neon maintains Write-Ahead Logs (WAL) allowing instant branching and time-travel recovery to any point in the preceding 24 hours.
2. **Automated Weekly Snapshots**: A lightweight GitHub Action executes `pg_dump` of the schema and essential project constitutions, storing encrypted artifacts without cost.
