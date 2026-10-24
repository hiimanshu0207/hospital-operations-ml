"""
Tests for the synthetic data generator and validation suite.

Verifies reproducibility, integrity constraints, and error detection.
"""

import pytest
import pandas as pd
from app.services.synthetic_generator import (
    SyntheticHospitalDataGenerator,
    validate_synthetic_data,
)


def test_generator_deterministic_reproducibility():
    """Generator with identical seeds must produce identical data."""
    gen1 = SyntheticHospitalDataGenerator(seed=123)
    data1 = gen1.generate_all(num_visits=50)

    gen2 = SyntheticHospitalDataGenerator(seed=123)
    data2 = gen2.generate_all(num_visits=50)

    pd.testing.assert_frame_equal(data1["departments"], data2["departments"])
    pd.testing.assert_frame_equal(data1["beds"], data2["beds"])
    pd.testing.assert_frame_equal(data1["staff"], data2["staff"])
    pd.testing.assert_frame_equal(data1["patient_visits"], data2["patient_visits"])


def test_generator_different_seeds_produce_different_data():
    """Different seeds must produce different simulated visit arrivals."""
    gen1 = SyntheticHospitalDataGenerator(seed=10)
    v1 = gen1.generate_all(num_visits=30)["patient_visits"]

    gen2 = SyntheticHospitalDataGenerator(seed=99)
    v2 = gen2.generate_all(num_visits=30)["patient_visits"]

    assert not v1["waiting_time_minutes"].equals(v2["waiting_time_minutes"])


def test_generated_data_passes_validation():
    """Generated datasets must pass all operational integrity rules."""
    gen = SyntheticHospitalDataGenerator(seed=42)
    data = gen.generate_all(num_visits=100)

    metrics = validate_synthetic_data(
        visits_df=data["patient_visits"],
        departments_df=data["departments"],
        beds_df=data["beds"],
    )

    assert metrics["status"] == "VALID"
    assert metrics["total_visits"] == 100
    assert metrics["total_departments"] == 5
    assert metrics["avg_waiting_time_minutes"] >= 0
    assert metrics["avg_length_of_stay_minutes"] > 0


def test_validation_catches_negative_waiting_time():
    """Validator must reject negative waiting times."""
    gen = SyntheticHospitalDataGenerator(seed=42)
    data = gen.generate_all(num_visits=20)
    data["patient_visits"].loc[0, "waiting_time_minutes"] = -5.0

    with pytest.raises(ValueError, match="Negative waiting times"):
        validate_synthetic_data(
            visits_df=data["patient_visits"],
            departments_df=data["departments"],
            beds_df=data["beds"],
        )


def test_validation_catches_invalid_timestamp_sequence():
    """Validator must reject visits where service_start < arrival."""
    gen = SyntheticHospitalDataGenerator(seed=42)
    data = gen.generate_all(num_visits=20)
    arr = data["patient_visits"].loc[0, "arrival_timestamp"]
    data["patient_visits"].loc[0, "service_start_timestamp"] = arr - pd.Timedelta(minutes=10)

    with pytest.raises(ValueError, match="earlier than arrival"):
        validate_synthetic_data(
            visits_df=data["patient_visits"],
            departments_df=data["departments"],
            beds_df=data["beds"],
        )


def test_validation_catches_duplicate_visit_ids():
    """Validator must reject duplicate synthetic visit IDs."""
    gen = SyntheticHospitalDataGenerator(seed=42)
    data = gen.generate_all(num_visits=20)
    data["patient_visits"].loc[1, "visit_id"] = data["patient_visits"].loc[0, "visit_id"]

    with pytest.raises(ValueError, match="Duplicate synthetic visit IDs"):
        validate_synthetic_data(
            visits_df=data["patient_visits"],
            departments_df=data["departments"],
            beds_df=data["beds"],
        )


def test_validation_catches_occupied_beds_exceeding_capacity():
    """Validator must reject occupied bed counts that exceed department capacity."""
    gen = SyntheticHospitalDataGenerator(seed=42)
    data = gen.generate_all(num_visits=20)

    # Department 2 (ICU) has 12 beds. Fake capacity down to 1 bed while 3 are occupied.
    data["departments"].loc[data["departments"]["id"] == 2, "total_beds"] = 1
    # Mark two beds in dept 2 as occupied
    dept2_bed_idx = data["beds"][data["beds"]["department_id"] == 2].index[:2]
    data["beds"].loc[dept2_bed_idx, "is_occupied"] = True

    with pytest.raises(ValueError, match="exceeding capacity"):
        validate_synthetic_data(
            visits_df=data["patient_visits"],
            departments_df=data["departments"],
            beds_df=data["beds"],
        )


def test_validation_catches_invalid_acuity():
    """Validator must reject acuity outside 1-5."""
    gen = SyntheticHospitalDataGenerator(seed=42)
    data = gen.generate_all(num_visits=20)
    data["patient_visits"].loc[0, "acuity_level"] = 6

    with pytest.raises(ValueError, match="Acuity level out of valid range"):
        validate_synthetic_data(
            visits_df=data["patient_visits"],
            departments_df=data["departments"],
            beds_df=data["beds"],
        )
