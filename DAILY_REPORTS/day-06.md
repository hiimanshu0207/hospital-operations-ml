# Day 06 — Hospital Resource Optimization and What-if Simulation

**Date:** 2026-10-24 (Saturday)  
**Day:** 6 of 15  

---

## Today's Objective

Build a transparent, constraint-aware hospital resource optimization and what-if simulation module. Formulate mathematical and operational engines to analyze departmental bed utilization, staff availability by shift, queue pressures, and predictive waiting-time benchmarks; implement a pure, non-mutating what-if simulation engine to model the operational impact of arrival surges and staffing changes; engineer a constrained non-linear staff allocation optimizer using SciPy with rule-based baseline comparison; expose versioned FastAPI endpoints under `/api/v1/optimization`; and verify the entire system with comprehensive automated tests and frontend build checks.

---

## Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Built `calculate_department_utilization` computing bed utilization, shift/role staffing, nurse-to-patient ratios, queue pressures, and capacity alerts | ✅ Done |
| 2 | Enforced division-by-zero protection and missing data safeguards (e.g. `total_beds == 0` or unstaffed units handled gracefully) | ✅ Done |
| 3 | Clearly partitioned operational data sources: tagged `OBSERVED_DATABASE_STATE` vs. `ML_MODEL_ESTIMATE` | ✅ Done |
| 4 | Reused Day 5's serialized RandomForest waiting-time model (`predict_waiting_time`) for dynamic operational benchmark indicators | ✅ Done |
| 5 | Engineered `simulate_what_if_scenario` modeling patient arrival surges (-50% to +100%), staffing adjustments, and bed changes over custom horizons | ✅ Done |
| 6 | Verified strict data non-mutation during simulations (`pd.testing.assert_frame_equal` verified) | ✅ Done |
| 7 | Formulated constrained staff allocation optimization using SciPy (`SLSQP`) with objective balancing queue waiting pressure and reallocation churn | ✅ Done |
| 8 | Enforced hard operational constraints: exact total budget conservation, department minimum safety staffing, and physical capacity bounds | ✅ Done |
| 9 | Implemented Hamilton-Hare Largest Remainder integer rounding to guarantee integer headcount conservation | ✅ Done |
| 10 | Implemented transparent rule-based demand-ratio baseline allocator for algorithmic comparison | ✅ Done |
| 11 | Created Pydantic request/response schemas in `backend/app/schemas/optimization.py` | ✅ Done |
| 12 | Added FastAPI endpoints in `backend/app/routers/optimization.py`: `GET /utilization`, `POST /simulate`, `POST /allocate` | ✅ Done |
| 13 | Expanded automated test suite to 90 passing tests (11 new ML unit tests + 10 new API integration tests) | ✅ Done |
| 14 | Verified full test suite (90/90 passed) and confirmed frontend production build succeeds | ✅ Done |

---

## Resource and Capacity Analysis

The operational engine in [`ml/optimization.py`](file:///d:/Major%20Project/Hospital%20Operations%20&%20Workflow%20Optimization%20using%20Machine%20Learning/ml/optimization.py) processes hospital departments, bed inventories, active staff, and patient visits to produce a holistic operational audit:

### 1. Departmental Bed Utilization
- **Formula:** $\text{utilization\_pct} = \frac{\text{occupied\_beds}}{\max(1, \text{total\_beds})} \times 100\%$
- **Division-by-Zero Protection:** If `total_beds == 0`, utilization is set to `0.0%` with status `"NO_BEDS_CONFIGURED"`.
- **Status Classification:**
  - `NORMAL`: $< 70.0\%$
  - `ELEVATED`: $70.0\% \le \text{rate} < 85.0\%$
  - `HIGH`: $85.0\% \le \text{rate} < 95.0\%$
  - `CRITICAL_CAPACITY`: $\ge 95.0\%$

### 2. Staff Availability by Department & Shift
- Tracks active staff headcount across `Morning`, `Evening`, and `Night` shifts.
- Audits clinical role distribution (Doctors, Registered Nurses, Triage Nurses, Specialists).
- Compares available nurse headcount against mandatory clinical ratios:
  $$\text{required\_nurses} = \lceil \text{occupied\_beds} \times \text{target\_nurse\_to\_patient\_ratio} \rceil$$
  Flags `NURSE_RATIO_BREACH` if current nurse count falls below required staffing.

### 3. Queue Pressure and Demand
- Computes queue-to-staff ratio: $\frac{\text{recent\_queue\_estimate}}{\max(1, \text{active\_staff})}$.
- Categorizes operational pressure: `LOW` ($\le 0.5$), `MODERATE` ($0.5–1.0$), `HIGH` ($1.0–1.5$), `SEVERE` ($> 1.5$).

### 4. Predictive Waiting-Time Benchmarks
- Integrates Day 5's trained [`predict_waiting_time()`](file:///d:/Major%20Project/Hospital%20Operations%20&%20Workflow%20Optimization%20using%20Machine%20Learning/ml/waiting_time.py) to forecast benchmark waiting time for standard triage acuity (ESI 3) under the current department queue and staffing state.

### 5. Explicit Data Attribution
All returned payload blocks clearly declare provenance:
- Observed counts: `"data_source": "OBSERVED_DATABASE_STATE"`
- Inferred predictions: `"data_source": "ML_MODEL_ESTIMATE"`

---

## What-If Simulation Engine

The what-if simulator allows hospital administrators and nurse managers to test hypothetical operational scenarios without modifying ground-truth databases or production tables.

### 1. Scenario Parameters
- `arrival_surge_pct`: $-50.0\%$ to $+100.0\%$ patient arrival deviation.
- `staff_adjustments`: Departmental staff deltas (e.g. `{"ED": +2, "GEN": -1}`).
- `bed_capacity_adjustments`: Physical bed additions or closures (e.g. `{"ED": +5}`).
- `time_horizon_hours`: Simulation window (1 to 72 hours, default 12).
- `simulation_seed`: Integer seed for reproducible stochastic modeling.

### 2. Simulation Formulation
1. **Arrival Dynamics over Horizon:**
   $$\Delta \text{arrivals}_i = H \times \lambda_i \times \frac{\text{arrival\_surge\_pct}}{100}$$
   where $\lambda_i$ is baseline hourly arrival rate per department ($\text{ED}=2.0, \text{ICU}=0.4, \text{GEN}=1.2, \text{SURG}=0.6, \text{PED}=0.5$).
2. **Service Capacity Scaling:**
   $$\Delta \text{throughput}_i = H \times \left(\frac{\Delta \text{staff}_i}{3}\right) \times \mu_i$$
   where $\mu_i \approx 0.35$ patients cleared per nurse-hour.
3. **Net Simulated Queue Accumulation:**
   $$\text{sim\_queue}_i = \max\left(0, \text{base\_queue}_i + \lfloor 0.5 \times \Delta \text{arrivals}_i - \Delta \text{throughput}_i \rceil\right)$$
4. **Predictive Waiting-Time Re-estimation:**
   Evaluates $\hat{W}_i = f_{\text{RF}}(\text{sim\_queue}_i, \text{sim\_staff}_i, \text{ESI}=3)$ using Day 5's regression model.
5. **Bed Occupancy Impact:**
   Simulated admissions increase proportionally with arrivals; occupancy is bounded by physical beds:
   $$\text{sim\_occupied}_i = \min\left(\text{sim\_beds}_i, \max\left(0, \lfloor \text{base\_occupied}_i \times (1 + 0.3 \times \text{surge}) \rceil\right)\right)$$

### 3. Safety Guards
- Rejects staff reductions that breach departmental safety minimums (`DEFAULT_MIN_STAFF`).
- Rejects bed closures that exceed currently occupied beds (cannot evict active inpatients).
- Verifies that input operational DataFrames are 100% unmutated before and after simulation.

---

## Resource Allocation Optimizer

The optimizer solves a constrained non-linear resource allocation problem to rebalance available healthcare personnel across departments.

### 1. Mathematical Formulation
Let $s_i \in \mathbb{Z}^+$ be the staff assigned to department $i \in \{\text{ED}, \text{ICU}, \text{GEN}, \text{SURG}, \text{PED}\}$.

$$\min_{\{s_i\}} \sum_{i=1}^5 w_i \cdot \frac{q_i + 1.0}{s_i} + \lambda \sum_{i=1}^5 \frac{(s_i - s_i^{\text{current}})^2}{s_i^{\text{current}}}$$

**Subject to:**
1. **Total Headcount Conservation:** $\sum_{i=1}^5 s_i = S_{\text{budget}}$ (cannot invent or drop personnel).
2. **Department Safety Minimums:** $s_i \ge s_i^{\min}$ for all $i$ (e.g. ICU $\ge 3$, ED $\ge 4$ per shift).
3. **Physical Capacity Limits:** $s_i \le s_i^{\max}$ for all $i$ (supervisory and workstation caps).

- $w_i$: Clinical acuity priority weights ($\text{ICU}=2.5, \text{ED}=2.0, \text{SURG}=1.5, \text{PED}=1.5, \text{GEN}=1.0$).
- First term balances queue waiting pressure; second term regularizes against excessive operational disruption ($\lambda = 0.08$).

### 2. Solving Method
1. **Continuous Relaxation:** Solved using SciPy `scipy.optimize.minimize(method="SLSQP")` with bounds and equality constraint.
2. **Integer Headcount Conservation:** Continuous solution is converted to integers via the **Hamilton-Hare (Largest Remainder) Method**, ensuring the integer sum strictly equals $S_{\text{budget}}$ while respecting all $[s_i^{\min}, s_i^{\max}]$ bounds.
3. **Rule-Based Baseline Comparison:** Computes a transparent proportional allocation:
   $$\text{score}_i = w_i \times (q_i + \text{ratio}_i \times \text{occupied}_i)$$
   and outputs rule-based allocations alongside optimizer results for operational validation.

---

## API Endpoints (`/api/v1/optimization`)

### 1. `GET /api/v1/optimization/utilization`
Returns full departmental bed utilization, shift staffing, queue metrics, and capacity warnings.
```json
{
  "hospital_summary": {
    "total_beds": 122,
    "total_occupied_beds": 17,
    "total_available_beds": 105,
    "overall_bed_utilization_pct": 13.9,
    "total_active_staff": 84,
    "active_warning_count": 0,
    "operational_stress_index": 8.3
  },
  "department_utilization": [
    {
      "department_code": "ED",
      "department_name": "Emergency Department",
      "bed_capacity": {
        "total_beds": 25,
        "occupied_beds": 0,
        "available_beds": 25,
        "utilization_rate_pct": 0.0,
        "status": "NORMAL",
        "data_source": "OBSERVED_DATABASE_STATE"
      },
      "staffing": {
        "active_staff_total": 21,
        "nurse_count": 16,
        "target_nurse_to_patient_ratio": 0.35,
        "ratio_compliant": true
      },
      "estimated_wait_time": {
        "benchmark_acuity_level": 3,
        "estimated_minutes": 29.9,
        "data_source": "ML_MODEL_ESTIMATE"
      }
    }
  ]
}
```

### 2. `POST /api/v1/optimization/simulate`
Simulates arrival surges and staffing adjustments over custom horizons.
**Request:**
```json
{
  "arrival_surge_pct": 20.0,
  "staff_adjustments": {"ED": 2, "GEN": -1},
  "bed_capacity_adjustments": {"ED": 5},
  "time_horizon_hours": 12
}
```
**Response Summary:**
```json
{
  "overall_impact": {
    "average_baseline_wait_minutes": 33.6,
    "average_simulated_wait_minutes": 35.1,
    "net_wait_time_delta_minutes": 1.5,
    "surge_severity": "Moderate"
  },
  "department_comparisons": [ ... ]
}
```

### 3. `POST /api/v1/optimization/allocate`
Generates constraint-aware staffing recommendations.
**Request:**
```json
{
  "shift": "Morning",
  "total_staff_budget": 29
}
```
**Response Summary:**
```json
{
  "shift": "Morning",
  "total_staff_budget": 29,
  "total_allocated_staff": 29,
  "budget_conserved": true,
  "optimizer_status": "CONVERGED",
  "recommendations": [
    {
      "department_code": "ED",
      "current_staff": 7,
      "recommended_staff": 8,
      "net_change": 1,
      "minimum_staff_constraint": 4,
      "maximum_staff_constraint": 15,
      "rationale": "Allocate +1 staff to ED: High priority weight (2.0) and queue (2) exceed current coverage capacity."
    }
  ],
  "governance_notice": "DECISION SUPPORT NOTICE: Supervisory approval and staff credentials must be validated before executing reassignments."
}
```

---

## Automated Test Results

The backend and ML test suite was executed across all 13 test modules:

```text
======================= 90 passed, 5 warnings in 3.54s ========================
```

| Test File | Tests | Status | Scope |
|---|---|---|---|
| `test_health.py` | 2 | ✅ Passed | Health check endpoint |
| `test_models.py` | 5 | ✅ Passed | SQLAlchemy models, check constraints |
| `test_synthetic_generator.py` | 8 | ✅ Passed | Synthetic hospital data generator |
| `test_api_departments.py` | 5 | ✅ Passed | Department CRUD |
| `test_api_beds.py` | 4 | ✅ Passed | Bed capacity & occupancy management |
| `test_api_visits.py` | 6 | ✅ Passed | Patient visit lifecycle |
| `test_data_quality.py` | 7 | ✅ Passed | Temporal integrity, duration checks |
| `test_features.py` | 6 | ✅ Passed | Feature pipeline & leakage prevention |
| `test_demand_forecast.py` | 6 | ✅ Passed | Continuous time-series, demand model |
| `test_waiting_time.py` | 9 | ✅ Passed | Waiting-time model, baselines, residual stats |
| `test_api_predictions.py` | 11 | ✅ Passed | Demand & waiting time prediction endpoints |
| `test_optimization.py` | 11 | ✅ Passed | **Utilization math, div-by-zero, simulation determinism, non-mutation, SciPy budget conservation, bounds** |
| `test_api_optimization.py` | 10 | ✅ Passed | **API utilization, simulation 422s, allocation budget conservation, shift filtering** |
| **Total** | **90** | **✅ 90/90 Passed** | **Full system verification** |

**Frontend Production Build (`vite build`):**
```text
✓ 16 modules transformed.
dist/index.html                   0.63 kB │ gzip:  0.38 kB
dist/assets/index-C1YGgvjc.css   18.58 kB │ gzip:  3.91 kB
dist/assets/index-CL2XOwCN.js   222.68 kB │ gzip: 69.62 kB
✓ built in 180ms
```

---

## Known Assumptions & Limitations

1. **Synthetic Operational Scope:** Staff reallocation assumes cross-trained personnel eligible for reassignment across general units. In real clinical hospitals, specialized units (ICU, Pediatric, Surgical) require specific board certifications and clinical privileges.
2. **Steady-State Queue Approximation:** What-if simulation models queue accumulation using parameterized arrival rate deltas over fixed time horizons rather than stochastic event-driven queuing networks (M/M/c/K queues).
3. **Static Shift Allocations:** The optimizer operates at the shift level. Real-world intra-shift floating requires real-time nurse tracking and union/labor agreement constraints.

---

## Day 7 Recommendations (Resource Allocation & Scenario Explorer)

1. **Frontend Scenario Explorer:** Build interactive controls in the React frontend allowing users to adjust arrival surge sliders (-50% to +100%) and department staff toggles.
2. **Visual Utilization Gauges:** Render Recharts radial or bar gauges for department bed occupancy rates with color-coded warning thresholds (Green <70%, Amber 70–85%, Red >85%).
3. **What-If Impact Comparison View:** Render side-by-side diff cards displaying baseline vs. simulated waiting times and projected capacity bottlenecks.
4. **Shift Schedule Optimization:** Extend the allocation optimizer to generate multi-day shift rotation recommendations.
