"""
Tests for ML waiting-time prediction pipeline, baselines, leakage prevention, and model artifacts.
"""

from pathlib import Path
import json
import joblib
import pytest
import pandas as pd
import numpy as np

from ml.features import (
    HospitalFeaturePipeline,
    prepare_waiting_time_dataset,
    PROHIBITED_LEAKAGE_COLUMNS,
)
from ml.waiting_time import (
    OverallMedianBaseline,
    DepartmentMedianBaseline,
    DepartmentAcuityMedianBaseline,
    chronological_split_visits,
    predict_waiting_time,
)

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "patient_visits.csv"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


@pytest.fixture(scope="module")
def visits_df():
    """Load patient visits dataset."""
    return pd.read_csv(DATA_PATH)


def test_target_consistency_math(visits_df):
    """waiting_time_minutes must equal service_start - arrival in minutes within 0.05 tolerance."""
    arr = pd.to_datetime(visits_df["arrival_timestamp"])
    srv = pd.to_datetime(visits_df["service_start_timestamp"])
    computed_wait = (srv - arr).dt.total_seconds() / 60.0
    discrepancy = (computed_wait.round(1) - visits_df["waiting_time_minutes"]).abs().max()
    assert discrepancy <= 0.05, f"Discrepancy found: {discrepancy}"


def test_chronological_split_visits(visits_df):
    """chronological_split_visits must partition into train (Days 1-10), val (Days 11-12), and test (Days 13-14)."""
    train_df, val_df, test_df = chronological_split_visits(visits_df)

    assert len(train_df) == 420
    assert len(val_df) == 100
    assert len(test_df) == 80
    assert len(train_df) + len(val_df) + len(test_df) == len(visits_df)

    # Verify strict temporal sequencing without lookahead overlap
    max_train = pd.to_datetime(train_df["arrival_timestamp"]).max()
    min_val = pd.to_datetime(val_df["arrival_timestamp"]).min()
    max_val = pd.to_datetime(val_df["arrival_timestamp"]).max()
    min_test = pd.to_datetime(test_df["arrival_timestamp"]).min()

    assert max_train < min_val, "Train and validation splits overlap!"
    assert max_val < min_test, "Validation and test splits overlap!"


def test_leakage_prohibited_columns_enforcement(visits_df):
    """HospitalFeaturePipeline must reject any DataFrame containing prohibited future outcome columns."""
    pipe = HospitalFeaturePipeline()

    # Verify that prepare_waiting_time_dataset removes all prohibited leakage columns
    clean_X, y = prepare_waiting_time_dataset(visits_df)
    leaked = set(clean_X.columns).intersection(PROHIBITED_LEAKAGE_COLUMNS)
    assert len(leaked) == 0, f"Leaked columns remaining in clean_X: {leaked}"
    assert "admission_required" not in clean_X.columns
    assert "waiting_time_minutes" not in clean_X.columns
    assert "service_start_timestamp" not in clean_X.columns

    # Pipeline should fit cleanly on safe feature set
    pipe.fit(clean_X.head(50))

    # Pipeline MUST raise ValueError if any prohibited column is introduced
    for col in PROHIBITED_LEAKAGE_COLUMNS:
        dirty_df = clean_X.head(20).copy()
        dirty_df[col] = 1
        with pytest.raises(ValueError, match="Target Leakage Detected"):
            pipe.transform(dirty_df)


def test_baseline_predictors(visits_df):
    """Statistical median baselines must train cleanly and predict non-negative finite waiting times."""
    train_df, val_df, _ = chronological_split_visits(visits_df)
    X_train_raw, y_train = prepare_waiting_time_dataset(train_df)
    X_val_raw, _ = prepare_waiting_time_dataset(val_df)

    # 1. Overall Median
    b1 = OverallMedianBaseline()
    b1.fit(X_train_raw, y_train)
    p1 = b1.predict(X_val_raw)
    assert len(p1) == len(X_val_raw)
    assert (p1 >= 0).all()
    assert np.all(p1 == p1[0])

    # 2. Department Median
    b2 = DepartmentMedianBaseline()
    b2.fit(X_train_raw, y_train)
    p2 = b2.predict(X_val_raw)
    assert len(p2) == len(X_val_raw)
    assert (p2 >= 0).all()

    # 3. Department + Acuity Median
    b3 = DepartmentAcuityMedianBaseline()
    b3.fit(X_train_raw, y_train)
    p3 = b3.predict(X_val_raw)
    assert len(p3) == len(X_val_raw)
    assert (p3 >= 0).all()


def test_model_artifact_bundle_loading_and_structure():
    """Serialized model bundle in ml/models/waiting_time_pipeline.joblib must contain all required components."""
    artifact_path = MODELS_DIR / "waiting_time_pipeline.joblib"
    assert artifact_path.exists(), f"Missing model artifact: {artifact_path}"

    bundle = joblib.load(artifact_path)
    assert "model" in bundle
    assert "pipeline" in bundle
    assert "model_name" in bundle
    assert "model_version" in bundle
    assert "feature_names" in bundle
    assert "baselines" in bundle
    assert "residual_std" in bundle
    assert isinstance(bundle["pipeline"], HospitalFeaturePipeline)
    assert len(bundle["feature_names"]) == 19
    assert bundle["residual_std"] > 0


def test_predict_waiting_time_valid_inputs():
    """predict_waiting_time must return non-negative estimate, bounds, and metadata."""
    res = predict_waiting_time(
        department_code="ED",
        acuity_level=3,
        queue_length=2,
        staff_available=4,
        models_dir=MODELS_DIR,
    )

    assert res["department_code"] == "ED"
    assert res["department_name"] == "Emergency Department"
    assert res["acuity_level"] == 3
    assert res["estimated_waiting_time_minutes"] >= 0.0
    assert 0.0 <= res["confidence_lower"] <= res["estimated_waiting_time_minutes"] <= res["confidence_upper"]
    assert "operational_context" in res
    assert "disclaimer" in res
    assert "SIMULATED OPERATIONAL ESTIMATE" in res["disclaimer"]


def test_predict_waiting_time_acuity_monotonicity():
    """Higher acuity (e.g. Acuity 1 resuscitation) must wait less than lower acuity (Acuity 5) under identical queues."""
    res_acuity_1 = predict_waiting_time(
        department_code="ED",
        acuity_level=1,
        queue_length=2,
        staff_available=3,
        models_dir=MODELS_DIR,
    )
    res_acuity_5 = predict_waiting_time(
        department_code="ED",
        acuity_level=5,
        queue_length=2,
        staff_available=3,
        models_dir=MODELS_DIR,
    )

    assert res_acuity_1["estimated_waiting_time_minutes"] < res_acuity_5["estimated_waiting_time_minutes"]


def test_predict_waiting_time_validation_errors():
    """predict_waiting_time must raise ValueError on out-of-range or invalid inputs."""
    # Invalid department
    with pytest.raises(ValueError, match="Unknown department code"):
        predict_waiting_time(department_code="CARDIAC", acuity_level=3, models_dir=MODELS_DIR)

    # Invalid acuity level
    with pytest.raises(ValueError, match="Acuity level must be between 1 and 5"):
        predict_waiting_time(department_code="ED", acuity_level=0, models_dir=MODELS_DIR)

    with pytest.raises(ValueError, match="Acuity level must be between 1 and 5"):
        predict_waiting_time(department_code="ED", acuity_level=6, models_dir=MODELS_DIR)

    # Negative queue
    with pytest.raises(ValueError, match="Queue length cannot be negative"):
        predict_waiting_time(department_code="ED", acuity_level=3, queue_length=-2, models_dir=MODELS_DIR)

    # Zero staff
    with pytest.raises(ValueError, match="Available staff must be at least 1"):
        predict_waiting_time(department_code="ED", acuity_level=3, staff_available=0, models_dir=MODELS_DIR)

    # Invalid age group
    with pytest.raises(ValueError, match="Invalid age group"):
        predict_waiting_time(department_code="ED", acuity_level=3, patient_age_group="Centenarian", models_dir=MODELS_DIR)


def test_metadata_file_completeness():
    """ml/models/waiting_time_metadata.json must exist and record evaluation metrics, residual stats, and limitations."""
    meta_path = MODELS_DIR / "waiting_time_metadata.json"
    assert meta_path.exists(), f"Missing metadata file: {meta_path}"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["model_version"] == "1.0.0"
    assert "evaluation_metrics" in meta
    assert "RandomForestRegressor" in meta["evaluation_metrics"]
    assert "OverallMedianBaseline" in meta["evaluation_metrics"]
    assert "residual_analysis" in meta
    assert "department_slices" in meta
    assert "limitations" in meta
    assert len(meta["limitations"]) > 0
