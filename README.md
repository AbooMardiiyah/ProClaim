# ProClaim — AI-Powered NHIA Claims Processing

> **ProClaim** is an AI-powered healthcare claims processing web application built for the Nigerian healthcare system (NHIA). It helps hospital billing officers upload patient encounter documents, automatically extracts structured claim data using Google Gemini AI, and guides each claim through a review workflow until submission to an HMO or NHIA portal.

---

## Overview

Processing reimbursement claims in Nigerian hospitals is often slow, paper-heavy, and error-prone. ProClaim digitises this workflow by:

- Accepting multiple documents per patient encounter (outpatient registers, lab reports, pharmacy logs, billing receipts).
- Using **Google Gemini 3.5 Flash** to extract structured fields such as patient name, NHIA ID, diagnosis, tariff codes, and costs.
- Letting billing officers review, correct, and approve extracted data.
- Enforcing a clear claim lifecycle: `DRAFT → PROCESSING → EXTRACTED → UNDER_REVIEW → READY → SUBMITTED → PAID / REJECTED`.
- Exporting structured claim data as JSON or CSV for HMO/NHIA submission.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query |
| Backend | FastAPI 0.111 + Python 3.11 (async) |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic |
| Task Queue | Celery 5.4 + Redis 7 |
| AI Extraction | Google Gemini 3.5 Flash |
| Auth | JWT (HS256) + bcrypt |

---

## Quick Start (Docker Compose)

From the repository root:

```bash
# 1. Create env file
cp proclaim/.env.example proclaim/.env
#   → edit .env and set SECRET_KEY, GEMINI_API_KEY, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD

# 2. Start all services
cd proclaim && docker compose up --build

# 3. Access the app
#   Frontend  → http://localhost:3001
#   API docs  → http://localhost:8001/api/docs
#   Health    → http://localhost:8001/health
```

> If port `3001` is already in use, set `PROCLAIM_FRONTEND_PORT=3002` in `.env`.

### Convenience commands

A `Makefile` is included:

```bash
make up-build   # Build and start all services
make down       # Stop all services
make logs SERVICE=api   # Tail logs for a service
make shell-db   # Open psql
make generate-docs      # Generate mock PDFs for testing
```

---

## Environment Variables

Copy `.env.example` to `proclaim/.env` and configure:

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | Yes | JWT signing key (≥ 32 chars) |
| `GEMINI_API_KEY` | Yes | Google Gemini API key for document extraction |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `CELERY_BROKER_URL` | Yes | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Yes | Celery result backend URL |
| `FIRST_ADMIN_EMAIL` | Yes | Email for auto-created admin user |
| `FIRST_ADMIN_PASSWORD` | Yes | Password for auto-created admin user |
| `ALLOWED_ORIGINS` | Yes | JSON array of allowed CORS origins |
| `PROCLAIM_FRONTEND_PORT` | No | Host port for frontend container (default `3001`) |

---

## Testing the Extraction Flow

1. Log in with the seeded admin credentials at `http://localhost:3001/login`.
2. Create a new claim from the dashboard.
3. Upload one or more PDFs from the encounter.
4. Wait for extraction (status changes from `DRAFT` → `PROCESSING` → `EXTRACTED`).
5. Review extracted fields, make corrections, and advance the claim through `UNDER_REVIEW` → `READY` → `SUBMITTED`.
6. Export the claim as JSON or CSV.

Mock test documents can be generated with:

```bash
cd proclaim/backend
python scripts/generate_test_docs.py
```

---

## Deployment (Railway)

ProClaim is ready to deploy on Railway:

1. Create a new Railway project.
2. Add a **PostgreSQL** service and a **Redis** service.
3. Add three deployable services from this repo:
   - **API**: Dockerfile at `proclaim/backend/Dockerfile`; start command `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
   - **Worker**: Dockerfile at `proclaim/backend/Dockerfile`; start command `celery -A app.workers.celery_app worker -Q extraction -l info --concurrency 2`.
   - **Frontend**: Dockerfile at `proclaim/frontend/Dockerfile`.
4. Set the production environment variables from `.env.example`.
5. Run `alembic upgrade head` in the API service to create tables.
6. Update `ALLOWED_ORIGINS` to include the deployed frontend URL.

---

## Project Structure

```
proclaim/
├── docker-compose.yml      # Local dev orchestration
├── .env.example            # Required env vars
├── Makefile                # Convenience commands
├── README.md               # This file
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── api/            # FastAPI routers
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas
│       ├── services/       # Business logic + AI extraction
│       └── workers/        # Celery tasks
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── src/
        ├── pages/          # Landing, Login, Dashboard, Upload, Claims, Review
        ├── components/
        ├── hooks/
        └── lib/
```

---

## Submission Deliverables

- ✅ Live demo link (Railway)
- ✅ Source code (GitHub)
- ✅ Project report
- ✅ Presentation slides
- ✅ Demo video

---

## License

This project was built as an AI Accelerator Capstone Project and is provided for demonstration purposes.
