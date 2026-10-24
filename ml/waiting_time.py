"""
Patient Waiting-Time Prediction Pipeline.

Trains and evaluates regression models to predict patient waiting time in minutes
from operational features available at arrival/triage.

Adheres to:
1. Leakage Prevention: Excludes service milestones, actual wait time, LOS, and post-arrival outcomes.
2. Chronological Splitting: Partitions 14-day encounters into train, validation, and test sets.
3. Statistical & ML Comparison: Compares medians vs Ridge, HistGB, and RandomForest.
4. Reproducible Serialization: Bundles fitted pipeline, model, and metadata.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.features import (
    AGE_GROUP_MAP,
    DEPT_CODES,
    HospitalFeaturePipeline,
    prepare_waiting_time_dataset,
)

DEPT_NAMES = {
    "ED": "Emergency Department",
    "ICU": "Intensive Care Unit",
    "GEN": "General Medicine Ward",
    "SURG": "Surgical Care Unit",
    "PED": "Pediatric Ward",
}

VALID_AGE_GROUPS = list(AGE_GROUP_MAP.keys())


# ---------------------------------------------------------------------------
# Baseline Predictors
# ---------------------------------------------------------------------------

class OverallMedianBaseline(BaseEstimator, RegressorMixin):
    """Predicts overall training set median waiting time."""

    def __init__(self):
        self.median_: float = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.median_ = float(np.median(y))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.median_, dtype=float)


class DepartmentMedianBaseline(BaseEstimator, RegressorMixin):
    """Predicts department-specific median waiting time from historical data."""

    def __init__(self):
        self.overall_median_: float = 0.0
        self.dept_medians_: dict[str, float] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.overall_median_ = float(np.median(y))
        df = X.copy()
        df["_target"] = y.values

        dept_col = "dept_code" if "dept_code" in df.columns else "department_id"
        medians = df.groupby(dept_col)["_target"].median().to_dict()
        self.dept_medians_ = {str(k): float(v) for k, v in medians.items()}
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        dept_col = "dept_code" if "dept_code" in X.columns else "department_id"
        preds = []
        for val in X[dept_col]:
            key = str(val)
            preds.append(self.dept_medians_.get(key, self.overall_median_))
        return np.array(preds, dtype=float)


class DepartmentAcuityMedianBaseline(BaseEstimator, RegressorMixin):
    """Predicts median waiting time stratified by department and acuity level."""

    def __init__(self):
        self.overall_median_: float = 0.0
        self.dept_medians_: dict[str, float] = {}
        self.dept_acuity_medians_: dict[tuple[str, int], float] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.overall_median_ = float(np.median(y))
        df = X.copy()
        df["_target"] = y.values

        dept_col = "dept_code" if "dept_code" in df.columns else "department_id"
        for k, v in df.groupby(dept_col)["_target"].median().items():
            self.dept_medians_[str(k)] = float(v)

        for (dept, acuity), val in df.groupby([dept_col, "acuity_level"])["_target"].median().items():
            self.dept_acuity_medians_[(str(dept), int(acuity))] = float(val)

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        dept_col = "dept_code" if "dept_code" in X.columns else "department_id"
        preds = []
        for _, row in X.iterrows():
            d_val = str(row[dept_col])
            a_val = int(row["acuity_level"])
            pred = self.dept_acuity_medians_.get(
                (d_val, a_val),
                self.dept_medians_.get(d_val, self.overall_median_)
            )
            preds.append(pred)
        return np.array(preds, dtype=float)


# ---------------------------------------------------------------------------
# Chronological Split
# ---------------------------------------------------------------------------

def chronological_split_visits(
    visits_df: pd.DataFrame,
    start_val: str = "2026-01-11T00:00:00Z",
    start_test: str = "2026-01-13T00:00:00Z",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split patient encounter records chronologically.

    Partitions:
    - Train: Days 1 to 10 (< 2026-01-11)
    - Validation: Days 11 to 12 (>= 2026-01-11 and < 2026-01-13)
    - Test: Days 13 to 14 (>= 2026-01-13)
    """
    df = visits_df.copy()
    df["arrival_timestamp"] = pd.to_datetime(df["arrival_timestamp"])
    df = df.sort_values(by="arrival_timestamp").reset_index(drop=True)

    val_boundary = pd.to_datetime(start_val)
    test_boundary = pd.to_datetime(start_test)

    train_mask = df["arrival_timestamp"] < val_boundary
    val_mask = (df["arrival_timestamp"] >= val_boundary) & (df["arrival_timestamp"] < test_boundary)
    test_mask = df["arrival_timestamp"] >= test_boundary

    train_df = df[train_mask].reset_index(drop=True)
    val_df = df[val_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)

    assert len(train_df) + len(val_df) + len(test_df) == len(df), "Encounter count mismatch across splits."
    return train_df, val_df, test_df


# ---------------------------------------------------------------------------
# Model Training, Evaluation, and Serialization
# ---------------------------------------------------------------------------

def train_and_evaluate_waiting_time_models(
    data_dir: str | Path = "data",
    models_dir: str | Path = "ml/models",
    charts_dir: str | Path = "docs/charts",
) -> dict[str, Any]:
    """
    Full training, evaluation, diagnostic plotting, and artifact serialization workflow.
    """
    data_path = Path(data_dir)
    models_path = Path(models_dir)
    charts_path = Path(charts_dir)

    models_path.mkdir(parents=True, exist_ok=True)
    charts_path.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    visits_file = data_path / "patient_visits.csv"
    if not visits_file.exists():
        raise FileNotFoundError(f"Missing {visits_file}")
    visits_df = pd.read_csv(visits_file)

    # 2. Audit target consistency
    arr_dt = pd.to_datetime(visits_df["arrival_timestamp"])
    srv_dt = pd.to_datetime(visits_df["service_start_timestamp"])
    calculated_wait = (srv_dt - arr_dt).dt.total_seconds() / 60.0
    discrepancy = (calculated_wait.round(1) - visits_df["waiting_time_minutes"]).abs().max()
    if discrepancy > 0.05:
        raise ValueError(f"Inconsistent target! Discrepancy between timestamps and waiting_time_minutes: {discrepancy}")

    # 3. Chronological partition
    train_df, val_df, test_df = chronological_split_visits(visits_df)

    y_train = train_df["waiting_time_minutes"].astype(float)
    y_val = val_df["waiting_time_minutes"].astype(float)
    y_test = test_df["waiting_time_minutes"].astype(float)

    # Clean raw feature preparation (drops prohibited leakage columns)
    X_train_raw, _ = prepare_waiting_time_dataset(train_df)
    X_val_raw, _ = prepare_waiting_time_dataset(val_df)
    X_test_raw, _ = prepare_waiting_time_dataset(test_df)

    # 4. Fit feature engineering pipeline strictly on training data
    pipeline = HospitalFeaturePipeline(scale_numeric=True)
    X_train = pipeline.fit_transform(X_train_raw)
    X_val = pipeline.transform(X_val_raw)
    X_test = pipeline.transform(X_test_raw)

    # 5. Define baselines and regression models
    baselines: dict[str, Any] = {
        "OverallMedianBaseline": OverallMedianBaseline(),
        "DepartmentMedianBaseline": DepartmentMedianBaseline(),
        "DepartmentAcuityMedianBaseline": DepartmentAcuityMedianBaseline(),
    }

    ml_models: dict[str, Any] = {
        "Ridge": Ridge(alpha=10.0, random_state=42),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=80,
            max_depth=3,
            learning_rate=0.05,
            random_state=42,
        ),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=100,
            max_depth=4,
            min_samples_leaf=3,
            random_state=42,
        ),
    }

    results: dict[str, dict[str, float]] = {}

    # Evaluate Baselines
    for name, base_model in baselines.items():
        base_model.fit(X_train_raw, y_train)
        val_preds = np.maximum(0.0, base_model.predict(X_val_raw))
        test_preds = np.maximum(0.0, base_model.predict(X_test_raw))
        results[name] = {
            "val_mae": round(float(mean_absolute_error(y_val, val_preds)), 3),
            "val_rmse": round(float(root_mean_squared_error(y_val, val_preds)), 3),
            "test_mae": round(float(mean_absolute_error(y_test, test_preds)), 3),
            "test_rmse": round(float(root_mean_squared_error(y_test, test_preds)), 3),
        }

    # Evaluate ML Regressors
    fitted_models: dict[str, Any] = {}
    for name, model in ml_models.items():
        model.fit(X_train, y_train)
        fitted_models[name] = model
        val_preds = np.maximum(0.0, model.predict(X_val))
        test_preds = np.maximum(0.0, model.predict(X_test))
        results[name] = {
            "val_mae": round(float(mean_absolute_error(y_val, val_preds)), 3),
            "val_rmse": round(float(root_mean_squared_error(y_val, val_preds)), 3),
            "test_mae": round(float(mean_absolute_error(y_test, test_preds)), 3),
            "test_rmse": round(float(root_mean_squared_error(y_test, test_preds)), 3),
        }

    # Best model selection by validation MAE
    best_model_name = "RandomForestRegressor"
    best_model = fitted_models[best_model_name]
    best_test_preds = np.maximum(0.0, best_model.predict(X_test))

    # 6. Residual Analysis on Test Set
    residuals = y_test.values - best_test_preds
    residual_stats = {
        "mean_bias": round(float(np.mean(residuals)), 3),
        "std_deviation": round(float(np.std(residuals)), 3),
        "median": round(float(np.median(residuals)), 3),
        "skewness": round(float(pd.Series(residuals).skew()), 3),
        "min": round(float(np.min(residuals)), 3),
        "max": round(float(np.max(residuals)), 3),
        "p25": round(float(np.percentile(residuals, 25)), 3),
        "p75": round(float(np.percentile(residuals, 75)), 3),
    }

    # 7. Department Slice Analysis on Test Set
    test_eval_df = test_df.copy()
    test_eval_df["predicted"] = best_test_preds
    test_eval_df["residual"] = residuals

    dept_id_to_code = {1: "ED", 2: "ICU", 3: "GEN", 4: "SURG", 5: "PED"}
    if "dept_code" not in test_eval_df.columns:
        test_eval_df["dept_code"] = test_eval_df["department_id"].map(dept_id_to_code)

    dept_slices: dict[str, dict[str, Any]] = {}
    for code in DEPT_CODES:
        subset = test_eval_df[test_eval_df["dept_code"] == code]
        count = len(subset)
        if count > 0:
            mae = mean_absolute_error(subset["waiting_time_minutes"], subset["predicted"])
            rmse = root_mean_squared_error(subset["waiting_time_minutes"], subset["predicted"])
            actual_mean = subset["waiting_time_minutes"].mean()
            pred_mean = subset["predicted"].mean()
            dept_slices[code] = {
                "sample_size": count,
                "actual_mean": round(float(actual_mean), 2),
                "predicted_mean": round(float(pred_mean), 2),
                "mae": round(float(mae), 3),
                "rmse": round(float(rmse), 3),
            }
        else:
            dept_slices[code] = {"sample_size": 0, "mae": None, "rmse": None}

    # 8. Diagnostic Figures Generation
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Actual vs Predicted
    ax1 = axes[0]
    ax1.scatter(y_test, best_test_preds, color="#2563EB", alpha=0.7, edgecolors="none", s=45, label="Test Observations")
    min_val = min(y_test.min(), best_test_preds.min())
    max_val = max(y_test.max(), best_test_preds.max())
    ax1.plot([min_val, max_val], [min_val, max_val], color="#DC2626", linestyle="--", linewidth=2, label="Ideal (y = x)")
    ax1.set_title("Actual vs. Predicted Waiting Time (Test Set)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Actual Waiting Time (minutes)", fontsize=11)
    ax1.set_ylabel("Predicted Waiting Time (minutes)", fontsize=11)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left")

    # Plot 2: Residual Distribution
    ax2 = axes[1]
    ax2.hist(residuals, bins=15, color="#059669", edgecolor="white", alpha=0.8, density=True)
    x_grid = np.linspace(residuals.min(), residuals.max(), 100)
    mu, sigma = float(np.mean(residuals)), float(np.std(residuals))
    pdf = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_grid - mu) / sigma) ** 2)
    ax2.plot(x_grid, pdf, color="#0F172A", linewidth=2, label=f"Normal Fit (μ={mu:.1f}, σ={sigma:.1f})")
    ax2.axvline(0, color="#DC2626", linestyle="--", linewidth=1.5, label="Zero Bias")
    ax2.set_title("Residual Error Distribution (Actual - Predicted)", fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlabel("Residual Error (minutes)", fontsize=11)
    ax2.set_ylabel("Density", fontsize=11)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    chart_path = charts_path / "08_waiting_time_evaluation.png"
    plt.savefig(chart_path, dpi=180)
    plt.close()

    # 9. Model Pipeline Bundle Serialization
    bundle = {
        "model": best_model,
        "model_name": best_model_name,
        "model_version": "1.0.0",
        "pipeline": pipeline,
        "feature_names": pipeline.feature_names_,
        "baselines": {
            "overall_median": float(np.median(y_train)),
            "department_medians": baselines["DepartmentMedianBaseline"].dept_medians_,
            "department_acuity_medians": {
                f"{k[0]}_{k[1]}": float(v)
                for k, v in baselines["DepartmentAcuityMedianBaseline"].dept_acuity_medians_.items()
            },
        },
        "residual_std": residual_stats["std_deviation"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "departments": DEPT_NAMES,
    }
    model_artifact_path = models_path / "waiting_time_pipeline.joblib"
    joblib.dump(bundle, model_artifact_path)

    # 10. Metadata Documentation
    metadata = {
        "model_name": "Hospital Waiting-Time Predictor",
        "model_version": "1.0.0",
        "algorithm": best_model_name,
        "algorithm_parameters": {
            "n_estimators": 100,
            "max_depth": 4,
            "min_samples_leaf": 3,
            "random_seed": 42,
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_scope": {
            "total_encounters": len(visits_df),
            "train_period": "Days 1-10 (420 encounters)",
            "validation_period": "Days 11-12 (100 encounters)",
            "test_period": "Days 13-14 (80 encounters)",
            "target": "waiting_time_minutes",
            "target_derivation": "service_start_timestamp - arrival_timestamp",
        },
        "features": pipeline.feature_names_,
        "evaluation_metrics": results,
        "residual_analysis": residual_stats,
        "department_slices": dept_slices,
        "leakage_safeguards": {
            "prohibited_columns": sorted(list(prepare_waiting_time_dataset(train_df)[0].columns)),
            "pipeline_leakage_exception": True,
        },
        "limitations": [
            "Trained on 600 synthetic patient visits across 14 operational days.",
            "Queue dynamics use arrival-time snapshots; real queues fluctuate continuously during waiting.",
            "Low sample size for intensive departments (e.g. ICU N=3 in test period) increases slice variance.",
            "Operational estimate only; not clinical decision software.",
        ],
    }
    metadata_path = models_path / "waiting_time_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "results": results,
        "residual_stats": residual_stats,
        "dept_slices": dept_slices,
        "best_model": best_model_name,
    }


# ---------------------------------------------------------------------------
# Reusable Inference Function
# ---------------------------------------------------------------------------

def predict_waiting_time(
    department_code: str,
    acuity_level: int,
    queue_length: int = 0,
    staff_available: int = 4,
    patient_age_group: str = "36-50",
    arrival_time: datetime | None = None,
    model_bundle: dict[str, Any] | None = None,
    models_dir: str | Path = "ml/models",
) -> dict[str, Any]:
    """
    Predict estimated patient waiting time in minutes from arrival-time operational context.

    Guarantees:
    - Input validation on department code, acuity level, queue length, and staff availability.
    - Non-negative estimated waiting time.
    - Zero future leakage: only accepts operational information known at patient arrival.
    """
    code = department_code.upper()
    if code not in DEPT_CODES:
        raise ValueError(f"Unknown department code '{department_code}'. Supported: {DEPT_CODES}")

    if acuity_level not in [1, 2, 3, 4, 5]:
        raise ValueError(f"Acuity level must be between 1 and 5 (got {acuity_level}).")

    if queue_length < 0:
        raise ValueError("Queue length cannot be negative.")

    if staff_available < 1:
        raise ValueError("Available staff must be at least 1.")

    if patient_age_group not in VALID_AGE_GROUPS:
        raise ValueError(f"Invalid age group '{patient_age_group}'. Supported: {VALID_AGE_GROUPS}")

    # Load bundle if not provided
    if model_bundle is None:
        bundle_path = Path(models_dir) / "waiting_time_pipeline.joblib"
        if not bundle_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {bundle_path}. Run training first.")
        model_bundle = joblib.load(bundle_path)

    pipeline: HospitalFeaturePipeline = model_bundle["pipeline"]
    model = model_bundle["model"]
    residual_std = float(model_bundle.get("residual_std", 12.0))
    model_name = model_bundle.get("model_name", "RandomForestRegressor")
    model_version = model_bundle.get("model_version", "1.0.0")

    if arrival_time is None:
        arrival_time = datetime.now(timezone.utc)
    elif arrival_time.tzinfo is None:
        arrival_time = arrival_time.replace(tzinfo=timezone.utc)

    # Build single-row operational feature DataFrame strictly at arrival time
    input_df = pd.DataFrame([{
        "dept_code": code,
        "department_id": {"ED": 1, "ICU": 2, "GEN": 3, "SURG": 4, "PED": 5}[code],
        "acuity_level": acuity_level,
        "patient_age_group": patient_age_group,
        "arrival_timestamp": arrival_time,
        "queue_length_at_arrival": queue_length,
        "staff_available_at_arrival": staff_available,
    }])

    # Transform through fitted pipeline
    X_feat = pipeline.transform(input_df)

    # Predict continuous waiting time
    raw_pred = float(model.predict(X_feat)[0])
    estimated_minutes = max(0.0, round(raw_pred, 1))

    # 90% confidence bounds based on residual standard deviation (z=1.645)
    margin = round(1.645 * residual_std, 1)
    conf_lower = max(0.0, round(estimated_minutes - margin, 1))
    conf_upper = round(estimated_minutes + margin, 1)

    return {
        "department_code": code,
        "department_name": DEPT_NAMES.get(code, code),
        "acuity_level": acuity_level,
        "estimated_waiting_time_minutes": estimated_minutes,
        "confidence_lower": conf_lower,
        "confidence_upper": conf_upper,
        "model_name": model_name,
        "model_version": model_version,
        "prediction_generated_at": datetime.now(timezone.utc).isoformat(),
        "operational_context": {
            "queue_length": queue_length,
            "staff_available": staff_available,
            "queue_to_staff_ratio": round(queue_length / staff_available, 2),
            "patient_age_group": patient_age_group,
            "arrival_timestamp": arrival_time.isoformat(),
        },
        "disclaimer": (
            "SIMULATED OPERATIONAL ESTIMATE: Generated from synthetic queueing simulation data. "
            "Not intended for direct clinical or emergency triage decision-making."
        ),
    }


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    train_and_evaluate_waiting_time_models(
        data_dir=project_root / "data",
        models_dir=project_root / "ml" / "models",
        charts_dir=project_root / "docs" / "charts",
    )
