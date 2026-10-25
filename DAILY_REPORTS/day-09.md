# Day 09 — End-to-End Testing and Model Validation

**Date:** 2026-10-25 (Sunday)  
**Day:** 9 of 15  

---

## 1. Executive Summary

Day 9 focused on rigorous end-to-end testing, model validation, and edge-case auditing across the complete full-stack **Hospital Operations & Workflow Optimization** system. We verified that all six operational dashboard views communicate seamlessly with FastAPI backend endpoints, confirmed strict constraint enforcement (safety staffing minimums, bed eviction prevention, integer workforce conservation), validated reproducibility and clinical acuity monotonicity, and audited feature pipelines to guarantee zero target leakage.

During testing, three defects were identified and resolved:
1. **Bed Summary Route Collision:** `GET /api/v1/beds/summary` was matching `GET /api/v1/beds/{bed_id}`, returning 422 for string ID `"summary"`. Added explicit `BedSummaryResponse` and re-ordered the `/summary` route before `/{bed_id}`.
2. **Missing Department Metrics Route:** `api.js` had `getDepartmentMetrics(id)` pointing to `/api/v1/departments/{id}/metrics` which was unmapped. Added route alias in `departments.py`.
3. **Operational Stress Index Scaling in UI:** `OverviewTab.jsx` used 0.0–1.0 thresholds (`>= 0.7` for Critical) for an index computed on a 0.0–100.0 scale, improperly flagging normal operations as "Critical Stress". Corrected to `>= 70.0` and formatted as `${stressIndex.toFixed(1)} / 100`.

The test suite expanded from 90 to **115 automated tests** (22 new E2E validation tests), all passing cleanly. Oxlint reported 0 errors and 0 warnings, and Vite production build succeeded in 1.72s.

---

## 2. Six Dashboard Views — Live Endpoint Verification

| View | Primary Endpoints | Method | Verified Status | Payload / Query | Response Telemetry |
|------|-------------------|--------|-----------------|-----------------|--------------------|
| **1. Overview** | `/health`<br>`/api/v1/optimization/utilization`<br>`/api/v1/patient-visits/summary`<br>`/api/v1/patient-visits/recent` | GET<br>GET<br>GET<br>GET | 200 OK<br>200 OK<br>200 OK<br>200 OK | None<br>None<br>None<br>`?limit=8` | Real-time bed occupancy, active staff count, operational stress index (0–100 scale), encounter stream |
| **2. Department Operations** | `/api/v1/optimization/utilization`<br>`/api/v1/departments`<br>`/api/v1/departments/{id}/metrics` | GET<br>GET<br>GET | 200 OK<br>200 OK<br>200 OK | None<br>None<br>`id=1..5` | 5 departments (`ED`, `ICU`, `GEN`, `SURG`, `PED`), nurse-to-patient ratio compliance, queue pressure |
| **3. Demand Forecasting** | `/api/v1/predictions/demand` | POST | 200 OK | `{"department_code": "ED", "horizon_hours": 24}` | Hourly arrival forecasts, Poisson 95% confidence intervals, non-negative bounds |
| **4. Waiting-Time Prediction** | `/api/v1/predictions/waiting-time` | POST | 200 OK | `{"department_code": "ED", "acuity_level": 3, "queue_length": 5, "staff_available": 4}` | Estimated minutes to triage, 95% uncertainty interval, clinical explanation |
| **5. What-If Simulation** | `/api/v1/optimization/simulate` | POST | 200 OK | `{"arrival_surge_pct": 20, "staff_adjustments": {"ED": 2, "GEN": -1}, "time_horizon_hours": 12}` | Baseline vs. simulated comparison, projected queue deltas, capacity warnings |
| **6. Staff Allocation** | `/api/v1/optimization/allocate` | POST | 200 OK | `{"shift": "Morning", "total_staff_budget": 84}` | SciPy SLSQP optimization, integer headcount conservation, safety bound enforcement |

---

## 3. Constraint Validation & Optimization Auditing

1. **Workforce Headcount Conservation:**
   - Evaluated across all shifts (`All`, `Morning`, `Evening`, `Night`) and explicit budgets ($B \in [20, 150]$).
   - $\sum_{i=1}^{5} \text{Allocated Staff}_i = \text{Staff Budget}$ strictly holds via Hamilton-Hare largest-remainder integer rounding (0 fractional staff).
   - Confirmed `budget_conserved == True` on all runs.
2. **Staff Safety Minimums Enforcement:**
   - Both optimization and what-if simulation reject adjustments that violate mandatory departmental minimums (`ED: 4`, `ICU: 3`, `GEN: 4`, `SURG: 2`, `PED: 2`).
   - Reducing ED staff by -20 returns **422 Unprocessable Entity** with `detail: "Staffing for ED cannot be reduced below safety minimum of 4"`.
   - Insufficient staff budget ($B < \sum \text{Min Staff}$) is rejected with **422 Unprocessable Entity**.
3. **Bed Capacity & Eviction Prevention:**
   - Reducing bed capacity below current occupied census (e.g. ICU -20 beds while 1 bed is occupied) returns **422 Unprocessable Entity** (`detail: "Bed capacity for ICU cannot be reduced to -8 while 1 beds are occupied"`).
4. **Non-Mutating State Isolation:**
   - What-if simulation operates exclusively on deep copies; database entities remain unchanged.

---

## 4. Model Validation, Reproducibility & Leakage Safeguards

1. **Target Leakage Safeguard:**
   - Verified that `HospitalFeaturePipeline` enforces `PROHIBITED_LEAKAGE_COLUMNS`:
     - `service_start_timestamp`
     - `service_end_timestamp`
     - `waiting_time_minutes`
     - `length_of_stay_minutes`
     - `total_duration_minutes`
     - `admission_required`
     - `status`
     - `bed_id`
   - Injecting any of these into training or inference DataFrames raises an explicit `ValueError`.
2. **Clinical Acuity Monotonicity:**
   - Tested triage waiting times across ESI levels 1 to 5 with fixed queue ($N=5$) and staff ($S=4$):
     - **ESI 1 (Resuscitation):** $\approx 2.4$ minutes (Immediate care)
     - **ESI 2 (Emergent):** $\approx 10.9$ minutes
     - **ESI 3 (Urgent):** $\approx 25.4$ minutes
     - **ESI 4 (Less Urgent):** $\approx 42.1$ minutes
     - **ESI 5 (Non-Urgent):** $\approx 58.7$ minutes
   - Confirmed strict ordering: $\text{Wait}(\text{ESI 1}) < \text{Wait}(\text{ESI 2}) < \text{Wait}(\text{ESI 3}) < \text{Wait}(\text{ESI 4}) < \text{Wait}(\text{ESI 5})$.
3. **Output Non-Negativity:**
   - All predicted arrival counts, waiting times, and bed occupancies are bounded at $\ge 0.0$.
4. **Prediction Reproducibility:**
   - Repeated calls with identical inputs and seeds return bitwise-identical prediction values ($MAE_{\Delta} = 0.000$).
5. **Artifact Resilience:**
   - When model `.joblib` files are temporarily unavailable, prediction endpoints gracefully return **503 Service Unavailable** with diagnostic instructions, rather than crashing with 500.

---

## 5. Model Metrics Review & Synthetic Dataset Limitations

### Demand Forecasting Pipeline
- **Selected Model:** `SeasonalHourBaseline` (MAE: 0.415, RMSE: 0.631 on test set).
- **Comparison:**
  - Ridge Regression: Test MAE 0.437, RMSE 0.618
  - HistGradientBoosting: Test MAE 0.457, RMSE 0.676
  - Random Forest: Test MAE 0.433, RMSE 0.618
  - Department Mean Baseline: Test MAE 0.446, RMSE 0.635

### Waiting-Time Regression Pipeline
- **Selected Model:** `RandomForestRegressor` (`n_estimators=100, max_depth=4, min_samples_leaf=3`)
- **Metrics on Test Set (Days 13–14, 80 encounters):**
  - MAE: **9.231 minutes**
  - RMSE: **12.113 minutes**
  - Baseline (Overall Median): MAE 19.700 minutes, RMSE 25.262 minutes
  - Baseline (Dept + Acuity Median): MAE 9.331 minutes, RMSE 11.895 minutes
- **Residual Analysis:** Mean bias = 0.056 min, standard deviation = 12.113 min, 50% of residuals within $[-5.76, +7.61]$ min.

### Honest Documentation of Dataset Limitations
> [!WARNING]
> **Academic and Synthetic Dataset Constraints:**
> 1. **Small Sample Size:** The current dataset consists of only 600 total patient visits over a 14-day observation window. Sub-cohort slices (e.g., ICU test encounters = 3) are too small for statistically powered clinical sub-group analysis.
> 2. **Poisson Noise Dominance:** At 0–5 arrivals per department per hour, stochastic integer noise dominates, explaining why complex non-linear models do not dramatically outperform seasonal baselines.
> 3. **Non-Clinical Deployment:** This system is an academic decision-support prototype. It is **not clinically certified** or validated for real triage, clinical prioritization, or medical diagnosis. All views prominently display research disclaimers.

---

## 6. Verification & Test Commands

### 1. Pytest Backend & ML Test Suite
```powershell
.\backend\venv\Scripts\python.exe -m pytest -c pytest.ini
```
**Output:**
```
======================= 115 passed, 9 warnings in 6.28s =======================
```
- 22/22 end-to-end validation tests in `tests/test_backend/test_e2e_validation.py` passed.
- 93/93 existing unit/integration tests passed with 0 regressions.

### 2. Frontend Linting (`oxlint`)
```powershell
node node_modules/oxlint/bin/oxlint
```
**Output:**
```
Found 0 warnings and 0 errors.
Finished in 23ms on 17 files with 104 rules using 18 threads.
```

### 3. Frontend Production Build (`vite build`)
```powershell
node node_modules/vite/bin/vite.js build
```
**Output:**
```
vite v8.3.5 building client environment for production...
✓ 658 modules transformed.
dist/index.html                   0.63 kB │ gzip:   0.38 kB
dist/assets/index-Bweos3D2.css   59.58 kB │ gzip:   8.93 kB
dist/assets/index-CPkn_qnu.js   699.60 kB │ gzip: 206.49 kB
✓ built in 1.72s
```

---

## 7. Git Diff & Push Status

- **Status:** All changes audited; zero `.db`, `.pyc`, `.env`, or secrets committed.
- **Commit Message:** `test: add end-to-end validation and model verification suite`
- **Target Branch:** `origin/main`
