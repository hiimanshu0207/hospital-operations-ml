# Hospital Operations & Workflow Optimization using Machine Learning

> B.Tech CSE Major Project — ML-powered decision support for hospital administrators.

## Overview

This system helps hospital administrators:

- **Analyze patient demand** patterns across departments and time periods
- **Predict waiting times** using machine learning models
- **Monitor bed occupancy** in real time with forecasting
- **Explore resource-allocation scenarios** using optimization

Built with synthetic data for academic purposes — no real patient information is used.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React.js + Vite + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | SQLite (dev) → PostgreSQL (prod-ready) |
| ML | Pandas, NumPy, scikit-learn |
| Visualization | Recharts |
| Optimization | Google OR-Tools (Phase 2) |

## Project Structure

```
├── frontend/          React + Vite application
├── backend/           FastAPI REST API
├── ml/                Machine learning modules
├── data/              Synthetic datasets
├── tests/             Pytest & build tests
├── docs/              Architecture & design docs
└── DAILY_REPORTS/     Day-by-day progress logs
```

## Quick Start

### Prerequisites

- Node.js ≥ 18.x and npm ≥ 9.x
- Python ≥ 3.11 and pip
- Git

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy env file and adjust if needed
cp .env.example .env

# Start dev server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

## Verification Checklist

- [ ] `npm run build` in `frontend/` completes without errors
- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `GET http://localhost:8000/health` returns `{"status": "healthy", ...}`
- [ ] `http://localhost:5173` loads the landing page
- [ ] `pytest` passes all tests from the project root

## License

Academic project — not for clinical use.
