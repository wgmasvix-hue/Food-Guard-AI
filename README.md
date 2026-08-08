# FoodOS

**AI-powered Food Safety, Quality Management & Compliance Platform** for food manufacturers and food service businesses.

FoodOS replaces paper-based HACCP and GMP records with a secure, intelligent, cloud-ready system that works on desktop, tablet, and mobile devices. It is designed as the foundation of a complete Food Manufacturing ERP.

![stack](https://img.shields.io/badge/stack-Next.js%20%7C%20FastAPI%20%7C%20PostgreSQL%20%7C%20Ollama-16a34a)

---

## Features (MVP)

| Module | Capabilities |
|---|---|
| **Authentication** | JWT (access + refresh), registration, password reset, multi-company support, 7 roles (RBAC) |
| **Dashboard** | Compliance score, today's tasks, open corrective actions, temperature alerts, upcoming audits, recent inspections, AI recommendations |
| **Company Management** | Companies, sites/facilities, departments, employees |
| **HACCP** | Hazard analysis, CCPs, critical limits, monitoring, corrective actions, verification, validation, review history |
| **GMP** | Digital inspection checklists — hygiene, cleaning, sanitation, equipment, maintenance, building, water, waste, pest control, chemical storage, visitor control |
| **Temperature** | Cold rooms, freezers, refrigerators, cooking, cooling, hot holding — automatic out-of-limit alerts |
| **Corrective Actions** | Issue → root cause → CA/PA → responsible person → deadline → evidence → verification |
| **Audits** | Internal/external audits, non-conformances, CAPA, scheduling, history |
| **Documents** | SOPs, policies, certificates, specs, supplier docs, training records — with version control |
| **AI Assistant** | Ollama-powered generation of HACCP plans, SOPs, cleaning procedures, policies, training material, risk assessments + free-form Q&A |
| **Reports** | PDF reports: temperature logs, inspections, HACCP monitoring, corrective actions, audits, compliance summary |

## Technology Stack

- **Frontend** — Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui-style components, React Query, React Hook Form
- **Backend** — FastAPI, Python 3.12, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT
- **Database** — PostgreSQL 16
- **AI** — Ollama with a modular provider interface (cloud models pluggable later)
- **Infrastructure** — Docker, Docker Compose, Nginx (HTTPS-ready)

## Quick Start

```bash
cp .env.example .env          # review secrets before production use
docker compose up -d --build  # api + web + db + nginx (+ ollama profile)
docker compose exec api python -m app.db.seed   # demo data
```

- Web app: http://localhost (via Nginx) or http://localhost:3000
- API docs (Swagger): http://localhost:8000/api/v1/docs
- Default seed login: `admin@demo.foodguard.ai` / `FoodGuard!234`

To enable the AI assistant locally:

```bash
docker compose --profile ai up -d ollama
docker compose exec ollama ollama pull llama3.2
```

See **[docs/INSTALL.md](docs/INSTALL.md)** for full installation, configuration and production notes, and **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for system design.

## Project Structure

```
Food-Guard-AI/
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── api/v1/     # Versioned REST endpoints
│   │   ├── core/       # Config, security, RBAC, rate limiting
│   │   ├── db/         # Session, base, seed data
│   │   ├── models/     # SQLAlchemy models
│   │   ├── schemas/    # Pydantic schemas
│   │   └── services/   # AI providers, PDF reports, compliance scoring
│   ├── alembic/        # Database migrations
│   └── tests/          # Pytest suite
├── frontend/           # Next.js application
│   └── src/
│       ├── app/        # App Router pages
│       ├── components/ # UI + feature components
│       └── lib/        # API client, auth, query hooks
├── nginx/              # Reverse proxy (HTTPS-ready)
├── docs/               # Installation, architecture, API guide
└── docker-compose.yml
```

## Development

```bash
# Backend
cd backend && pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Tests
cd backend && pytest
```

## Roadmap (architecture-ready future modules)

Inventory, production planning, recipes, food costing, nutrition analysis, label generation, traceability & recall, warehouse, maintenance, purchasing, sales, IoT sensors, barcode/QR, offline sync, mobile apps.

## License

Proprietary — © FoodOS.
