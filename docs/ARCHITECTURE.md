# Architecture

## Overview

FoodOS is a modular monolith today, structured so individual modules (HACCP, GMP, Temperature, etc.) can be split into services later without a rewrite. The system is multi-tenant at the **company** level: every row of business data carries a `company_id`, and API endpoints scope all reads/writes to `current_user.company_id` (except `super_admin`, which can act across companies for platform administration).

```
┌─────────────┐      HTTPS       ┌────────────┐
│   Browser   │ ───────────────▶ │   Nginx    │
└─────────────┘                  └─────┬──────┘
                                        │
                    ┌───────────────────┼────────────────────┐
                    ▼                                         ▼
            ┌───────────────┐                         ┌───────────────┐
            │  Next.js (web) │                         │ FastAPI (api) │
            └───────────────┘                         └───────┬───────┘
                                                                │
                                          ┌─────────────────────┼─────────────────────┐
                                          ▼                     ▼                     ▼
                                   ┌────────────┐       ┌──────────────┐      ┌──────────────┐
                                   │ PostgreSQL │       │ Ollama (AI)  │      │ File storage │
                                   └────────────┘       └──────────────┘      │ (uploads vol)│
                                                                              └──────────────┘
```

## Backend layout (`backend/app`)

```
app/
├── main.py              FastAPI app, middleware, exception handlers, router mount
├── core/                 Config, JWT/password hashing, RBAC, rate limiting, audit logging
├── db/                    Engine/session, declarative base, seed script
├── models/                SQLAlchemy ORM models (one file per domain area)
├── schemas/                Pydantic request/response schemas
├── api/v1/endpoints/    One router per module, mounted under /api/v1
└── services/
    ├── ai/                 Modular AI provider interface + Ollama implementation
    ├── compliance.py    Compliance score calculation
    └── reports.py         ReportLab PDF generation
```

### Request flow

1. `app/main.py` wires CORS, rate limiting (`slowapi`), and mounts `api_router` at `/api/v1`.
2. Each endpoint depends on `get_current_active_user` (JWT-authenticated) and, where relevant, `require_min_role` / `require_roles` from `core/rbac.py` to enforce the role hierarchy.
3. Endpoints scope queries by `current_user.company_id`, so tenants never see each other's data (super_admin excepted).
4. Domain writes that represent a food-safety event — a CCP monitoring reading outside limits, a temperature log out of range, a failed critical GMP checklist item — **automatically open a `CorrectiveAction`** row linking back to the source record (`source` / `source_reference_id`). This is the core cross-module integration point.

### Data model

All tables use string UUID primary keys (portable across Postgres and SQLite, which the test suite uses in-memory). Key relationships:

- `Company` → `Facility` → `Department` / `Employee`
- `HaccpPlan` → `Hazard`, `CCP` → `MonitoringRecord`, `HaccpReview`
- `ChecklistTemplate` → `ChecklistTemplateItem`; `Checklist` → `ChecklistItem`
- `TemperatureUnit` → `TemperatureLog`
- `Audit` → `AuditFinding`
- `Document` → `DocumentVersion` (version history, including AI-generated text content)
- `CorrectiveAction` — the shared sink for deviations raised by HACCP, GMP, Temperature, and Audit modules
- `AIConversation` → `AIMessage` — chat history for the AI assistant

See `backend/alembic/versions/` for the full schema, or `backend/app/models/` for the SQLAlchemy source of truth.

### AI provider abstraction

`app/services/ai/base.py` defines a minimal `AIProvider` protocol (`complete()`, `is_available()`). `OllamaProvider` implements it against a local/self-hosted Ollama instance. `get_ai_provider()` (`services/ai/factory.py`) is the single place that decides which implementation to use, driven by `AI_PROVIDER` in settings — swapping in a cloud model later means adding one class and one branch, with zero changes to endpoints or prompts.

### Compliance score

`services/compliance.py` blends four rolling 30-day signals into a single 0-100 score shown on the dashboard: GMP checklist pass rate (30%), temperature-within-limits rate (30%), corrective actions not overdue (25%), audit findings closed (15%). Each signal defaults to 100 with no data, so new tenants start at 100 rather than being penalized for an empty history.

## Frontend layout (`frontend/src`)

```
src/
├── app/                    Next.js App Router
│   ├── (auth)/               Login, register, forgot/reset password (public)
│   ├── dashboard/            Protected pages, one folder per module
│   ├── haccp/, gmp/, temperature/, corrective-actions/, audits/, documents/, ai-assistant/, settings/
├── components/
│   ├── ui/                  Hand-rolled shadcn-style primitives (Button, Card, Dialog, ...)
│   └── layout/               Sidebar, Topbar, ProtectedShell (auth guard + chrome)
└── lib/
    ├── api-client.ts        Axios instance, JWT attach + silent refresh-on-401, blob download helper
    ├── auth-context.tsx      React context wrapping login/register/logout/me
    ├── query-provider.tsx   React Query client provider
    └── types.ts               Shared TypeScript types mirroring the backend schemas
```

Data fetching uses React Query; forms are plain controlled components (React Hook Form is available as a dependency for more complex forms as the app grows). Auth tokens are stored in `localStorage`; the Axios response interceptor transparently refreshes an expired access token using the refresh token and retries the original request once.

## Security

- **Authentication**: JWT access (short-lived) + refresh (long-lived) tokens, `python-jose` + `passlib[bcrypt]`.
- **Authorization**: Role-based, enforced server-side via FastAPI dependencies (`core/rbac.py`); the frontend never gates access on its own, it just reflects what the API allows.
- **Rate limiting**: `slowapi`, tighter limits on auth endpoints (`AUTH_RATE_LIMIT_PER_MINUTE`) to slow credential stuffing.
- **Input validation**: Pydantic v2 schemas on every request body; SQLAlchemy parameterizes all queries (no raw SQL string interpolation).
- **Audit logging**: `core/logging.py` writes security-relevant actions (login, register, password changes/resets) to `system_logs`.
- **Multi-tenancy isolation**: every query is filtered by `company_id` server-side; there is no tenant selector on the frontend that could be tampered with to cross tenants.

## Why this shape scales into a full Manufacturing ERP

The domain boundaries chosen here — Company/Facility, Product/Batch/Ingredient/Supplier, and a generic `CorrectiveAction` sink — are the same primitives a broader ERP needs. Adding **Inventory**, **Production Planning**, **Recipe Management**, **Traceability/Recall**, **Purchasing**, **Sales**, etc. means adding new model/schema/endpoint modules that reference the existing `Company`, `Facility`, `Product`, and `Batch` tables rather than redesigning the tenancy or auth model. The AI provider interface, PDF report service, and RBAC dependency pattern are all reusable as-is for new modules.

Not yet implemented, but the schema and module boundaries anticipate: Inventory Management, Production Planning, Recipe Management, Food Costing, Nutrition Analysis, Label Generation, Traceability, Product Recall, Warehouse Management, Maintenance, Purchasing, Sales, IoT Sensors, Barcode/QR Scanning, Offline Sync, and native Mobile Apps.
