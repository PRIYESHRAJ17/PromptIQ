# PromptIQ Database Architecture & PostgreSQL Verification Status

**Audit Date**: November 21, 2026  
**Auditor**: Lead Systems & Database Architect  
**ORM Framework**: SQLAlchemy 2.0 Async (`AsyncEngine`, `AsyncSession`)  
**Migration Engine**: Alembic Async (`alembic/`)  

---

## 1. Honest Verification Status Disclosure

To prevent false claims or inaccurate compliance declarations, PromptIQ explicitly documents the testing environment reality on the operator workstation:

| Target Database | Testing Environment Reality | Verification Status | Evidence & Test Coverage |
| :--- | :--- | :--- | :--- |
| **SQLite (Async)** | Local Developer Workstation (Windows, Python 3.13) | **`VERIFIED`** | **100% (75/75 tests passing)**. Fully exercises async transactions, UUID mixins, timestamp mixins, cross-tenant foreign key constraints, and JSON column types. |
| **Alembic Migrations** | Local Migrations Engine (`alembic upgrade head`) | **`VERIFIED`** | Verified programmatic upgrade and downgrade in `tests/test_database_migrations.py`. Validates SQL DDL generation. |
| **PostgreSQL / Neon Serverless** | Docker daemon NOT running on workstation PATH; local PostgreSQL engine not installed | **`IMPLEMENTED_NOT_LIVE_VERIFIED`** | Code written with `asyncpg` compatibility, verified Alembic PostgreSQL DDL scripts, `pool_pre_ping=True`, and `pool_recycle=300`. Live remote connectivity requires deployed Neon connection string. |

---

## 2. Serverless PostgreSQL Hardening (Neon Serverless Recovery)

Serverless PostgreSQL databases like Neon autosuspend their compute instances after a period of inactivity (typically 5 minutes) to conserve resources. When a new query arrives, the compute instance resumes, but existing socket connections in the connection pool may have been closed by the remote gateway.

PromptIQ implements connection resilience in `promptiq/core/database.py`:

```python
engine = create_async_engine(
    database_url,
    echo=settings.DATABASE_ECHO,
    future=True,
    # Recovers from Neon serverless compute suspend/resume
    pool_pre_ping=True,
    # Refreshes idle connections before remote firewalls drop sockets
    pool_recycle=300,
)
```

1. **`pool_pre_ping=True`**: Executes a lightweight test statement (`SELECT 1`) on checked-out connections before issuing queries. If the connection was terminated during Neon compute sleep, the engine transparently re-establishes a fresh connection without raising an unhandled `ConnectionResetError` to the user.
2. **`pool_recycle=300`**: Cycles pooled connections every 5 minutes (300 seconds), preventing stale connections from exceeding remote firewall NAT timeouts.

---

## 3. Cross-Tenant Isolation Enforcement

Database schema enforces multi-tenant isolation at the data tier:
1. Every business entity (`Project`, `ProjectConstitution`, `ResearchRecord`, `EvaluationSuite`, `Checkpoint`) carries an indexed `workspace_id` and `created_by_user_id`.
2. Database queries filter by `workspace_id == user.default_workspace_id`.
3. IDOR attacks are systematically tested across all entity types in `tests/test_auth_and_tenancy.py::test_exhaustive_cross_tenant_idor_enforcement`.
