"""
Automated data quality and integrity tests for synthetic hospital datasets.

Verifies:
- Required columns and data types
- Missing values and duplicate constraints
- Sequential timestamps and non-negative durations
- Bed capacity and occupancy bounds
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@pytest.fixture(scope="module")
def datasets():
    """Load all 4 CSV datasets from data/ directory."""
    return {
        "departments": pd.read_csv(DATA_DIR / "departments.csv"),
        "staff": pd.read_csv(DATA_DIR / "staff.csv"),
        "beds": pd.read_csv(DATA_DIR / "beds.csv"),
        "patient_visits": pd.read_csv(DATA_DIR / "patient_visits.csv"),
    }


def test_required_dataset_files_exist():
    """All 4 standard dataset files must exist on disk."""
    for filename in ["departments.csv", "staff.csv", "beds.csv", "patient_visits.csv"]:
        assert (DATA_DIR / filename).exists(), f"Missing dataset file: {filename}"


def test_patient_visits_schema_and_types(datasets):
    """Patient visits dataset must contain all required columns with expected types."""
    visits = datasets["patient_visits"]
    required_cols = [
        "id", "visit_id", "department_id", "patient_age_group", "acuity_level",
        "arrival_timestamp", "queue_length_at_arrival", "staff_available_at_arrival",
        "service_start_timestamp", "service_end_timestamp", "waiting_time_minutes",
        "length_of_stay_minutes", "total_duration_minutes", "admission_required",
        "bed_id", "status", "created_at"
    ]
    for col in required_cols:
        assert col in visits.columns, f"Missing required column: {col}"

    assert len(visits) >= 500, "Dataset should have at least 500 records"
    assert pd.api.types.is_numeric_dtype(visits["waiting_time_minutes"])
    assert pd.api.types.is_numeric_dtype(visits["length_of_stay_minutes"])
    assert pd.api.types.is_numeric_dtype(visits["acuity_level"])


def test_no_critical_missing_values(datasets):
    """Critical operational features must have zero missing/null values."""
    visits = datasets["patient_visits"]
    critical_cols = [
        "id", "visit_id", "department_id", "patient_age_group", "acuity_level",
        "arrival_timestamp", "queue_length_at_arrival", "staff_available_at_arrival",
        "service_start_timestamp", "service_end_timestamp", "waiting_time_minutes",
        "length_of_stay_minutes", "total_duration_minutes", "admission_required",
        "status"
    ]
    for col in critical_cols:
        assert visits[col].isnull().sum() == 0, f"Column {col} has unexpected null values"

    # bed_id is allowed null only for unadmitted patients
    admitted = visits[visits["admission_required"] == True]
    assert admitted["bed_id"].isnull().sum() == 0, "Admitted patients must have a bed_id assigned"


def test_unique_identifiers(datasets):
    """All entity identifiers must be completely unique."""
    assert datasets["patient_visits"]["visit_id"].is_unique, "Duplicate visit_id detected"
    assert datasets["beds"]["bed_number"].is_unique, "Duplicate bed_number detected"
    assert datasets["staff"]["staff_id"].is_unique, "Duplicate staff_id detected"
    assert datasets["departments"]["code"].is_unique, "Duplicate department code detected"


def test_timestamp_chronology(datasets):
    """Timestamp sequence must be strictly sequential: arrival <= service_start <= service_end."""
    visits = datasets["patient_visits"]
    t_arr = pd.to_datetime(visits["arrival_timestamp"])
    t_start = pd.to_datetime(visits["service_start_timestamp"])
    t_end = pd.to_datetime(visits["service_end_timestamp"])

    assert (t_start >= t_arr).all(), "Service start timestamp cannot be earlier than arrival timestamp"
    assert (t_end >= t_start).all(), "Service end timestamp cannot be earlier than service start timestamp"


def test_non_negative_durations_and_math_consistency(datasets):
    """Durations must be non-negative and mathematically match timestamps."""
    visits = datasets["patient_visits"]
    t_arr = pd.to_datetime(visits["arrival_timestamp"])
    t_start = pd.to_datetime(visits["service_start_timestamp"])
    t_end = pd.to_datetime(visits["service_end_timestamp"])

    assert (visits["waiting_time_minutes"] >= 0).all(), "Negative waiting time detected"
    assert (visits["length_of_stay_minutes"] >= 0).all(), "Negative length of stay detected"
    assert (visits["total_duration_minutes"] >= 0).all(), "Negative total duration detected"

    calc_wait = (t_start - t_arr).dt.total_seconds() / 60.0
    calc_los = (t_end - t_start).dt.total_seconds() / 60.0

    # Allow tiny float precision margin (< 0.1 min)
    assert np.allclose(calc_wait, visits["waiting_time_minutes"], atol=0.1), "Wait time formula mismatch"
    assert np.allclose(calc_los, visits["length_of_stay_minutes"], atol=0.1), "LOS formula mismatch"


def test_bed_capacity_bounds(datasets):
    """Occupied beds must never exceed total capacity in any department."""
    depts = datasets["departments"]
    beds = datasets["beds"]

    dept_cap = depts.set_index("id")["total_beds"].to_dict()
    occupied = beds[beds["is_occupied"] == True].groupby("department_id").size().to_dict()

    for dept_id, capacity in dept_cap.items():
        occ_count = occupied.get(dept_id, 0)
        assert occ_count <= capacity, f"Dept {dept_id} occupied beds ({occ_count}) exceed capacity ({capacity})"
