# Architecture Document

## System Overview

```
┌─────────────────┐     HTTP/JSON      ┌──────────────────┐     SQL      ┌──────────┐
│                 │ ◄──────────────────► │                  │ ◄──────────► │          │
│  React Frontend │     REST API        │  FastAPI Backend  │   ORM       │  SQLite   │
│  (Vite + TW)    │                     │                   │             │  (→ PG)   │
│                 │                     │  ┌─────────────┐  │             │          │
└─────────────────┘                     │  │ ML Module   │  │             └──────────┘
                                        │  │ (scikit-learn)│  │
                                        │  └─────────────┘  │
                                        └──────────────────┘
```

## Layer Responsibilities

### Frontend (React + Vite + Tailwind CSS)
- **Role:** Presentation layer and user interaction
- **Key libraries:** Recharts (visualization), axios (HTTP), react-router-dom (routing)
- **Communication:** REST API calls to backend via axios
- **Build:** Vite dev server on port 5173; production bundle via `npm run build`

### Backend (FastAPI + Python)
- **Role:** Business logic, data access, ML inference
- **Structure:**
  - `routers/` — API endpoint definitions
  - `services/` — Business logic (decoupled from HTTP layer)
  - `models/` — SQLAlchemy ORM models
  - `schemas/` — Pydantic request/response validation
  - `config.py` — Environment-based configuration
  - `database.py` — Engine, session, and base model
- **Server:** Uvicorn ASGI on port 8000

### ML Module (`ml/`)
- **Role:** Data processing, model training, inference
- **Libraries:** pandas, numpy, scikit-learn
- **Models:** Serialized via joblib, stored in `ml/models/`
- **Integration:** Imported by backend services; no direct HTTP exposure

### Database (SQLite → PostgreSQL)
- **ORM:** SQLAlchemy 2.0 with declarative models
- **Migration path:** Change `DATABASE_URL` in `.env` to switch engines
- **Constraints:** All queries use ORM — no raw SQL tied to SQLite syntax

## Data Flow

```
User Action (Frontend)
    │
    ▼
API Request (axios → FastAPI router)
    │
    ▼
Service Layer (business logic)
    │
    ├──► Database (SQLAlchemy ORM)
    │
    └──► ML Module (scikit-learn model inference)
           │
           ▼
      Prediction / Analysis Result
           │
           ▼
API Response (Pydantic schema → JSON)
    │
    ▼
Frontend Rendering (Recharts / React components)
```

## Directory Map

| Directory | Purpose | Key files |
|-----------|---------|-----------|
| `frontend/src/components/` | Reusable UI components | Cards, charts, forms |
| `frontend/src/pages/` | Route-level page components | Dashboard, Analysis |
| `frontend/src/services/` | API client functions | `api.js` |
| `backend/app/routers/` | FastAPI endpoint groups | One file per domain |
| `backend/app/services/` | Business logic layer | Decoupled from HTTP |
| `backend/app/models/` | SQLAlchemy ORM models | One file per entity |
| `backend/app/schemas/` | Pydantic validation | Request/response DTOs |
| `ml/` | ML training and inference | Model code + artifacts |
| `data/` | Synthetic datasets | CSV/JSON files |
| `tests/` | Automated tests | pytest suites |

## Security & Privacy Notes

- This is an **academic project** — not a clinical system
- All data is **synthetic** — no real patient information
- `.env` files are excluded from version control
- No authentication is implemented (out of scope for this academic project)
- CORS is restricted to the frontend dev server origin
