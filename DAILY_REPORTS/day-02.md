# Day 02 — Hospital Domain Models & Synthetic Dataset

**Date:** 2026-10-24 (Saturday)  
**Day:** 2 of 15  

---

## Today's Objective

Design and implement core hospital operational domain models in SQLAlchemy, configure SQLite persistence, build a reproducible and strictly validated synthetic dataset generator using Pandas and NumPy, expose REST CRUD endpoints in FastAPI, and establish automated test coverage.

---

## Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Designed hospital domain entities (Departments, Staff, Beds, Patient Visits) | ✅ Done |
| 2 | Implemented SQLAlchemy ORM models with integrity check constraints | ✅ Done |
| 3 | Configured SQLite persistence with `init_db()` table auto-generation | ✅ Done |
| 4 | Verified `.gitignore` excludes SQLite database files (`*.db`, `*.sqlite3`) | ✅ Done |
| 5 | Built reproducible synthetic generator (`SyntheticHospitalDataGenerator`, `seed=42`) | ✅ Done |
| 6 | Generated non-identifying operational records (arrivals, queues, staff, service times, LOS) | ✅ Done |
| 7 | Added strict validation preventing negative durations, timestamp inversion, duplicate IDs, and bed overflow | ✅ Done |
| 8 | Exported 4 validated CSV datasets to `data/` (`departments`, `staff`, `beds`, `patient_visits`) | ✅ Done |
| 9 | Created Pydantic schemas with request validation in `app/schemas/` | ✅ Done |
| 10 | Implemented FastAPI CRUD endpoints for departments, beds, and patient visits | ✅ Done |
| 11 | Added `/api/v1/visits/metrics/summary` endpoint for aggregated operational analytics | ✅ Done |
| 12 | Added `/api/v1/admin/seed` endpoint and CLI script `seed.py` | ✅ Done |
| 13 | Built unit and integration tests across models, generator, and API routes | ✅ Done (30/30 passed) |
| 14 | Re-verified frontend production build (`vite build`) remains clean | ✅ Done (16 modules, 178ms) |

---

## Domain Architecture & Database Models

### 1. Departments (`departments`)
- **Key Columns:** `id`, `code` (unique, e.g. "ED", "ICU", "GEN", "SURG", "PED"), `name`, `total_beds`, `target_nurse_to_patient_ratio`, `created_at`
- **Relationships:** One-to-many with Staff, Beds, and PatientVisits.

### 2. Staff & Assignments (`staff`)
- **Key Columns:** `id`, `staff_id` (unique, e.g. "STF-ED-001"), `role` ("Doctor", "Registered Nurse", "Triage Nurse", etc.), `department_id` (FK), `shift` ("Morning", "Evening", "Night"), `is_active`
- **Relationships:** Many-to-one with Department.

### 3. Beds & Occupancy (`beds`)
- **Key Columns:** `id`, `bed_number` (unique, e.g. "ED-B01"), `department_id` (FK), `bed_type` ("Emergency", "ICU", "Standard", "Pediatric"), `is_occupied` (bool)
- **Relationships:** Many-to-one with Department; One-to-many with PatientVisits.

### 4. Synthetic Patient Visits (`patient_visits`)
- **Key Columns:** `id`, `visit_id` (unique synthetic code, e.g. "VIS-2026-00001"), `department_id` (FK), `patient_age_group` (categorical: "0-17", "18-35", "36-50", "51-65", "65+"), `acuity_level` (1=Resuscitation to 5=Non-urgent), `arrival_timestamp`, `queue_length_at_arrival`, `staff_available_at_arrival`, `service_start_timestamp`, `service_end_timestamp`, `waiting_time_minutes`, `length_of_stay_minutes`, `total_duration_minutes`, `admission_required`, `bed_id` (FK, nullable), `status`
- **Integrity Constraints:** Database check constraints enforcing `waiting_time_minutes >= 0`, `length_of_stay_minutes >= 0`, `total_duration_minutes >= 0`, `acuity_level BETWEEN 1 AND 5`, `queue_length_at_arrival >= 0`, `staff_available_at_arrival >= 0`.

---

## Synthetic Dataset Specification

- **Reproducibility:** Fully deterministic given random seed (`seed=42`).
- **Scale:** 5 Departments, 84 Staff, 122 Physical Beds, 600 Patient Encounters over 14 days.
- **Queue & Wait Dynamics:** High-acuity encounters (ESI 1-2) experience immediate/rapid care (< 15 mins), while lower-acuity cases scale dynamically with queue length and on-duty staff.
- **Bed Capacity Constraint:** At all points in simulated time, occupied beds never exceed total department capacity.
- **Exported Files:**
  - `data/departments.csv` (5 records)
  - `data/staff.csv` (84 records)
  - `data/beds.csv` (122 records)
  - `data/patient_visits.csv` (600 records)

---

## Files Created / Modified

### Backend Models & Schemas
- `backend/app/models/department.py` — Department ORM model
- `backend/app/models/staff.py` — Staff member & shift model
- `backend/app/models/bed.py` — Bed inventory & occupancy model
- `backend/app/models/patient_visit.py` — Patient encounter model with check constraints
- `backend/app/models/__init__.py` — Package export
- `backend/app/schemas/department.py` — Department Pydantic schemas
- `backend/app/schemas/staff.py` — Staff Pydantic schemas
- `backend/app/schemas/bed.py` — Bed Pydantic schemas & occupancy update
- `backend/app/schemas/patient_visit.py` — Visit schemas with validation
- `backend/app/schemas/__init__.py` — Package export

### Backend Routers & Services
- `backend/app/routers/departments.py` — CRUD endpoints for departments
- `backend/app/routers/beds.py` — Bed listing, filters, and capacity-safe occupancy update
- `backend/app/routers/patient_visits.py` — Encounter management & metrics summary
- `backend/app/routers/admin.py` — Admin database seed endpoint
- `backend/app/routers/__init__.py` — Package export
- `backend/app/services/synthetic_generator.py` — Synthetic data generator & validator
- `backend/app/services/__init__.py` — Package export
- `backend/app/database.py` — Updated with `init_db()` helper
- `backend/app/main.py` — Configured database lifespan & included `/api/v1` routes
- `backend/seed.py` — CLI database seeding script

### Tests
- `tests/conftest.py` — Isolated in-memory SQLite fixtures & TestClient overrides
- `tests/test_backend/test_models.py` — Model creation & integrity constraint tests
- `tests/test_backend/test_synthetic_generator.py` — Generator reproducibility & validation tests
- `tests/test_backend/test_api_departments.py` — Department API tests
- `tests/test_backend/test_api_beds.py` — Bed API & occupancy tests
- `tests/test_backend/test_api_visits.py` — Visit API & validation tests

### Data
- `data/departments.csv`
- `data/staff.csv`
- `data/beds.csv`
- `data/patient_visits.csv`

---

## Tests & Results

| Test Suite | Tests | Result | Execution Time |
| :--- | :--- | :--- | :--- |
| `test_health.py` | 2 | ✅ Passed | 0.08s |
| `test_models.py` | 5 | ✅ Passed | 0.12s |
| `test_synthetic_generator.py` | 8 | ✅ Passed | 0.19s |
| `test_api_departments.py` | 5 | ✅ Passed | 0.11s |
| `test_api_beds.py` | 4 | ✅ Passed | 0.10s |
| `test_api_visits.py` | 6 | ✅ Passed | 0.12s |
| **Total Automated Tests** | **30** | **✅ 30/30 Passed** | **0.72s** |
| **Frontend Production Build** | `vite build` | **✅ Passed** (16 modules) | **178ms** |

---

## Known Issues & Blockers

| Issue | Severity | Status / Resolution |
| :--- | :--- | :--- |
| **`&` in workspace directory path** | 🟡 Medium | Direct `npm run` commands fail due to path parsing at `&`. Direct binary invocation (`node node_modules/vite/bin/vite.js build`) works smoothly. |

---

## Next Day's Tasks (Day 3)

1. Build data exploration and descriptive statistics module (summary stats, arrival distributions, wait-time percentiles).
2. Create specialized analytics API endpoints for operational dashboards.
3. Build frontend navigation bar and dashboard layout using React Router and Tailwind CSS.
4. Integrate initial KPI summary cards (total visits, average waiting time, bed occupancy rate).
