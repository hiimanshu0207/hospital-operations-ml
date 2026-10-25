# Project Plan — 15-Day Development Schedule

**Project:** Hospital Operations & Workflow Optimization using ML
**Start Date:** 2026-10-23
**Target Completion:** 2026-11-06

---

## Phase 1: Foundation (Days 1–3)

### Day 1 — Project Setup ✅ (2026-10-23)
- [x] Workspace inspection and prerequisite check
- [x] Monorepo folder structure
- [x] React + Vite + Tailwind frontend scaffold
- [x] FastAPI backend with `/health` endpoint
- [x] Dependencies, `.gitignore`, environment config
- [x] Documentation: README, PROJECT_PLAN, ARCHITECTURE
- [x] Verification: frontend build + backend health check
- [x] Git init, configuration, and initial commit pushed to GitHub

### Day 2 — Database & Data Models ✅ (2026-10-24)
- [x] Design hospital domain entities (patients, departments, beds, staff)
- [x] SQLAlchemy ORM models with integrity check constraints
- [x] SQLite persistence configuration and table initialization (`init_db`)
- [x] Reproducible synthetic data generator (Python, Pandas, NumPy)
- [x] Validation for non-negative durations, sequential timestamps, and bed capacity
- [x] FastAPI CRUD endpoints for departments, beds, and patient visits
- [x] Automated test suite (30 passing tests: models, generator, API endpoints)

### Day 3 — Exploratory Data Analysis & Feature Engineering ✅ (2026-10-24)
- [x] Comprehensive dataset audit (zero duplicates, zero negative durations, 100% timestamp consistency)
- [x] Exploratory Data Analysis suite generating 7 operational visualization figures
- [x] Markdown EDA report with distribution insights and queue correlations (`docs/EDA_REPORT.md`)
- [x] Prediction-time feature engineering pipeline (temporal, cyclical, operational queues, acuity)
- [x] Strict target leakage prevention enforcing separation of future service milestones
- [x] Automated test suite expanded to 43 passing tests across data quality, features, and API

---

## Phase 2: ML Models (Days 4–8)

### Day 4 — Patient Demand Forecasting ✅ (2026-10-24)
- [x] Continuous hourly department arrival aggregation with zero-fill (1,680 series rows across 14 days)
- [x] Time-series audit, temporal ordering validation, and dataset limitation documentation
- [x] Strict chronological train/validation/test partitions without lookahead leakage
- [x] Baseline implementations: Historical Department Mean and Seasonal Hour Baseline
- [x] Scikit-learn regression models trained and evaluated: Ridge, HistGradientBoosting, RandomForest
- [x] Honest evaluation reporting: Seasonal Hour Baseline best Test MAE (0.415), Ridge/RF lowest Test RMSE (0.618)
- [x] Model bundle serialization (`ml/models/demand_forecast_model.joblib`) and metadata documentation (`ml/models/demand_model_metadata.json`)
- [x] REST endpoint `POST /api/v1/predictions/demand` with dynamic Poisson confidence bounds, validation, and simulation disclaimer
- [x] Automated test suite expanded to 53 passing tests (unit, ML validation, and prediction API)

### Day 5 — Waiting Time Prediction ✅ (2026-10-24)
- [x] Target definition and consistency audit (`waiting_time_minutes = service_start - arrival`, max discrepancy 0.0m)
- [x] Prediction-time operational feature extraction (19 features, strict leakage elimination including `admission_required`)
- [x] Chronological train/validation/test partitions (Days 1–10 train [420], Days 11–12 val [100], Days 13–14 test [80])
- [x] Statistical median baselines (Overall, Department, Department+Acuity)
- [x] Regressor training and comparison: Ridge, HistGradientBoosting, RandomForestRegressor
- [x] Honest evaluation reporting: RandomForest achieved lowest Test MAE (9.231m) and Test RMSE (12.113m)
- [x] Residual diagnostics (mean bias: 0.056m, std: 12.113m, near-normal error distribution) and department slice analysis
- [x] Model pipeline serialization (`ml/models/waiting_time_pipeline.joblib`) and metadata documentation (`ml/models/waiting_time_metadata.json`)
- [x] REST endpoint `POST /api/v1/predictions/waiting-time` with input validation, confidence intervals, and clinical disclaimer
- [x] Automated test suite expanded to 69 passing tests across ML validation and prediction API

### Day 6 — Hospital Resource Optimization and What-if Simulation ✅ (2026-10-24)
- [x] Departmental resource & capacity utilization engine (bed utilization, staff by shift/role, queue pressure, ML wait-time indicators)
- [x] Division-by-zero protection and missing data safety across all operational calculations
- [x] Reproducible, non-mutating what-if simulation engine (arrival surges, staff adjustments, bed capacity changes)
- [x] Reused Day 5 ML waiting-time predictor and Day 4 demand metrics to model simulated operational deltas
- [x] Transparent constraint-aware staff allocation optimizer using SciPy SLSQP with Largest Remainder integer rounding
- [x] Hard safety constraints enforced (headcount budget conservation, minimum safety staffing, maximum capacity bounds)
- [x] Rule-based constrained recommendation baseline for comparison
- [x] Versioned FastAPI endpoints: `GET /api/v1/optimization/utilization`, `POST /api/v1/optimization/simulate`, `POST /api/v1/optimization/allocate`
- [x] Automated test suite expanded to 90 passing tests across ML units and FastAPI integration

### Day 7 — React Dashboard Integration ✅ (2026-10-25)
- [x] Vite dev proxy configured in `frontend/vite.config.js` to route `/api` and `/health` to FastAPI on port 8000
- [x] Centralized Axios service layer (`frontend/src/services/api.js`) consuming real backend endpoints without mock fallbacks
- [x] Modern, responsive dashboard layout with dark aesthetic, ambient glow, top navigation, and sidebar tabs
- [x] Live backend connectivity status indicator with automatic reconnection polling and manual refresh controls
- [x] Hospital Overview with dynamic KPI cards, operational stress index gauge, active warnings alert box, and recent patient encounter stream
- [x] Department Operations view with per-department bed utilization progress bars, nurse ratio compliance badges, and queue pressures
- [x] Interactive Demand Forecast tool with department and horizon selectors, Recharts `AreaChart` with shaded 95% confidence intervals, and hourly forecast table
- [x] Interactive Waiting-Time Predictor with ESI triage acuity (Levels 1–5), queue length and staff availability sliders, age demographic groups, and 95% uncertainty interval output
- [x] What-If Simulation Explorer with arrival surge slider (-50% to +100%), horizon windows, fine-grained staff/bed steppers, and baseline vs. simulated comparisons
- [x] Staff Allocation Optimizer with shift selector, optional budget constraints, optimal staff recommendations table, and API recommendation rationales
- [x] Prominent academic synthetic-data disclaimer displayed across all model prediction views
- [x] Verification completed: full pytest suite passing (90/90), oxlint passing (0 errors, 0 warnings), and Vite production build succeeding

### Day 8 — Patient-Visit API Integration & Route Harmonization
- [x] Diagnosed and resolved 404 on `GET /api/v1/patient-visits/summary` and `GET /api/v1/patient-visits/recent?limit=8`
- [x] Mounted `visits_router` under both `/api/v1/visits` and `/api/v1/patient-visits` for 100% backward compatibility
- [x] Added `PatientVisitSummaryResponse` and ordered `/recent` query endpoints
- [x] Automated test suite in `tests/test_backend/test_api_visits.py` passing with limit validation

---

## Phase 3: Integration & Dashboard (Days 9–12)

### Day 9 — End-to-End Testing and Model Validation
- [x] Automated end-to-end validation suite covering all six operational views in `tests/test_backend/test_e2e_validation.py`
- [x] Verified demand forecasting and waiting-time prediction with valid, invalid, and boundary inputs
- [x] Tested what-if simulation and staff allocation constraints: staffing minimums, bed eviction prevention, integer allocations, and workforce budget conservation
- [x] Verified prediction reproducibility, non-negativity ($\ge 0$), and clinical acuity triage ordering (ESI 1 wait < ESI 5 wait)
- [x] Audited strict absence of prohibited target-leakage features (`PROHIBITED_LEAKAGE_COLUMNS` rejection verified)
- [x] Tested empty database handling across all routes, malformed bodies, and missing model artifacts (503 Service Unavailable)
- [x] Resolved defect in `GET /api/v1/beds/summary` (router path ordering and `BedSummaryResponse`) and added `GET /api/v1/departments/{id}/metrics`
- [x] Fixed operational stress index threshold scaling bug in `OverviewTab.jsx` (adjusted to 0–100 scale)
- [x] Executed complete test suite (115/115 passed), frontend lint (`oxlint` 0 errors/warnings), and production build (`vite build` succeeded)

### Day 10 — Deployment Readiness, Dashboard Polish, and Major Project Demonstration
- [x] Code-level audit and full walkthrough across all six dashboard views (Overview, Departments, Demand Forecast, Wait-Time Predictor, What-If Simulation, Staff Allocation)
- [x] Verified loading, success, empty-data, invalid-input, API-error, and missing-model states
- [x] Tested desktop, tablet, and mobile responsiveness; resolved UI status badge mismatches in `SimulationTab.jsx` and `AllocationTab.jsx`
- [x] Removed non-standard `xs:` class in `Navbar.jsx` ensuring permanent mobile status visibility
- [x] Audited dependency manifests (`requirements.txt` updated with `scipy` and `joblib`, `package.json`), `.env.example`, and CORS/proxy configs
- [x] Updated `README.md` with detailed practical demonstration walkthrough, architecture diagrams, benchmark tables, and production deployment guide
- [x] Updated `docs/ARCHITECTURE.md` with complete multi-tier Mermaid diagrams and optimization formulations
- [x] Full test suite (115/115 passed), oxlint (0 errors/warnings), and Vite production build verified

### Day 11 — Advanced Visualizations
- [ ] Heatmaps, trend lines, distribution plots
- [ ] KPI summary cards
- [ ] Alerts for critical occupancy levels

### Day 12 — Integration Testing
- [ ] End-to-end API tests
- [ ] Frontend component tests
- [ ] Performance optimization

---

## Phase 4: Polish & Documentation (Days 13–15)

### Day 13 — OR-Tools Optimization
- [ ] Google OR-Tools integration for staff scheduling
- [ ] Constraint-based resource allocation
- [ ] Optimization results API

### Day 14 — Documentation & Presentation
- [ ] Final ARCHITECTURE.md update
- [ ] API documentation (auto-generated + manual)
- [ ] User guide
- [ ] Project report draft

### Day 15 — Final Testing & Submission
- [ ] Complete test suite execution
- [ ] Bug fixes and final polish
- [ ] Final commit and tag (v1.0.0)
- [ ] Deployment instructions
- [ ] Project submission

---

## Status Legend
- ✅ Completed
- 🔄 In progress
- ⏳ Upcoming
- ❌ Blocked
