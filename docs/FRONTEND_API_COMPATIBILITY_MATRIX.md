# PROMPTIQ FRONTEND-BACKEND API COMPATIBILITY MATRIX
## Type-Level Contract Reconciliation & Wire Parity

---

## 1. Overview

The PromptIQ Web Application connects to the FastAPI backend via `frontend/src/lib/api.ts`. All TypeScript types in `frontend/src/types/index.ts` map 1:1 to PromptIQ's Pydantic schemas in `promptiq/api/models.py` and `promptiq/core/`.

---

## 2. Endpoint & Type Mapping Matrix

| Frontend Client Method | HTTP Verb | Backend Endpoint | Pydantic Schema | TypeScript Interface | Parity Status |
|---|---|---|---|---|---|
| `api.getProjects()` | `GET` | `/api/v1/projects` | `List[ProjectResponse]` | `Project[]` | Full Parity |
| `api.getProject(id)` | `GET` | `/api/v1/projects/{id}` | `ProjectResponse` | `Project` | Full Parity |
| `api.createProject(data)` | `POST` | `/api/v1/projects` | `ProjectCreateRequest` | `Omit<Project, 'id' \| 'created_at'>` | Full Parity |
| `api.getConstitution(id)` | `GET` | `/api/v1/projects/{id}/constitution` | `ConstitutionResponse` | `ProjectConstitution` | Full Parity |
| `api.proposeConstitutionChange()` | `POST` | `/api/v1/projects/{id}/constitution/propose` | `ConstitutionProposeRequest` | `Record<string, unknown>` | Full Parity |
| `api.createWorkflowJob()` | `POST` | `/api/v1/jobs` | `JobCreateRequest` | `WorkflowJob` | Full Parity |
| `api.getWorkflowJob(id)` | `GET` | `/api/v1/jobs/{id}` | `JobResponse` | `WorkflowJob` | Full Parity |
| `api.runAutopsy(prompt)` | `POST` | `/api/v1/critic/autopsy` | `AutopsyRequest` -> `AutopsyResult` | `AutopsyResponse` | Full Parity |
| `api.getQuotaStatus()` | `GET` | `/api/v1/governor/quota-status` | `QuotaStatusResponse` | `QuotaStatus` | Full Parity |
| `api.getHealth()` | `GET` | `/health` | `HealthCheckResponse` | `{ status, version, zero_price_policy }` | Full Parity |

---

## 3. Data Integrity & Provenance Fields

The frontend surfaces all backend metadata without flattening or data loss:
- **Requirement Provenance**: `user_provided`, `file_extracted`, `connected_source`, `inferred`, `research_backed`, `unknown`, `conflicting`.
- **Decision Supersession**: `supersedes` foreign keys linking revised decisions back to their historical precursors (e.g. `DEC-002` superseding `DEC-001`).
- **Exact Research Offsets**: `char_offset_start` and `char_offset_end` preserved and displayed in the Evidence Inspector.
- **Autopsy Defect Categories**: 21 categories with severity rankings, evidence quotations, consequences, and release blocking flags (`blocks_release: boolean`).
