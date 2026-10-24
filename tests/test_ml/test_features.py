"""
Tests for ML feature engineering and leakage prevention pipeline.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from ml.features import (
    HospitalFeaturePipeline,
    extract_prediction_time_features,
    prepare_waiting_time_dataset,
    get_waiting_time_target,
    get_hourly_demand_series,
    PROHIBITED_LEAKAGE_COLUMNS,
)

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "patient_visits.csv"


@pytest.fixture(scope="module")
def raw_visits():
    """Load sample patient visits dataset."""
    return pd.read_csv(DATA_PATH)


def test_extract_prediction_time_features_columns(raw_visits):
    """Raw feature extraction must generate all expected temporal and operational features."""
    features = extract_prediction_time_features(raw_visits.head(20))

    expected_cols = [
        "arrival_hour", "arrival_day_of_week", "is_weekend", "is_night_shift", "is_peak_hours",
        "sin_hour", "cos_hour", "sin_day", "cos_day",
        "queue_length", "staff_available", "queue_to_staff_ratio", "high_queue_flag",
        "acuity_level", "is_critical_acuity", "age_group_code", "dept_code"
    ]
    for col in expected_cols:
        assert col in features.columns, f"Feature column missing: {col}"

    assert features["arrival_hour"].between(0, 23).all()
    assert features["arrival_day_of_week"].between(0, 6).all()
    assert features["is_weekend"].isin([0, 1]).all()
    assert (features["queue_to_staff_ratio"] >= 0).all()


def test_deterministic_preprocessing(raw_visits):
    """Pipeline transformation must be deterministic given identical input data."""
    X_raw, _ = prepare_waiting_time_dataset(raw_visits.head(50))

    pipe1 = HospitalFeaturePipeline()
    res1 = pipe1.fit_transform(X_raw)

    pipe2 = HospitalFeaturePipeline()
    res2 = pipe2.fit_transform(X_raw)

    pd.testing.assert_frame_equal(res1, res2)


def test_target_separation_and_leakage_absence(raw_visits):
    """prepare_waiting_time_dataset must cleanly separate X and y without leakage."""
    X_raw, y = prepare_waiting_time_dataset(raw_visits)

    # Target checks
    assert isinstance(y, pd.Series)
    assert len(y) == len(raw_visits)
    assert (y >= 0).all()

    # Leakage checks on X_raw
    leaked = set(X_raw.columns).intersection(PROHIBITED_LEAKAGE_COLUMNS)
    assert len(leaked) == 0, f"Target leakage detected in X_raw: {leaked}"


def test_pipeline_raises_error_on_target_leakage(raw_visits):
    """Pipeline must actively raise ValueError if prohibited outcome columns are present in features."""
    pipe = HospitalFeaturePipeline()

    # Intentionally supply raw data that includes waiting_time_minutes and service_end_timestamp
    with pytest.raises(ValueError, match="Target Leakage Detected"):
        pipe.fit(raw_visits.head(30))

    # Clean fit, but leaked transform
    clean_X, _ = prepare_waiting_time_dataset(raw_visits.head(30))
    pipe.fit(clean_X)

    with pytest.raises(ValueError, match="Target Leakage Detected"):
        pipe.transform(raw_visits.head(30))


def test_strict_featurization_train_test_split(raw_visits):
    """Encoders and scalers must fit ONLY on the training split and transform test set independently."""
    X_raw, y = prepare_waiting_time_dataset(raw_visits)

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.25, random_state=42, shuffle=False
    )

    pipeline = HospitalFeaturePipeline(scale_numeric=True)
    X_train_feat = pipeline.fit_transform(X_train_raw)
    X_test_feat = pipeline.transform(X_test_raw)

    assert X_train_feat.shape[1] == X_test_feat.shape[1]
    assert list(X_train_feat.columns) == list(X_test_feat.columns)
    assert len(X_train_feat) == len(X_train_raw)
    assert len(X_test_feat) == len(X_test_raw)


def test_get_hourly_demand_series(raw_visits):
    """Hourly demand aggregation must produce a valid continuous time-series."""
    demand = get_hourly_demand_series(raw_visits)

    assert isinstance(demand.index, pd.DatetimeIndex)
    assert "arrival_count" in demand.columns
    assert (demand["arrival_count"] >= 0).all()
    assert demand["arrival_count"].sum() == len(raw_visits)
