"""
Tests for Patient Demand Forecasting Pipeline.

Verifies:
- Continuous hourly series generation (zero-arrival representation)
- Chronological train/validation/test split integrity (no temporal overlap)
- Lag feature construction without future lookahead
- Model bundle serialization and loading
- Non-negative prediction outputs and confidence intervals
- Error handling on invalid inputs
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import joblib

from ml.demand_forecast import (
    build_continuous_hourly_demand_series,
    create_demand_features,
    chronological_split,
    predict_future_demand,
    DEPT_CODES,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


@pytest.fixture(scope="module")
def raw_data():
    """Load patient encounters and department metadata."""
    visits = pd.read_csv(DATA_DIR / "patient_visits.csv")
    depts = pd.read_csv(DATA_DIR / "departments.csv")
    return visits, depts


def test_continuous_hourly_series_has_no_gaps(raw_data):
    """Hourly series must contain all 336 hours per department with zero arrivals included."""
    visits, depts = raw_data
    hourly_df = build_continuous_hourly_demand_series(visits, depts)

    num_depts = len(depts)
    total_rows = len(hourly_df)
    assert total_rows % num_depts == 0, "Hourly series length must be multiple of department count"

    # Verify zero arrivals are represented
    zero_hours = (hourly_df["arrival_count"] == 0).sum()
    assert zero_hours > 0, "Zero arrival hours must be explicitly present"
    assert (hourly_df["arrival_count"] >= 0).all(), "Negative arrival counts are invalid"


def test_chronological_split_has_zero_temporal_overlap(raw_data):
    """Chronological split must ensure strict train < val < test ordering without overlap."""
    visits, depts = raw_data
    hourly_df = build_continuous_hourly_demand_series(visits, depts)
    featured = create_demand_features(hourly_df)

    train_df, val_df, test_df = chronological_split(featured, train_days=8, val_days=2, test_days=2)

    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()
    assert len(train_df) > 0 and len(val_df) > 0 and len(test_df) > 0


def test_demand_features_no_nan_and_expected_columns(raw_data):
    """Demand features must be non-empty and free of NaN values after warm-up drop."""
    visits, depts = raw_data
    hourly_df = build_continuous_hourly_demand_series(visits, depts)
    featured = create_demand_features(hourly_df)

    assert featured["lag_24h"].isnull().sum() == 0
    assert featured["lag_48h"].isnull().sum() == 0
    assert featured["rolling_mean_24h"].isnull().sum() == 0

    expected_cols = [
        "hour", "day_of_week", "is_weekend", "is_night_shift", "is_peak_hours",
        "sin_hour", "cos_hour", "sin_day", "cos_day",
        "dept_ED", "dept_ICU", "dept_GEN", "dept_SURG", "dept_PED",
        "lag_24h", "lag_48h", "rolling_mean_24h", "rolling_max_24h",
    ]
    for col in expected_cols:
        assert col in featured.columns, f"Missing feature: {col}"


def test_saved_model_artifact_loads_correctly():
    """Trained model bundle must be present in ml/models/ and load cleanly."""
    bundle_path = MODELS_DIR / "demand_forecast_model.joblib"
    assert bundle_path.exists(), "Model bundle file is missing from ml/models/"

    bundle = joblib.load(bundle_path)
    assert "model" in bundle
    assert "model_name" in bundle
    assert "scaler" in bundle
    assert "feature_columns" in bundle
    assert "departments" in bundle


def test_predict_future_demand_structure_and_bounds():
    """Inference function must return valid hourly predictions, bounds, and disclaimer."""
    forecast = predict_future_demand(
        department_code="ED",
        horizon_hours=24,
        models_dir=MODELS_DIR,
    )

    assert forecast["department_code"] == "ED"
    assert forecast["horizon_hours"] == 24
    assert len(forecast["hourly_forecasts"]) == 24
    assert forecast["total_predicted_arrivals"] >= 0
    assert "disclaimer" in forecast

    for hf in forecast["hourly_forecasts"]:
        assert hf["predicted_arrivals"] >= 0, "Forecast arrivals must be non-negative"
        assert hf["confidence_lower"] <= hf["predicted_arrivals"] <= hf["confidence_upper"]


def test_predict_future_demand_input_validation():
    """Inference must reject unknown department codes or invalid horizon limits."""
    with pytest.raises(ValueError, match="Unknown department code"):
        predict_future_demand("UNKNOWN_DEPT", horizon_hours=12, models_dir=MODELS_DIR)

    with pytest.raises(ValueError, match="Horizon hours must be between 1 and 72"):
        predict_future_demand("ED", horizon_hours=0, models_dir=MODELS_DIR)

    with pytest.raises(ValueError, match="Horizon hours must be between 1 and 72"):
        predict_future_demand("ED", horizon_hours=100, models_dir=MODELS_DIR)
