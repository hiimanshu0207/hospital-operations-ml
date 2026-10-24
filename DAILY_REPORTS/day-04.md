# Day 04 — Patient Demand Forecasting with Machine Learning

**Date:** 2026-10-24 (Saturday)  
**Day:** 4 of 15  

---

## Today's Objective

Build a reproducible, leak-free patient-demand forecasting pipeline using Python, Pandas, NumPy, and scikit-learn to predict hourly patient arrivals per department. Audit the continuous hourly time series, establish naive and seasonal baselines, train multiple ML regressors under strict chronological splitting, serialize production-ready artifacts with metadata, expose an inference endpoint `POST /api/v1/predictions/demand`, and verify the entire system with comprehensive automated tests.

---

## Tasks Completed

| # | Task | Status |
|---|------|--------|
| 1 | Audited the synthetic time-series structure and built `build_continuous_hourly_demand_series()` generating 1,680 continuous hourly observations (including zero-arrival hours) across 5 departments over 14 days | ✅ Done |
| 2 | Verified timestamp timezone assumptions (UTC normalized) and strict chronological ordering | ✅ Done |
| 3 | Engineered leak-free prediction-time demand features (calendar, cyclical sine/cosine, department one-hot, historical lags, rolling statistics) | ✅ Done |
| 4 | Implemented chronological partitions: Days 3–10 (train, 960 rows), Days 11–12 (validation, 240 rows), Days 13–14 (test, 240 rows) with zero lookahead leakage | ✅ Done |
| 5 | Implemented statistical baseline predictors: `DepartmentMeanBaseline` and `SeasonalHourBaseline` | ✅ Done |
| 6 | Trained and evaluated scikit-learn regression models: `Ridge`, `HistGradientBoostingRegressor`, and `RandomForestRegressor` | ✅ Done |
| 7 | Conducted honest comparative evaluation across MAE and RMSE on identical validation and test periods | ✅ Done |
| 8 | Serialized model artifact to `ml/models/demand_forecast_model.joblib` (excluded from git) and documented reproducibility metadata in `ml/models/demand_model_metadata.json` | ✅ Done |
| 9 | Created Pydantic request/response schemas in `backend/app/schemas/prediction.py` with validation and simulation disclaimer | ✅ Done |
| 10 | Implemented REST endpoint `POST /api/v1/predictions/demand` in `backend/app/routers/predictions.py` with dynamic Poisson confidence bounds | ✅ Done |
| 11 | Added 10 new automated unit and API integration tests in `tests/test_ml/test_demand_forecast.py` and `tests/test_backend/test_api_predictions.py` | ✅ Done |
| 12 | Executed full test suite (53/53 passed) and verified frontend production build remains healthy | ✅ Done |

---

## Data & Time-Series Design

1. **Continuous Hourly Grid:**
   - Hospital patient visits arrive as discrete, irregularly spaced point processes. For hourly demand forecasting, discrete timestamps must be resampled into an uninterrupted continuous hourly interval grid.
   - Using `pd.date_range(start_hour, end_hour, freq="1h")` across all 5 departments (`ED`, `ICU`, `GEN`, `SURG`, `PED`), 336 hourly timestamps were constructed over 14 operational days.
   - Departments without arrivals in any specific hour were explicitly zero-filled, producing 1,680 total hourly department observations.
2. **Chronological Splitting:**
   - Shuffling time-series observations creates severe lookahead bias.
   - Days 1–2 (48 hours) serve as the historical warm-up window for computing lag features (`lag_24h`, `lag_48h`, `rolling_mean_24h`, `rolling_max_24h`).
   - **Training Set:** Days 3–10 (8 days, 192 hours × 5 departments = 960 observations).
   - **Validation Set:** Days 11–12 (2 days, 48 hours × 5 departments = 240 observations).
   - **Test Set:** Days 13–14 (2 days, 48 hours × 5 departments = 240 observations).
   - Zero overlap exists between train, validation, and test intervals.
3. **Features Available at Prediction Time:**
   - **Calendar/Temporal:** `hour`, `day_of_week`, `is_weekend`, `is_night_shift`, `is_peak_hours`.
   - **Cyclical Trigonometric:** `sin_hour`, `cos_hour`, `sin_day`, `cos_day` (preserving smooth boundary continuity between 23:00 and 00:00).
   - **Departmental:** One-hot encoded indicators (`dept_ED`, `dept_ICU`, `dept_GEN`, `dept_SURG`, `dept_PED`), `total_beds`, and `target_nurse_to_patient_ratio`.
   - **Autoregressive Lags:** Lagged arrivals from 24 hours ago (`lag_24h`) and 48 hours ago (`lag_48h`), plus rolling mean and max over the previous 24 hours. No current-hour or future outcome data is used.

---

## Baseline & Model Evaluation Results

### Model Performance Comparison

All models were evaluated on the identical holdout validation and test periods using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE):

| Model / Baseline | Val MAE | Val RMSE | Test MAE | Test RMSE | Description |
|------------------|---------|----------|----------|-----------|-------------|
| **DepartmentMeanBaseline** | 0.476 | 0.682 | 0.446 | 0.635 | Constant historical mean arrivals per department |
| **SeasonalHourBaseline** | 0.440 | 0.660 | **0.415** | 0.631 | Historical average for department × hour of day |
| **Ridge Regression** | 0.448 | 0.672 | 0.437 | **0.618** | Linear L2-regularized model on temporal & lag features |
| **HistGradientBoosting** | **0.426** | **0.663** | 0.457 | 0.676 | Gradient-boosted decision trees with histogram binning |
| **RandomForestRegressor** | 0.440 | **0.663** | 0.433 | **0.618** | Ensemble of 100 decision trees |

### Honest Comparison & Findings
1. **Low-Count Poisson Regime:**
   - In a 600-encounter synthetic dataset spanning 14 days, hourly arrivals per department range between 0 and 5 patients (with ~65% of hourly intervals recording 0 arrivals).
   - Under this low-count Poisson regime, variance across individual hours is dominated by discrete arrival noise rather than complex non-linear feature interactions.
2. **Seasonal Hour Baseline Strength:**
   - The `SeasonalHourBaseline` achieved the lowest Test MAE (**0.415**), outperforming `Ridge` (0.437), `RandomForest` (0.433), and `HistGradientBoosting` (0.457).
   - `Ridge` and `RandomForest` achieved the lowest Test RMSE (**0.618**), moderately better than the seasonal baseline's 0.631 by smoothing large variance swings.
   - Rather than forcing an unjustified claim of machine learning superiority, the pipeline honestly reports that the domain-specific `SeasonalHourBaseline` remains highly competitive and robust for low-volume hourly counts, and stores its seasonal profiles alongside regularized regressors.

---

## API Behavior (`POST /api/v1/predictions/demand`)

The FastAPI backend exposes the patient demand forecasting service under `/api/v1/predictions/demand`:

### Request
```json
{
  "department_code": "ED",
  "horizon_hours": 24,
  "start_timestamp": "2026-10-25T00:00:00Z"
}
```

### Response
```json
{
  "department_code": "ED",
  "department_name": "Emergency Department",
  "horizon_hours": 24,
  "start_timestamp": "2026-10-25T00:00:00Z",
  "end_timestamp": "2026-10-26T00:00:00Z",
  "model_version": "1.0.0",
  "algorithm": "SeasonalHourBaseline",
  "total_predicted_arrivals": 21.6,
  "forecasts": [
    {
      "timestamp": "2026-10-25T00:00:00Z",
      "hour": 0,
      "predicted_arrivals": 0.44,
      "confidence_lower": 0.0,
      "confidence_upper": 1.74
    },
    ...
  ],
  "disclaimer": "SIMULATED OPERATIONAL ESTIMATE: Generated from synthetic queueing simulation data. Not intended for direct clinical or emergency deployment."
}
```

### Key API Validations:
- **Case-Insensitive Department Lookup:** Accepts `"ed"`, `"ED"`, `"icu"`, etc.
- **Department Existence:** Returns HTTP `404 Not Found` for unrecognized codes (e.g. `"INVALID_DEPT"`).
- **Horizon Validation:** Restricts `horizon_hours` to `1 <= horizon_hours <= 168` (1 hour to 7 days), returning HTTP `422 Unprocessable Entity` for out-of-range values.
- **Model Availability:** Returns HTTP `503 Service Unavailable` if serialized artifacts are missing.
- **Confidence Intervals:** Calculates Poisson 90% confidence bounds (`[max(0, λ - 1.645*sqrt(λ)), λ + 1.645*sqrt(λ)]`) for each future hour.
- **Non-Negative Guarantee:** Forecast values are clipped at zero to guarantee physical validity.

---

## Automated Test Results

The full backend and ML test suite was executed:

```text
======================== 53 passed, 1 warning in 1.03s ========================
```

| Test File | Tests | Status | Scope |
|-----------|-------|--------|-------|
| `test_health.py` | 2 | ✅ Passed | System health endpoint |
| `test_models.py` | 5 | ✅ Passed | SQLAlchemy models and check constraints |
| `test_synthetic_generator.py` | 8 | ✅ Passed | Reproducible generator & validation |
| `test_api_departments.py` | 5 | ✅ Passed | Department CRUD endpoints |
| `test_api_beds.py` | 4 | ✅ Passed | Bed capacity & occupancy management |
| `test_api_visits.py` | 6 | ✅ Passed | Patient visit lifecycle & metrics |
| `test_data_quality.py` | 7 | ✅ Passed | Data integrity & duration constraints |
| `test_features.py` | 6 | ✅ Passed | Preprocessing, leakage prevention, target splits |
| `test_demand_forecast.py` | 6 | ✅ Passed | Time-series continuity, chronological split, lag features, artifact loading, inference bounds, input validation |
| `test_api_predictions.py` | 4 | ✅ Passed | Demand forecast endpoint, case insensitivity, 404 & 422 validations |
| **Total** | **53** | **✅ 53/53 Passed** | **Full system verification** |

**Frontend Production Build (`vite build`):**
```text
✓ 16 modules transformed.
dist/index.html                   0.63 kB │ gzip:  0.38 kB
dist/assets/index-C1YGgvjc.css   18.58 kB │ gzip:  3.91 kB
dist/assets/index-CL2XOwCN.js   222.68 kB │ gzip: 69.62 kB
✓ built in 134ms
```

---

## Known Limitations

1. **Dataset Volume:** The pipeline is trained on 600 synthetic encounters across 14 days (1,680 department-hours). This is a demonstration-scale dataset designed for architectural reproducibility, not real-world clinical deployment.
2. **High Sparsity in Intensive Units:** Departments like ICU have very low arrival rates (often 0 arrivals for multiple consecutive hours), meaning baseline diurnal averages capture typical flow as well as or better than parameterized trees.
3. **No External Shock Regimes:** Synthetic data reflects standard operational cycles; it does not model external catastrophes, epidemiological surges, or public health emergencies.

---

## Day 5 Recommendations (Waiting Time Prediction)

1. **Target Definition:** Transition from hourly aggregated demand counts to individual encounter-level waiting time (`waiting_time_minutes = service_start_timestamp - arrival_timestamp`).
2. **Feature Reuse:** Leverage `HospitalFeaturePipeline` engineered in Day 3 (`ml/features.py`), including arrival hour cyclical terms, triage acuity levels, queue lengths, and available staff.
3. **Model Selection:** Train and compare regression architectures (Gradient Boosting, Ridge, Random Forest) against department median wait-time baselines.
4. **Endpoint:** Implement `POST /api/v1/predictions/waiting-time` accepting patient triage and current department state to return expected wait times and confidence bands.
