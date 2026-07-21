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

## 6. Production Deployment (one server, real domain, HTTPS)

`deploy/install.sh` automates a full production install on a fresh (or shared)
Ubuntu/Debian server that already has Docker + the Compose plugin: it clones
the repo, generates `.env` with random secrets, brings the stack up, obtains
a Let's Encrypt certificate via the HTTP-01 webroot challenge, switches nginx
to HTTPS, sets up daily certbot renewal, and seeds demo data.

```bash
sudo DOMAIN=foodguard.yourdomain.com EMAIL=you@yourdomain.com bash deploy/install.sh
```

Requirements before running it:
- The domain's DNS **A record already points at the server's public IP** (the script checks this and refuses to continue if it doesn't resolve).
- Ports **80 and 443** are free on the host (the script checks and aborts if something else is already bound — safe to run on a box hosting other apps, as long as those apps use different ports).
- You're running it as root (or via `sudo`).

It's safe to re-run: it skips secret generation if `.env` already exists, skips certificate issuance if a valid cert is already present, and the seed script no-ops if demo data already exists.

The script deploys the `claude/food-guard-ai-platform-z05ynw` branch by default (override with `BRANCH=main` once you've merged it) — review the diff and merge to `main` via a PR before treating a deployment as your production baseline long-term.

### Production notes (whether or not you use the script)

- Set `ENVIRONMENT=production` and a strong, unique `SECRET_KEY`.
- The compose file already binds `db`, `api`, and `web` to `127.0.0.1`/internal-only — nginx (80/443) is the only public surface.
- TLS is terminated at Nginx using `nginx/conf.d/default.conf.ssl.template`, rendered to `nginx/conf.d/default.conf` with the real domain substituted in (this file is gitignored — it's generated per-deployment, not committed).
- Put PostgreSQL and file uploads (`/data/uploads` volume) on durable, backed-up storage.
- Restrict `BACKEND_CORS_ORIGINS` to your real frontend domain(s) — the install script does this for you.
- Tune `RATE_LIMIT_PER_MINUTE` / `AUTH_RATE_LIMIT_PER_MINUTE` for your traffic.
- Run behind a process supervisor / orchestrator (Docker Swarm, Kubernetes, ECS, etc.) for zero-downtime deploys; the containers here are stateless aside from the `db`, `pgdata`, `api-uploads`, and `certbot-etc` volumes.
