# Hospital Operations & Workflow Optimization using Machine Learning

> **B.Tech CSE Major Project** — An end-to-end, machine learning-powered clinical decision-support and hospital capacity management platform.

---

## 1. System Overview

This platform provides hospital administrators, nurse supervisors, and operational leadership with transparent, real-time analytics and predictive intelligence across clinical workflows:

- **Hospital Operational Telemetry:** Real-time monitoring of departmental bed occupancy, nurse-to-patient staffing ratio compliance, queue depth pressures, and an aggregated hospital-wide **Operational Stress Index (0–100 scale)**.
- **Patient Demand Forecasting:** Hourly patient arrival predictions across departments (`ED`, `ICU`, `GEN`, `SURG`, `PED`) using trained scikit-learn regression pipelines with dynamic Poisson 95% confidence intervals and Recharts visual analytics.
- **Patient Waiting-Time Prediction:** Target-leakage-free regression predicting estimated minutes to physician triage based on clinical acuity (Emergency Severity Index Levels 1–5), queue depth, active clinical staff, and demographic groups, complete with 95% uncertainty bounds.
- **What-If Scenario Simulation:** Parameterized stochastic simulation projecting the operational impact of arrival surges ($-50\%$ to $+100\%$), departmental staffing reassignments, and bed expansions without mutating underlying database records.
- **Constraint-Aware Staff Allocation Optimizer:** Linear programming optimization (SciPy SLSQP) balancing acuity-weighted queue pressure against staffing churn, enforcing mandatory patient safety minimums, physical capacity limits, and exact workforce headcount conservation via Hamilton-Hare integer rounding.

> [!NOTE]
> **Academic Research & Demonstration Notice:** This system is built entirely on mathematically modeled synthetic operational and clinical encounter data. All model estimates represent statistical decision-support simulations for research evaluation and must not be used as confirmed real-world clinical diagnoses or triage mandates.

---

## 2. System Architecture

```mermaid
graph TB
    subgraph ClientLayer ["Frontend Presentation Layer (React 19 + Vite 8 + Tailwind CSS 4)"]
        SPA["React SPA (App.jsx)"]
        NAV["Navbar & Connectivity Monitor"]
        SIDE["Responsive Navigation Sidebar"]
        TAB1["OverviewTab (Hospital Stress Index & Encounters)"]
        TAB2["DepartmentsTab (Bed Utilization & Nurse Ratios)"]
        TAB3["DemandForecastTab (Recharts AreaChart + 95% CI)"]
        TAB4["WaitingTimeTab (ESI 1-5 Acuity & Uncertainty Intervals)"]
        TAB5["SimulationTab (Surge Slider & Bottleneck Warnings)"]
        TAB6["AllocationTab (Shift Optimizer & Headcount Conservation)"]
        AXIOS["Axios Client (services/api.js)"]
    end

    subgraph GatewayLayer ["Vite Proxy / Reverse Proxy"]
        PROXY["Proxy Gateway (:5173)<br/>/api & /health -> :8000"]
    end

    subgraph BackendLayer ["Application Service Layer (FastAPI + Python 3.11/3.15)"]
        FASTAPI["FastAPI REST API (app/main.py)"]
        CORS["CORS Policy Middleware"]
        ROUTERS["Domain Routers (/departments, /beds, /visits, /predictions, /optimization)"]
        SCHEMAS["Pydantic Schemas (Strict Request/Response DTOs)"]
    end

    subgraph MLLayer ["Machine Learning & Optimization Engine (ml/)"]
        FEAT["HospitalFeaturePipeline (Leakage-Safe Transformer)"]
        DEMAND["Demand Forecast Model (SeasonalHourBaseline / RF)"]
        WAIT["Waiting-Time Regressor (RandomForestRegressor Depth 4)"]
        SIM["What-If Scenario Engine (Non-Mutating State Isolation)"]
        OPT["Staff Allocation Optimizer (SciPy SLSQP + Hamilton-Hare Rounding)"]
        MODELS["Serialized Model Artifacts (ml/models/*.joblib + *.json)"]
    end

    subgraph DataLayer ["Persistence & Synthetic Telemetry Layer"]
        ORM["SQLAlchemy 2.0 ORM"]
        SQLITE["SQLite Database (hospital_ops.db)<br/>PostgreSQL Migration Ready"]
        GEN["Synthetic Data Generator (600 Encounters, 5 Departments)"]
        CSV["Data Directory (data/*.csv)"]
    end

    SPA --> NAV & SIDE
    SPA --> TAB1 & TAB2 & TAB3 & TAB4 & TAB5 & TAB6
    TAB1 & TAB2 & TAB3 & TAB4 & TAB5 & TAB6 --> AXIOS
    AXIOS --> PROXY
    PROXY --> FASTAPI
    FASTAPI --> CORS --> ROUTERS --> SCHEMAS
    ROUTERS --> ORM --> SQLITE
    ROUTERS --> FEAT & SIM & OPT
    FEAT --> DEMAND & WAIT --> MODELS
    SIM --> WAIT
    GEN --> SQLITE & CSV
```

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend Framework** | React | 19.3.x | Reactive component UI and state management |
| **Build & Dev Server** | Vite | 8.3.x | Sub-second HMR and optimized production bundling |
| **Styling** | Tailwind CSS | 4.3.x | Modern dark-mode aesthetic with ambient glassmorphism |
| **Data Visualization** | Recharts | 3.10.x | Responsive time-series charts with 95% confidence bands |
| **API Client** | Axios | 1.20.x | HTTP client with automatic error extraction |
| **Backend Framework** | FastAPI | 0.115.x | High-performance asynchronous REST API |
| **Validation** | Pydantic v2 | 2.6.x | Schema validation and settings management |
| **ORM / Database** | SQLAlchemy | 2.0.x | Declarative data models (SQLite / PostgreSQL) |
| **Machine Learning** | Scikit-Learn | 1.6.x | Leakage-free regression, baseline pipelines, and model evaluation |
| **Mathematical Optimization** | SciPy | 1.13.x | Constrained non-linear optimization (`scipy.optimize.minimize`) |
| **Data Manipulation** | Pandas & NumPy | 2.2.x / 2.1.x | Data transformation and matrix operations |
| **Testing & Quality** | Pytest & Oxlint | 9.1.x / 1.88.x | 115 backend/ML/E2E tests + sub-50ms static linting |

---

## 4. Practical Demonstration Walkthrough

When presenting or evaluating this major project, follow this structured six-step demonstration walkthrough:

### Step 1: Real-Time Operational Telemetry (Overview Tab)
1. Navigate to `http://localhost:5173`.
2. Inspect the **Navbar Status Indicator** (`API Online` with pulsing green dot).
3. Review the top KPI StatCards:
   - **Operational Stress:** Displays the composite index (0–100 scale) with color-coded operational severity (Normal $<40$, Elevated $40-69$, Critical $\ge 70$).
   - **Bed Occupancy:** Current hospital census against total capacity.
   - **Active Clinical Staff:** Total on-duty doctors and nurses across active shifts.
   - **Avg Triage Wait:** Historical average wait time across all recorded patient encounters.
4. Review the **Active Operational Warnings** and the **Recent Patient Encounters** stream displaying incoming patients and ESI triage scores.

### Step 2: Department Capacity & Compliance Auditing (Departments Tab)
1. Click the **Departments** tab.
2. Observe individual clinical cards for **ED**, **ICU**, **GEN**, **SURG**, and **PED**.
3. Point out the **Nurse-to-Patient Ratio Compliance Badge** (Compliant vs Non-compliant) dynamically calculated from the assigned nurses and bed census.
4. Point out the **Queue Pressure Level** (Low, Moderate, High, Severe) and ML-predicted benchmark wait times.

### Step 3: Patient Arrival Trajectory Forecasting (Demand Forecast Tab)
1. Click the **Demand Forecast** tab.
2. Select **Emergency Department (ED)** and toggle the horizon pills (**12 Hours**, **24 Hours**, **48 Hours**).
3. Click **Update Trajectory**.
4. Examine the **Recharts AreaChart**:
   - Solid cyan curve represents expected patient arrivals per hour.
   - Shaded purple band represents the Poisson-based 95% confidence interval ($\text{Lower} \dots \text{Upper}$).
5. Review the hourly projection table detailing timestamp, forecasted arrivals, and peak load indicators.

### Step 4: Leakage-Safe Patient Waiting-Time Prediction (Wait-Time Predictor Tab)
1. Click the **Wait-Time Predictor** tab.
2. Demonstrate **Clinical Acuity Sensitivity**:
   - Select **ESI 1: Resuscitation** $\rightarrow$ Observe immediate triage wait time ($\approx 1-3$ minutes).
   - Select **ESI 5: Non-urgent** $\rightarrow$ Observe deferred wait time ($\approx 45-60$ minutes).
3. Demonstrate **Queue vs. Staff Sensitivity**:
   - Drag the **Queue Length** slider up to 25 patients $\rightarrow$ Wait time increases smoothly.
   - Drag the **Available Staff** slider up to 10 personnel $\rightarrow$ Wait time drops significantly due to increased service throughput.
4. Review the predicted waiting time, 95% uncertainty interval, and automated clinical rationale explaining model feature importance.

### Step 5: What-If Operational Simulation (What-If Simulation Tab)
1. Click the **What-If Simulation** tab.
2. Drag the **Arrival Surge Adjustment** slider to **+30%** (hypothetical mass-casualty or seasonal epidemic).
3. Adjust departmental staffing steppers (e.g. +3 staff to ED, -1 from GEN).
4. Click **Run Operational Simulation**.
5. Observe the **Baseline vs. Simulated** comparison cards:
   - Net change in average hospital wait time.
   - Department-by-department bed utilization shifts and queue accumulation deltas.
   - Projected capacity bottleneck warnings (e.g., `PROJECTED_HIGH_OCCUPANCY: ED at 96%`).
6. Emphasize that the simulation executes in isolated memory without corrupting database records.

### Step 6: Constraint-Aware Staff Allocation Optimization (Staff Allocation Tab)
1. Click the **Staff Allocation** tab.
2. Select a target shift (e.g., **Morning** or **All**).
3. Enter a custom total staff budget or leave blank to conserve the current active staff count.
4. Click **Solve Staff Plan**.
5. Review the optimization output:
   - **Workforce Headcount Conservation:** Verified $\sum \text{Allocated} = \text{Budget}$ with zero fractional personnel.
   - **Constraint Bounds:** Every department respects mandatory patient safety minimums (`ED: 4`, `ICU: 3`, `GEN: 4`, `SURG: 2`, `PED: 2`) and maximum physical room capacities.
   - **Contextual Clinical Rationale:** Clear textual justifications for each transfer (e.g., allocating staff to ICU due to clinical life-support weight).

---

## 5. Machine Learning Benchmarks & Model Evaluation

### 5.1 Demand Forecasting Model Evaluation
- **Task:** 1-step to 72-step hourly arrival prediction across 5 hospital departments.
- **Features (20):** Hour of day, day of week, cyclical sine/cosine transforms, weekend flag, night shift flag, peak hours flag, department bed capacity, target nurse ratio, one-hot department encodings, 24h/48h autoregressive lags, 24h rolling mean/max.
- **Evaluation Dataset:** 14 days of synthetic admissions (Train: Days 3–10, Val: Days 11–12, Test: Days 13–14).

| Algorithm | Validation MAE | Validation RMSE | Test MAE | Test RMSE | Notes |
|-----------|----------------|-----------------|----------|-----------|-------|
| **SeasonalHourBaseline** (Selected) | **0.440** | **0.660** | **0.415** | **0.631** | **Best test generalization; robust against small-count Poisson noise** |
| Ridge Regression | 0.448 | 0.672 | 0.437 | 0.618 | L2 regularization ($\alpha=1.0$) prevents overfitting |
| Random Forest Regressor | 0.440 | 0.663 | 0.433 | 0.618 | 100 trees, max depth 5 |
| HistGradientBoosting | 0.426 | 0.663 | 0.457 | 0.676 | Slight overfit on validation set |
| Department Mean Baseline | 0.476 | 0.682 | 0.446 | 0.635 | Naive reference baseline |

### 5.2 Waiting-Time Prediction Model Evaluation
- **Task:** Continuous regression predicting minutes to service start from arrival information available at intake.
- **Features (19):** Current queue length, available staff, queue-to-staff ratio, ESI acuity (1–5), age group code, cyclical hour/day sine/cosine, weekend/night/peak flags, critical acuity flag, high queue flag, department encodings.
- **Target Leakage Safeguard:** Explicit exclusion of `service_start_timestamp`, `length_of_stay_minutes`, `admission_required`, `status`, and `bed_id`.

| Algorithm | Validation MAE (min) | Validation RMSE (min) | Test MAE (min) | Test RMSE (min) | Notes |
|-----------|----------------------|-----------------------|----------------|-----------------|-------|
| **RandomForestRegressor** (Selected) | **8.472** | **10.278** | **9.231** | **12.113** | **Enforces clinical monotonicity; 100 estimators, max depth 4** |
| HistGradientBoosting | 8.561 | 10.276 | 9.757 | 12.279 | Fast gradient boosting |
| Ridge Regression | 9.397 | 11.617 | 9.551 | 12.257 | Linear baseline with engineered interaction terms |
| Dept + Acuity Median Baseline | 9.462 | 11.712 | 9.331 | 11.895 | Domain-heuristic baseline |
| Overall Median Baseline | 19.731 | 25.432 | 19.700 | 25.262 | Naive median reference |

- **Residual Distribution (Test Set):** Mean bias $= +0.056$ min, Standard Deviation $= 12.113$ min, Median $= +0.285$ min, Interquartile Range $=[-5.761, +7.606]$ min.

---

## 6. Setup & Execution Guide

### Prerequisites
- **Node.js:** $\ge$ 18.x and **npm:** $\ge$ 9.x
- **Python:** $\ge$ 3.11 (tested on Python 3.11 and 3.15)
- **Git**

---

### Step 1: Backend Setup & Database Seeding

Open a terminal in the project root:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate Python virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment configuration
cp .env.example .env

# 5. Initialize database tables and seed synthetic operational records
python seed.py

# 6. Launch FastAPI server with auto-reload
python -m uvicorn app.main:app --reload --port 8000
```

- API Root: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`
- System Health Check: `http://localhost:8000/health`

---

### Step 2: Frontend Setup & Dev Server

Open a second terminal in the project root:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite dev server
npm run dev
```

- Local Dashboard: `http://localhost:5173`
- The Vite development server automatically proxies all `/api` and `/health` requests to `http://localhost:8000`.

---

## 7. Running the Automated Test Suite

### Full Backend, ML & E2E Pytest Suite
From the repository root using the virtual environment:

```powershell
# Windows PowerShell
.\backend\venv\Scripts\python.exe -m pytest -c pytest.ini

# Linux / macOS
# ./backend/venv/bin/python -m pytest -c pytest.ini
```

**Expected Result:**
```
======================= 115 passed, 9 warnings in 6.28s =======================
```
Covers:
- View 1–6 end-to-end integration contracts
- Staff allocation budget conservation and safety minimums
- What-if simulation surge bounds and bed eviction prevention
- Clinical triage acuity monotonicity ($\text{ESI 1} < \text{ESI 5}$)
- Prohibited target leakage column rejection
- Missing model artifact 503 handling
- Empty database resilience across all endpoints

### Frontend Linting
```powershell
# Run from frontend/ directory:
node node_modules/oxlint/bin/oxlint
```
**Expected Result:** `Found 0 warnings and 0 errors.`

### Frontend Production Build
```powershell
# Run from frontend/ directory:
node node_modules/vite/bin/vite.js build
```
**Expected Result:** Clean production bundle compiled into `frontend/dist/` in $<2$ seconds.

---

## 8. Integrated API Endpoints

| Domain | Method | Endpoint | Description | Status |
|--------|--------|----------|-------------|--------|
| **System** | `GET` | `/health` | API liveness and database connectivity verification | `200 OK` |
| **Departments** | `GET` | `/api/v1/departments` | List clinical units, bed counts, and occupancy percentages | `200 OK` |
| **Departments** | `GET` | `/api/v1/departments/{id}` | Single department details and operational ratios | `200 OK` |
| **Departments** | `GET` | `/api/v1/departments/{id}/metrics` | Department-specific telemetry and occupancy rates | `200 OK` |
| **Beds** | `GET` | `/api/v1/beds` | Bed inventory with department and occupancy filtering | `200 OK` |
| **Beds** | `GET` | `/api/v1/beds/summary` | Hospital-wide total, occupied, and available bed counts | `200 OK` |
| **Patient Visits** | `GET` | `/api/v1/patient-visits/summary` | Triage statistics, wait times, and acuity breakdowns | `200 OK` |
| **Patient Visits** | `GET` | `/api/v1/patient-visits/recent` | Recent patient arrivals ordered chronologically descending | `200 OK` |
| **Demand Forecast** | `POST` | `/api/v1/predictions/demand` | Hourly arrival forecasts with 95% Poisson confidence bands | `200 OK` |
| **Waiting Time** | `POST` | `/api/v1/predictions/waiting-time` | Leakage-free regression wait-time inference with 95% CI | `200 OK` |
| **Resource Utilization**| `GET` | `/api/v1/optimization/utilization` | Bed capacity, staffing ratios, queue pressures, and alerts | `200 OK` |
| **What-If Simulation** | `POST` | `/api/v1/optimization/simulate` | Stochastic simulation of arrival surges and resource adjustments | `200 OK` |
| **Staff Allocation** | `POST` | `/api/v1/optimization/allocate` | Constrained linear programming staff allocation optimizer | `200 OK` |

---

## 9. Deployment Architecture & Production Guide

### Production ASGI Configuration
For multi-threaded or multi-worker production deployments:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
```

### PostgreSQL Migration
The application uses SQLAlchemy 2.0 declarative models with zero SQLite-specific raw SQL. To migrate to PostgreSQL:
1. Ensure PostgreSQL driver is installed: `pip install psycopg2-binary`
2. Update `DATABASE_URL` in `backend/.env`:
   ```env
   DATABASE_URL="postgresql://hospital_user:secure_password@localhost:5432/hospital_ops"
   ```
3. Run `python seed.py` to create the schema and populate baseline synthetic records.

### Nginx Reverse Proxy Blueprint
```nginx
server {
    listen 80;
    server_name hospital-ops.example.edu;

    # Serve compiled Vite frontend
    location / {
        root /var/www/hospital-ops/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API and health check to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 10. Academic Dataset Scope & Limitations

1. **Synthetic Data Boundaries:**
   - The current synthetic database contains 600 total patient visits over a 14-day window across 5 clinical departments.
   - Low hourly counts (0–5 arrivals per hour) mean stochastic Poisson noise dominates individual hours.
2. **Clinical Decision Disclaimer:**
   - This project demonstrates machine learning architectures and mathematical optimization workflows. It is **not clinically certified** or validated for real medical diagnosis, real triage classification, or actual hospital staffing reassignments.
3. **No Private Patient Data:**
   - Zero patient identifiers, medical histories, or protected health information (PHI) exist in this repository.

---

## 11. License

B.Tech Computer Science & Engineering Major Project. For academic evaluation and research purposes only.
