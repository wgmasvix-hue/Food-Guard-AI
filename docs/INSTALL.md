# Installation Guide

## 1. Prerequisites

- Docker & Docker Compose (v2)
- (Optional, for local dev without Docker) Node.js 20+, Python 3.12+, PostgreSQL 16

## 2. Quick Start (Docker)

```bash
git clone <repo-url> food-guard-ai
cd food-guard-ai
cp .env.example .env
```

Edit `.env` and set at minimum:
- `SECRET_KEY` — a long random string (`openssl rand -hex 32`)
- `POSTGRES_PASSWORD` — a strong password
- `NEXT_PUBLIC_API_URL` — the public URL the browser will use to reach the API (defaults to `http://localhost:8000/api/v1`)

Start the stack:

```bash
docker compose up -d --build
```

This starts:
- `db` — PostgreSQL 16
- `api` — FastAPI backend (runs Alembic migrations automatically on boot, then Uvicorn)
- `web` — Next.js frontend
- `nginx` — reverse proxy on port 80, routes `/api/*` to the backend and everything else to the frontend

Load demo data (company, users, a sample HACCP plan, GMP checklist, temperature units):

```bash
docker compose exec api python -m app.db.seed
```

Visit:
- App: http://localhost
- API docs (Swagger UI): http://localhost:8000/api/v1/docs
- API docs (ReDoc): http://localhost:8000/api/v1/redoc

Demo logins (after seeding):
| Role | Email | Password |
|---|---|---|
| Company Admin | admin@demo.foodguard.ai | FoodGuard!234 |
| QA Manager | qa.manager@demo.foodguard.ai | FoodGuard!234 |
| Food Safety Officer | fso@demo.foodguard.ai | FoodGuard!234 |
| Production Supervisor | supervisor@demo.foodguard.ai | FoodGuard!234 |
| Auditor | auditor@demo.foodguard.ai | FoodGuard!234 |
| Operator | operator@demo.foodguard.ai | FoodGuard!234 |
| Super Admin (platform) | superadmin@foodguard.ai | FoodGuard!234 |

## 3. Enabling the AI Assistant (Ollama)

The AI Assistant is optional and disabled gracefully if no model is running. To enable it locally:

```bash
docker compose --profile ai up -d ollama
docker compose exec ollama ollama pull llama3.2
```

The backend talks to Ollama via `OLLAMA_BASE_URL` / `OLLAMA_MODEL` in `.env`. To point at a different model, change `OLLAMA_MODEL` and re-pull, or set `AI_PROVIDER=disabled` to turn the assistant off entirely.

To use a different AI backend later (cloud LLM), implement `app.services.ai.base.AIProvider` and register it in `app.services.ai.factory.get_ai_provider()` — no other code changes needed.

## 4. Local Development (without Docker)

### Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp ../.env.example ../.env   # or export the vars directly
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Run tests (uses an in-memory SQLite database, no Postgres needed):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if the API isn't at `http://localhost:8000/api/v1`.

## 5. Database Migrations

Migrations live in `backend/alembic/versions/`. After changing a SQLAlchemy model:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Review the generated migration before committing — autogenerate is a starting point, not a guarantee.

## 6. Production Notes

- Set `ENVIRONMENT=production` and a strong, unique `SECRET_KEY`.
- Terminate TLS at Nginx: mount certificates into `nginx/certs` and uncomment the HTTPS `server` block in `nginx/nginx.conf`.
- Put PostgreSQL and file uploads (`/data/uploads` volume) on durable, backed-up storage.
- Restrict `BACKEND_CORS_ORIGINS` to your real frontend domain(s).
- Tune `RATE_LIMIT_PER_MINUTE` / `AUTH_RATE_LIMIT_PER_MINUTE` for your traffic.
- Run behind a process supervisor / orchestrator (Docker Swarm, Kubernetes, ECS, etc.) for zero-downtime deploys; the containers here are stateless aside from the `db`, `pgdata`, and `api-uploads` volumes.
