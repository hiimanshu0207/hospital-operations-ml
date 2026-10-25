# Hospital Operations & Workflow Optimization using Machine Learning

> B.Tech CSE Major Project — ML-powered decision support for hospital administrators and clinical workflow optimization.

## Overview

This system provides a full-stack, data-driven operational decision-support platform for hospital administrators, nurse managers, and clinical leaders:

- **Hospital Operational Telemetry:** Real-time monitoring of departmental bed occupancy, staff census by shift/role, nurse-to-patient ratio compliance, queue pressure indicators, and operational stress index.
- **Patient Demand Forecasting:** Hourly patient arrival predictions across departments (`ED`, `ICU`, `GEN`, `SURG`, `PED`) using trained scikit-learn regression pipelines with dynamic Poisson 95% confidence intervals and Recharts visual analytics.
- **Patient Waiting-Time Prediction:** Leakage-safe inference estimating minutes to triage based on triage acuity (ESI 1–5), queue depth, staff availability, and demographic profiles with 95% uncertainty bounds.
- **What-If Scenario Simulation:** Stochastic simulation evaluating the operational impact of patient arrival surges ($-50\%$ to $+100\%$), departmental staffing shifts, and physical bed expansions without modifying ground-truth databases.
- **Constraint-Aware Staff Allocation:** Linear programming optimization (SciPy SLSQP / Simplex) balancing clinical acuity, nurse-to-patient safety minimums, and physical department capacity with transparent recommendation rationales.

> [!NOTE]
> **Academic Research Notice:** This system is built entirely on synthetic operational and clinical encounter data. All model estimates represent statistical simulations for research purposes and must not be used as confirmed real-world clinical or operational outcomes.

---

## Tech Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| **Frontend** | React 19 + Vite 8 + Tailwind CSS 4 | Responsive SPA with ambient dark aesthetic, KPI stat cards, and interactive tools |
| **Data Visualization** | Recharts 3.x | AreaCharts with 95% uncertainty bands, custom dark-mode tooltips, and grid analytics |
| **API Client** | Axios | Centralized service layer with Vite proxy integration and error parsing |
| **Backend** | Python 3.11+ / 3.15 + FastAPI | High-performance asynchronous REST API with Pydantic validation |
| **Database** | SQLite / SQLAlchemy ORM | Local development database with PostgreSQL schema migration readiness |
| **Machine Learning** | Scikit-Learn, Pandas, NumPy | Leakage-free regression, time-series forecasting, and Poisson uncertainty estimation |
| **Optimization** | SciPy (`scipy.optimize.minimize`) | Constrained non-linear optimization with Hamilton-Hare integer rounding |
| **Code Quality** | Pytest, Oxlint | 115 automated backend, ML & E2E tests + sub-50ms frontend static linting |


---

## Project Structure

```
├── frontend/                  React + Vite dashboard application
│   ├── src/
│   │   ├── components/        StatCard, Navbar, Sidebar, DisclaimerBanner, LoadingSkeleton, Icons
│   │   ├── pages/             OverviewTab, DepartmentsTab, DemandForecastTab, WaitingTimeTab,
│   │   │                      SimulationTab, AllocationTab
│   │   ├── services/          api.js (centralized Axios client & endpoint functions)
│   │   ├── App.jsx            Root dashboard container & state synchronization
│   │   └── main.jsx           Vite entry point
│   ├── vite.config.js         Proxy configuration (/api and /health to FastAPI)
│   └── package.json           Dependencies & scripts
├── backend/                   FastAPI REST API
│   ├── app/
│   │   ├── main.py            FastAPI application entry point & CORS
│   │   ├── config.py          Pydantic settings & database configurations
│   │   ├── database.py        SQLAlchemy engine & session management
│   │   ├── models/            SQLAlchemy ORM domain models
│   │   ├── schemas/           Pydantic request & response schemas
│   │   └── routers/           API routers (departments, beds, visits, predictions, optimization)
│   └── requirements.txt       Python dependencies
├── ml/                        Machine learning pipelines & serialized artifacts
│   ├── demand_forecast.py     Patient arrival time-series forecasting pipeline
│   ├── waiting_time.py        Patient waiting-time regression pipeline
│   ├── optimization.py        Resource utilization, what-if simulator & staff allocator
│   └── models/                Serialized Joblib model pipelines & JSON metadata
├── data/                      Synthetic operational datasets (CSV format)
├── tests/                     Comprehensive test suite (115 passing tests)
├── docs/                      Architecture, EDA report, and design documentation
└── DAILY_REPORTS/             Day-by-day development logs
```

---

## Setup & Startup Instructions

### Prerequisites

- **Node.js:** $\ge$ 18.x and **npm:** $\ge$ 9.x
- **Python:** $\ge$ 3.11 (tested on Python 3.11 and 3.15)
- **Git**

---

### Terminal 1 — Backend (FastAPI Server)

Open your first terminal in the repository root:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux / macOS:
# source venv/bin/activate

# 3. Install required Python dependencies
pip install -r requirements.txt

# 4. Initialize environment file (if not already present)
cp .env.example .env

# 5. Start the FastAPI backend server
uvicorn app.main:app --reload --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- ReDoc API Documentation: `http://localhost:8000/redoc`
- System Health Endpoint: `http://localhost:8000/health`

---

### Terminal 2 — Frontend (React + Vite Dashboard)

Open a second terminal in the repository root:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

- Local Dashboard URL: `http://localhost:5173`
- The Vite development server automatically proxies all `/api` and `/health` requests to `http://localhost:8000`.

---

## Running Verification & Tests

### Backend & Machine Learning Test Suite

From the project root using the virtual environment:

```bash
# Windows PowerShell
.\backend\venv\Scripts\python.exe -m pytest -c pytest.ini

# Linux / macOS
# ./backend/venv/bin/python -m pytest -c pytest.ini
```

Expected result: `90 passed` covering unit tests, leakage audits, ML models, and API endpoints.

### Frontend Linting

From the `frontend/` directory:

```bash
# Direct node execution (reliable across Windows paths with special characters)
node node_modules/oxlint/bin/oxlint
# or: npm run lint
```

Expected result: `Found 0 warnings and 0 errors.`

### Frontend Production Build

From the `frontend/` directory:

```bash
node node_modules/vite/bin/vite.js build
# or: npm run build
```

Expected result: Production bundle compiled into `frontend/dist/`.

---

## API Endpoints Integrated

| Domain | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| **System** | `GET` | `/health` | API operational status and database connectivity |
| **Departments** | `GET` | `/api/v1/departments` | List all clinical departments and bed inventories |
| **Departments** | `GET` | `/api/v1/departments/{id}/metrics` | Aggregated department operational metrics |
| **Beds** | `GET` | `/api/v1/beds` | Bed inventory with occupancy status |
| **Beds** | `GET` | `/api/v1/beds/summary` | Hospital-wide bed capacity and occupancy totals |
| **Patient Visits** | `GET` | `/api/v1/patient-visits/summary` | Triage statistics, wait times, and acuity breakdowns |
| **Patient Visits** | `GET` | `/api/v1/patient-visits/recent` | Recent patient encounters stream for live queue auditing |
| **Demand Forecast** | `POST` | `/api/v1/predictions/demand` | Hourly arrival predictions with 95% Poisson confidence bands |
| **Waiting Time** | `POST` | `/api/v1/predictions/waiting-time` | Regression wait-time estimate by ESI acuity with 95% CI |
| **Resource Utilization** | `GET` | `/api/v1/optimization/utilization` | Bed capacity, staffing ratios, queue pressures, and alerts |
| **What-If Simulation** | `POST` | `/api/v1/optimization/simulate` | Stochastic simulation of arrival surges and resource adjustments |
| **Staff Allocation** | `POST` | `/api/v1/optimization/allocate` | Constrained linear programming staff allocation optimizer |

---

## License

B.Tech Major Project — Academic research use only. Not approved for real-world clinical decision-making.
