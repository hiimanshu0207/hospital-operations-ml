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

### Day 3 — Synthetic Data & Exploration
- [ ] Generate realistic synthetic hospital datasets
- [ ] Data loading scripts and seed command
- [ ] Basic data exploration and statistics
- [ ] API endpoints to serve summary statistics
- [ ] Frontend: dashboard skeleton with placeholder cards

---

## Phase 2: ML Models (Days 4–8)

### Day 4 — Patient Demand Analysis
- [ ] Feature engineering for patient arrival data
- [ ] Time-series decomposition of demand patterns
- [ ] Visualization of demand trends
- [ ] API endpoint for demand analytics

### Day 5 — Waiting Time Prediction
- [ ] Train regression model for waiting-time estimation
- [ ] Feature selection and model evaluation
- [ ] Model serialization (joblib)
- [ ] Prediction API endpoint

### Day 6 — Bed Occupancy Monitoring
- [ ] Occupancy rate computation and forecasting
- [ ] Classification model for occupancy levels
- [ ] Real-time monitoring API
- [ ] Dashboard occupancy charts

### Day 7 — Resource Allocation
- [ ] Staff and equipment utilization metrics
- [ ] Basic optimization model setup
- [ ] What-if scenario API endpoints
- [ ] Frontend scenario explorer

### Day 8 — Model Refinement & Testing
- [ ] Cross-validation and hyperparameter tuning
- [ ] Model comparison and selection
- [ ] Comprehensive ML test suite
- [ ] Performance benchmarks

---

## Phase 3: Integration & Dashboard (Days 9–12)

### Day 9 — Dashboard Core
- [ ] Full dashboard layout with Recharts visualizations
- [ ] Real-time data refresh
- [ ] Responsive design

### Day 10 — Interactive Features
- [ ] Date/department filters
- [ ] Scenario comparison tool
- [ ] Export functionality (CSV/PDF)

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
