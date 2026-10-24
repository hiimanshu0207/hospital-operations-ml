# Day 05 — Patient Waiting-Time Prediction using Machine Learning

**Date:** 2026-10-24 (Saturday)  
**Day:** 5 of 15  

---

## Today's Objective

Build, evaluate, and serialize a leak-free regression pipeline that predicts estimated patient waiting time in minutes from operational information available strictly at patient arrival/triage. Audit the target definition, verify consistency against timestamp differentials, establish statistical median baselines, train and compare regularized linear and ensemble models under strict chronological splitting, conduct thorough residual and department slice analyses, serialize the production artifact with complete metadata, implement the `POST /api/v1/predictions/waiting-time` endpoint, and verify the entire system with comprehensive automated tests.

---

## Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Audited `waiting_time_minutes` consistency: verified `service_start_timestamp - arrival_timestamp` matches target with 0.0m max discrepancy | ✅ Done |
| 2 | Enforced strict target leakage prevention: added `admission_required` to `PROHIBITED_LEAKAGE_COLUMNS` along with all post-arrival milestones | ✅ Done |
| 3 | Extracted 19 prediction-time operational features (temporal, cyclical sin/cos, queue length, staff availability, queue-to-staff ratio, triage acuity, demographics, department one-hot) | ✅ Done |
| 4 | Implemented chronological train/validation/test partitions: Days 1–10 (train, 420 encounters), Days 11–12 (val, 100 encounters), Days 13–14 (test, 80 encounters) | ✅ Done |
| 5 | Implemented statistical baseline predictors: `OverallMedianBaseline`, `DepartmentMedianBaseline`, and `DepartmentAcuityMedianBaseline` | ✅ Done |
| 6 | Trained and evaluated scikit-learn regressors: `Ridge`, `HistGradientBoostingRegressor`, and `RandomForestRegressor` | ✅ Done |
| 7 | Conducted honest comparative evaluation: `RandomForestRegressor` achieved the lowest Test MAE (**9.231m**) and lowest Test RMSE (**12.113m**) | ✅ Done |
| 8 | Performed residual analysis (mean bias: 0.056m, std: 12.113m, near-normal error distribution) and department slice evaluation | ✅ Done |
| 9 | Generated diagnostic evaluation visual figures (`docs/charts/08_waiting_time_evaluation.png`) | ✅ Done |
| 10 | Serialized production artifact to `ml/models/waiting_time_pipeline.joblib` (excluded from git) and documented reproducibility metadata in `ml/models/waiting_time_metadata.json` | ✅ Done |
| 11 | Created Pydantic schemas in `backend/app/schemas/prediction.py` and implemented REST endpoint `POST /api/v1/predictions/waiting-time` in `backend/app/routers/predictions.py` | ✅ Done |
| 12 | Added 16 new automated tests in `tests/test_ml/test_waiting_time.py` and `tests/test_backend/test_api_predictions.py` (total suite now 69 passing tests) | ✅ Done |
| 13 | Verified full test suite (69/69 passed) and confirmed frontend production build succeeds in ~226ms | ✅ Done |

---

## Target Audit & Leakage-Free Features

### 1. Target Definition & Consistency Audit
The operational target `waiting_time_minutes` represents the duration between a patient's arrival at the facility and the moment clinical treatment/service commences:
$$\text{waiting\_time\_minutes} = \frac{\text{service\_start\_timestamp} - \text{arrival\_timestamp}}{60 \text{ seconds}}$$

An automated audit across all 600 records in `data/patient_visits.csv` confirmed:
- **Maximum discrepancy:** `0.00 minutes` (100% mathematical consistency with recorded timestamps).
- **Distribution:** Mean = 41.43 min, Median = 37.85 min, Min = 0.60 min, Max = 127.80 min.
- **Physical Bounds:** Strictly non-negative; zero negative durations detected.

### 2. Leakage Elimination (`PROHIBITED_LEAKAGE_COLUMNS`)
Any information that becomes known only during or after patient service is strictly prohibited:
```python
PROHIBITED_LEAKAGE_COLUMNS = {
    "service_start_timestamp",
    "service_end_timestamp",
    "waiting_time_minutes",
    "length_of_stay_minutes",
    "total_duration_minutes",
    "admission_required",       # Clinical decision made post-triage
    "status",                   # Downstream encounter state
    "bed_id",                   # Physical bed assigned upon admission
}
```
If any of these columns are passed to `HospitalFeaturePipeline.fit()` or `transform()`, the pipeline immediately raises a `ValueError("Target Leakage Detected!")`.

### 3. Features Available at Prediction Time
The feature engineering pipeline extracts 19 features strictly available at patient arrival:
- **Queue Dynamics:** `queue_length`, `staff_available`, `queue_to_staff_ratio` ($\frac{\text{queue}}{\max(1, \text{staff})}$), `high_queue_flag` ($\ge 5$).
- **Triage Acuity & Demographics:** `acuity_level` (ESI 1–5), `is_critical_acuity` ($\le 2$), `age_group_code` (0–4 ordinal mapping).
- **Calendar & Shift:** `arrival_hour`, `arrival_day_of_week`, `is_weekend`, `is_night_shift` (22:00–06:00), `is_peak_hours` (10:00–19:00).
- **Cyclical Trigonometric Transforms:** `sin_hour`, `cos_hour`, `sin_day`, `cos_day` (preserving smooth circular continuity across 23:00 to 00:00 and Sunday to Monday).
- **Department One-Hot:** `dept_ED`, `dept_ICU`, `dept_GEN`, `dept_SURG`, `dept_PED`.

All numerical features are standardized using `StandardScaler` fitted **exclusively on the training partition**.

---

## Chronological Train / Validation / Test Methodology

To prevent temporal lookahead leakage and data snooping, the 14-day encounter timeline was partitioned chronologically:

| Split | Time Period | Encounters | Percentage | Description |
|---|---|---|---|---|
| **Train** | Days 1–10 (`< 2026-01-11T00:00:00Z`) | 420 | 70.0% | Model training and pipeline parameter fitting |
| **Validation** | Days 11–12 (`>= 2026-01-11` and `< 2026-01-13`) | 100 | 16.7% | Hyperparameter tuning and model selection |
| **Test** | Days 13–14 (`>= 2026-01-13T00:00:00Z`) | 80 | 13.3% | Unbiased final generalization evaluation |

- **Zero Temporal Overlap:** $\max(\text{Train}) < \min(\text{Val}) < \max(\text{Val}) < \min(\text{Test})$.
- **Fit Once:** Preprocessing scalers and encoders are fitted on the training split only and applied to validation and test splits independently.

---

## Baseline & Model Evaluation Results

All models were evaluated on the identical holdout validation and test sets using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) in minutes:

| Model / Architecture | Val MAE (min) | Val RMSE (min) | Test MAE (min) | Test RMSE (min) | Architecture Notes |
|---|---|---|---|---|---|
| **OverallMedianBaseline** | 19.731 | 25.432 | 19.700 | 25.262 | Historical training set median (37.85 min) |
| **DepartmentMedianBaseline** | 19.930 | 25.598 | 19.565 | 25.160 | Historical median per department |
| **DepartmentAcuityMedianBaseline** | 9.462 | 11.712 | 9.331 | 11.895 | Stratified median by (department, acuity) |
| **Ridge Regression** ($\alpha=10.0$) | 9.397 | 11.617 | 9.551 | 12.257 | L2-regularized linear model on all 19 features |
| **HistGradientBoosting** | 8.561 | **10.276** | 9.757 | 12.279 | Histogram-binned gradient-boosted trees ($d=3, \text{lr}=0.05$) |
| **RandomForestRegressor** (Selected) | **8.472** | 10.278 | **9.231** | **12.113** | Ensemble of 100 decision trees ($d=4, l=3$) |

### Comparative Analysis & Findings:
1. **The Critical Role of Triage Acuity:**
   - The simple `OverallMedianBaseline` (Test MAE: 19.70m) and `DepartmentMedianBaseline` (Test MAE: 19.56m) fail to distinguish between life-threatening emergencies and routine check-ups.
   - Adding acuity stratification (`DepartmentAcuityMedianBaseline`) drops Test MAE by over 10 minutes to **9.331m**, establishing that patient acuity is the primary driver of operational triage priority.
2. **Machine Learning Model Superiority:**
   - `RandomForestRegressor` with depth regularization ($d=4, \text{min\_samples\_leaf}=3$) achieved the lowest Test MAE (**9.231 min**) and lowest Test RMSE (**12.113 min**), outperforming the stratified baseline and linear Ridge regression.
   - HistGradientBoosting exhibited slight validation-to-test variance (Val MAE: 8.561m $\to$ Test MAE: 9.757m), whereas regularized RandomForest demonstrated superior generalization stability across the holdout test period.

---

## Residual Analysis & Department Slices

### 1. Residual Error Diagnostics (Test Set)
Residuals are defined as $\text{actual} - \text{predicted}$:
- **Mean Residual Bias:** **+0.056 minutes** (virtually unbiased estimator; no systematic under- or over-estimation).
- **Residual Standard Deviation ($\sigma$):** **12.113 minutes**.
- **Median Residual:** **+0.285 minutes**.
- **Skewness:** **-0.576** (slight left tail, close to symmetric).
- **Error Percentiles:**
  - 25th Percentile: -5.761 min
  - 50th Percentile: +0.285 min
  - 75th Percentile: +7.606 min
  - Interquartile Range (IQR): 13.367 minutes.
- **Diagnostic Visual Artifact:** Saved to `docs/charts/08_waiting_time_evaluation.png`, illustrating actual vs. predicted correlation along the $y=x$ identity line and Gaussian error density.

### 2. Performance by Department (Test Set Slice Evaluation)

| Department Code | Department Name | Sample Size ($N$) | Mean Actual Wait | Mean Predicted Wait | Slice MAE (min) | Slice RMSE (min) |
|---|---|---|---|---|---|---|
| **ED** | Emergency Department | 33 | 45.34m | 43.16m | 9.511 | 12.252 |
| **GEN** | General Medicine Ward | 22 | 43.91m | 43.25m | 9.429 | 11.475 |
| **ICU** | Intensive Care Unit | 3 | 39.20m | 37.66m | 5.404 | 5.700 |
| **SURG** | Surgical Care Unit | 10 | 49.83m | 50.66m | 8.081 | 9.885 |
| **PED** | Pediatric Ward | 12 | 32.31m | 38.85m | 10.016 | 15.308 |

> [!NOTE]
> In intensive units like the ICU ($N=3$ in the 2-day test holdout), the small sample size limits statistical power. Slices with $N \ge 20$ (ED, GEN) exhibit consistent MAE around 9.4–9.5 minutes.

---

## API Behavior (`POST /api/v1/predictions/waiting-time`)

The FastAPI backend exposes the waiting-time prediction service under `/api/v1/predictions/waiting-time`:

### Request
```json
{
  "department_code": "ED",
  "acuity_level": 3,
  "queue_length": 4,
  "staff_available": 3,
  "patient_age_group": "36-50"
}
```

### Response
```json
{
  "department_code": "ED",
  "department_name": "Emergency Department",
  "acuity_level": 3,
  "estimated_waiting_time_minutes": 27.6,
  "confidence_lower": 7.7,
  "confidence_upper": 47.5,
  "model_name": "RandomForestRegressor",
  "model_version": "1.0.0",
  "prediction_generated_at": "2026-10-24T17:56:46.940915Z",
  "operational_context": {
    "queue_length": 4,
    "staff_available": 3,
    "queue_to_staff_ratio": 1.33,
    "patient_age_group": "36-50",
    "arrival_timestamp": "2026-10-24T17:56:46.899124Z"
  },
  "disclaimer": "SIMULATED OPERATIONAL ESTIMATE: Generated from synthetic queueing simulation data. Not intended for direct clinical or emergency triage decision-making."
}
```

### Key API Validations:
- **Case-Insensitive Department Lookup:** Accepts `"ed"`, `"ED"`, `"gen"`, `"SURG"`, etc.
- **Department Existence:** Returns HTTP `404 Not Found` for unrecognized codes (e.g. `"NEUROLOGY"`).
- **Acuity Level Range:** Restricts `acuity_level` to integers $1 \le \text{acuity} \le 5$, returning HTTP `422 Unprocessable Entity` for invalid values.
- **Queue & Staff Bounds:** Restricts `queue_length >= 0` and `staff_available >= 1`, returning HTTP `422 Unprocessable Entity` for negative queues or zero staff.
- **Model Availability:** Returns HTTP `503 Service Unavailable` if serialized `.joblib` model artifact is missing.
- **Non-Negative Guarantee:** Estimated wait time and lower confidence bound are clipped at zero to guarantee physical plausibility.
- **Confidence Intervals:** Computes 90% prediction intervals ($z = 1.645$) based on the empirical test residual standard deviation ($\sigma = 12.11\text{m}$).

---

## Automated Test Results

The backend and ML test suite was executed across all 11 test modules:

```text
======================== 69 passed, 1 warning in 1.72s ========================
```

| Test Module | Tests | Status | Scope |
|---|---|---|---|
| `test_health.py` | 2 | ✅ Passed | Service health check endpoint |
| `test_models.py` | 5 | ✅ Passed | SQLAlchemy models, foreign keys & check constraints |
| `test_synthetic_generator.py` | 8 | ✅ Passed | Synthetic hospital data generator & schema validation |
| `test_api_departments.py` | 5 | ✅ Passed | Department CRUD endpoints |
| `test_api_beds.py` | 4 | ✅ Passed | Bed inventory & occupancy endpoints |
| `test_api_visits.py` | 6 | ✅ Passed | Patient visit lifecycle endpoints |
| `test_data_quality.py` | 7 | ✅ Passed | Zero negative duration, monotonic timestamps, bed capacities |
| `test_features.py` | 6 | ✅ Passed | Feature extraction, deterministic transformation, strict leakage checks |
| `test_demand_forecast.py` | 6 | ✅ Passed | Hourly arrival series, lag features, chronological split, demand model |
| `test_waiting_time.py` | 9 | ✅ Passed | Target consistency, chronological split, leakage guard, baselines, bundle loading, acuity monotonicity, bounds |
| `test_api_predictions.py` | 11 | ✅ Passed | Demand and waiting-time endpoints, 404, 422 validations, 503 fallback |
| **Total** | **69** | **✅ 69/69 Passed** | **Full system verification** |

**Frontend Production Build (`vite build`):**
```text
✓ 16 modules transformed.
dist/index.html                   0.63 kB │ gzip:  0.38 kB
dist/assets/index-C1YGgvjc.css   18.58 kB │ gzip:  3.91 kB
dist/assets/index-CL2XOwCN.js   222.68 kB │ gzip: 69.62 kB
✓ built in 226ms
```

---

## Synthetic Data Generator Limitations

1. **Stochastic Relationship Structure:**
   - The synthetic generator models waiting time as a piece-wise uniform random variable added to a linear ratio of queue to staff:
     $$\text{wait} \sim U(a_{\text{acuity}}, b_{\text{acuity}}) + \frac{\text{queue}}{\max(1, \text{staff})} \times c_{\text{acuity}}$$
   - While realistic for demonstrating triage priority dynamics, real hospital queueing involves non-linear queueing curves (Erlang-C delays) and heavy right-tailed distributions caused by unexpected resuscitation emergencies and bed blockage.
2. **Snapshot vs. Dynamic Queues:**
   - Operational features reflect a static snapshot captured at patient arrival. In actual operations, queue lengths and staffing levels evolve continuously between arrival and initial treatment.
3. **Small Sample Sizes in High-Acuity Units:**
   - Departments with low encounter volume (such as ICU with only 3 test arrivals) have high variance in slice metrics.

---

## Day 6 Recommendations (Bed Occupancy Monitoring)

1. **Occupancy Rate Metric Engine:** Compute historical hourly bed occupancy rates ($\frac{\text{occupied\_beds}}{\text{total\_beds}}$) across departments by mapping active intervals `[service_start_timestamp, service_end_timestamp]`.
2. **Classification & Early Warning Model:** Train a multi-class or binary model predicting near-capacity occupancy states ($>85\%$ and $>95\%$) 6–12 hours ahead.
3. **Real-Time Monitoring API:** Implement `/api/v1/monitoring/occupancy` returning department capacity status, active beds, and surge warning indicators.
4. **Dashboard Charts:** Connect frontend Recharts components to visualize department occupancy thresholds.
