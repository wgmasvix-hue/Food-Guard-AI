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

There are four installer scripts under `deploy/`, depending on what already
owns ports 80/443 on the target server. All four: clone/update the repo,
generate `.env` with random secrets, build and start `db`/`api`/`web`, and
seed demo data. They differ only in how HTTPS gets terminated.

| Script | Use when... |
|---|---|
| `deploy/install.sh` | Nothing else is on ports 80/443 — it runs its own nginx container and gets a cert via certbot. |
| `deploy/install-vhost.sh` | The server already runs its **own host-installed nginx** in front of other sites — it adds a vhost to that nginx and gets its own cert via certbot (with a deploy-hook so renewals reload nginx without disturbing other sites' renewal setup). |
| `deploy/install-caddy.sh` | The server already runs a **host-installed Caddy** (a systemd service, `caddy` binary on PATH) in front of other sites — it adds a site block to the existing Caddyfile. Caddy obtains its own certificate automatically — no certbot step at all. |
| `deploy/install-caddy-docker.sh` | Caddy itself runs **inside a Docker container** (e.g. tooling like ChengetAi Deploy that runs `caddy:2.x` as a container) reaching other containers by name on a shared Docker network rather than via the host's `127.0.0.1`. Attaches `api`/`web` to that same network (via `docker-compose.caddy-network.yml`) and points Caddy at them by container name — the same way it already reaches e.g. `dspace:8080`. |

Telling the host-Caddy and containerized-Caddy cases apart: `systemctl status caddy` finding a real service means host-installed (`install-caddy.sh`); `docker ps` showing a `caddy` image with 80/443 published means containerized (`install-caddy-docker.sh`). If nginx *fails to start* with "Address already in use", something else (check `ss -ltnp | grep -E ':80 |:443 '`) already holds those ports — don't assume it's nginx's config that's broken.

### Fresh server (dockerized nginx)

```bash
sudo DOMAIN=foodguard.yourdomain.com EMAIL=you@yourdomain.com bash deploy/install.sh
```

### Shared server already running nginx

```bash
sudo DOMAIN=foodguard.yourdomain.com EMAIL=you@yourdomain.com \
  API_HOST_PORT=8001 WEB_HOST_PORT=3001 \
  bash deploy/install-vhost.sh
```

`API_HOST_PORT`/`WEB_HOST_PORT` (loopback-only) default to 8000/3000 — override them if something else on the box already holds those.

### Shared server already running Caddy

```bash
sudo DOMAIN=foodguard.yourdomain.com \
  API_HOST_PORT=8001 WEB_HOST_PORT=3001 \
  bash deploy/install-caddy.sh
```

No `EMAIL` needed — Caddy's automatic HTTPS doesn't require one up front (though its own config may set one globally for ACME notices).

### Shared server running Caddy in Docker

```bash
sudo DOMAIN=foodguard.yourdomain.com \
  CADDY_CONTAINER=chengetai-caddy \
  CADDY_NETWORK=chengetai-dare_dspacenet \
  CADDYFILE_HOST_PATH=/opt/chengetai-deploy/deployments/dare/engine/caddy/Caddyfile \
  bash deploy/install-caddy-docker.sh
```

Find those three values first:
```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'         # CADDY_CONTAINER: the caddy:2.x one
docker inspect <container> --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{"\n"}}{{end}}'   # CADDY_NETWORK
docker inspect <container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'      # CADDYFILE_HOST_PATH (the one mounted to /etc/caddy/Caddyfile)
```

Requirements for all four:
- The domain's DNS **A record already points at the server's public IP** (each script checks this and refuses to continue if it doesn't resolve; set `SKIP_DNS_CHECK=1` to bypass).
- You're running as root (or via `sudo`).

All four are safe to re-run: they skip secret generation if `.env` already exists, skip certificate issuance if a valid cert is already present (or no-op for Caddy if the site block already exists), and the seed script no-ops if demo data already exists.

Each script deploys the `claude/food-guard-ai-platform-z05ynw` branch by default (override with `BRANCH=main` once you've merged it) — review the diff and merge to `main` via a PR before treating a deployment as your production baseline long-term.

### Production notes (whether or not you use a script)

- Set `ENVIRONMENT=production` and a strong, unique `SECRET_KEY`.
- The compose file binds `db`, `api`, and `web` to `127.0.0.1`/internal-only by default; `API_HOST_PORT`/`WEB_HOST_PORT` control which loopback ports `api`/`web` publish to, so a reverse proxy on the same host can reach them without any port being exposed publicly except the proxy itself.
- Put PostgreSQL and file uploads (`/data/uploads` volume) on durable, backed-up storage — every install script now sets up nightly backups and health-check alerting automatically; see `docs/OPERATIONS.md` for what's installed and how to restore.
- Restrict `BACKEND_CORS_ORIGINS` to your real frontend domain(s) — the install scripts do this for you.
- Tune `RATE_LIMIT_PER_MINUTE` / `AUTH_RATE_LIMIT_PER_MINUTE` for your traffic.
- Run behind a process supervisor / orchestrator (Docker Swarm, Kubernetes, ECS, etc.) for zero-downtime deploys; the containers here are stateless aside from the `db`, `pgdata`, `api-uploads`, and (nginx-path only) `certbot-etc` volumes.
