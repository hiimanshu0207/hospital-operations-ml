"""
Unit tests for hospital resource utilization, what-if simulation, and staff allocation optimizer.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from ml.optimization import (
    load_hospital_operational_state,
    calculate_department_utilization,
    simulate_what_if_scenario,
    optimize_staff_allocation,
    DEFAULT_MIN_STAFF,
    DEFAULT_MAX_STAFF,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


@pytest.fixture(scope="module")
def operational_state():
    """Load baseline operational state from CSV."""
    return load_hospital_operational_state(data_dir=DATA_DIR)


def test_calculate_department_utilization(operational_state):
    """Department utilization analysis must compute valid bed, staffing, queue, and wait time indicators."""
    res = calculate_department_utilization(operational_state, models_dir=MODELS_DIR)

    assert "hospital_summary" in res
    assert "department_utilization" in res
    assert len(res["department_utilization"]) == 5

    summary = res["hospital_summary"]
    assert summary["total_beds"] > 0
    assert summary["total_occupied_beds"] >= 0
    assert summary["total_occupied_beds"] <= summary["total_beds"]
    assert 0.0 <= summary["overall_bed_utilization_pct"] <= 100.0
    assert 0.0 <= summary["operational_stress_index"] <= 100.0

    for dept in res["department_utilization"]:
        assert dept["department_code"] in ["ED", "ICU", "GEN", "SURG", "PED"]
        assert dept["bed_capacity"]["available_beds"] >= 0
        assert dept["bed_capacity"]["total_beds"] == dept["bed_capacity"]["occupied_beds"] + dept["bed_capacity"]["available_beds"]
        assert dept["staffing"]["active_staff_total"] > 0
        assert dept["staffing"]["nurse_count"] >= 0
        assert dept["queue_and_demand"]["current_queue_estimate"] >= 0
        assert dept["estimated_wait_time"]["estimated_minutes"] >= 0.0
        assert dept["bed_capacity"]["data_source"] == "OBSERVED_DATABASE_STATE"
        assert dept["estimated_wait_time"]["data_source"] == "ML_MODEL_ESTIMATE"


def test_zero_capacity_and_missing_data_safety():
    """calculate_department_utilization must safely handle zero total beds, zero staff, and empty visits without DivisionByZero."""
    empty_state = {
        "departments": pd.DataFrame([{
            "id": 99,
            "code": "TEST",
            "name": "Empty Test Ward",
            "total_beds": 0,
            "target_nurse_to_patient_ratio": 0.20,
        }]),
        "staff": pd.DataFrame(columns=["id", "staff_id", "role", "department_id", "shift", "is_active"]),
        "beds": pd.DataFrame(columns=["id", "bed_number", "department_id", "bed_type", "is_occupied"]),
        "patient_visits": pd.DataFrame(columns=["id", "visit_id", "department_id", "queue_length_at_arrival"]),
    }

    res = calculate_department_utilization(empty_state, models_dir=MODELS_DIR)
    dept_res = res["department_utilization"][0]

    assert dept_res["bed_capacity"]["total_beds"] == 0
    assert dept_res["bed_capacity"]["occupied_beds"] == 0
    assert dept_res["bed_capacity"]["utilization_rate_pct"] == 0.0
    assert dept_res["bed_capacity"]["status"] == "NO_BEDS_CONFIGURED"
    assert dept_res["staffing"]["active_staff_total"] == 0
    assert dept_res["queue_and_demand"]["queue_to_staff_ratio"] >= 0.0


def test_simulate_what_if_scenario_deterministic(operational_state):
    """Simulating identical parameters with the same seed must produce identical outputs."""
    sim1 = simulate_what_if_scenario(
        operational_state,
        arrival_surge_pct=20.0,
        staff_adjustments={"ED": 2, "GEN": -1},
        time_horizon_hours=12,
        simulation_seed=42,
        models_dir=MODELS_DIR,
    )
    sim2 = simulate_what_if_scenario(
        operational_state,
        arrival_surge_pct=20.0,
        staff_adjustments={"ED": 2, "GEN": -1},
        time_horizon_hours=12,
        simulation_seed=42,
        models_dir=MODELS_DIR,
    )

    assert sim1["overall_impact"] == sim2["overall_impact"]
    assert sim1["department_comparisons"] == sim2["department_comparisons"]


def test_simulate_what_if_no_mutation(operational_state):
    """Simulations must never mutate or modify the input operational DataFrames."""
    depts_before = operational_state["departments"].copy()
    staff_before = operational_state["staff"].copy()
    beds_before = operational_state["beds"].copy()
    visits_before = operational_state["patient_visits"].copy()

    _ = simulate_what_if_scenario(
        operational_state,
        arrival_surge_pct=50.0,
        staff_adjustments={"ED": 4, "ICU": 2},
        bed_capacity_adjustments={"ED": 10},
        models_dir=MODELS_DIR,
    )

    pd.testing.assert_frame_equal(operational_state["departments"], depts_before)
    pd.testing.assert_frame_equal(operational_state["staff"], staff_before)
    pd.testing.assert_frame_equal(operational_state["beds"], beds_before)
    pd.testing.assert_frame_equal(operational_state["patient_visits"], visits_before)


def test_simulate_what_if_capacity_constraints(operational_state):
    """Simulation must raise ValueError when bed reduction violates current occupied beds or staff drops below minimum."""
    # Staff below minimum constraint
    with pytest.raises(ValueError, match="cannot be reduced below safety minimum"):
        simulate_what_if_scenario(
            operational_state,
            staff_adjustments={"ED": -20},
            models_dir=MODELS_DIR,
        )

    # Bed reduction below occupied count (ICU has 4 occupied beds)
    with pytest.raises(ValueError, match="cannot be reduced to"):
        simulate_what_if_scenario(
            operational_state,
            bed_capacity_adjustments={"ICU": -11},  # 12 - 11 = 1 bed, but 4 are occupied!
            models_dir=MODELS_DIR,
        )


def test_simulate_what_if_invalid_inputs(operational_state):
    """simulate_what_if_scenario must reject invalid surge rates, horizons, and department codes."""
    # Surge rate > 100%
    with pytest.raises(ValueError, match=r"Arrival surge percentage"):
        simulate_what_if_scenario(operational_state, arrival_surge_pct=150.0, models_dir=MODELS_DIR)

    # Surge rate < -50%
    with pytest.raises(ValueError, match=r"Arrival surge percentage"):
        simulate_what_if_scenario(operational_state, arrival_surge_pct=-60.0, models_dir=MODELS_DIR)

    # Invalid horizon
    with pytest.raises(ValueError, match="Time horizon must be between 1 and 72 hours"):
        simulate_what_if_scenario(operational_state, time_horizon_hours=0, models_dir=MODELS_DIR)

    # Unknown department
    with pytest.raises(ValueError, match="Unknown department code"):
        simulate_what_if_scenario(operational_state, staff_adjustments={"ONCOLOGY": 2}, models_dir=MODELS_DIR)


def test_optimize_staff_allocation_budget_conservation(operational_state):
    """Staff allocation optimizer must strictly conserve total staff budget."""
    opt_default = optimize_staff_allocation(operational_state)

    assert opt_default["budget_conserved"] is True
    assert opt_default["total_allocated_staff"] == opt_default["total_staff_budget"]
    assert opt_default["optimizer_status"] == "CONVERGED"

    # Custom budget
    custom_budget = 80
    opt_custom = optimize_staff_allocation(operational_state, total_staff_budget=custom_budget)
    assert opt_custom["total_allocated_staff"] == custom_budget
    assert opt_custom["budget_conserved"] is True


def test_optimize_staff_allocation_bounds_enforcement(operational_state):
    """Staff allocation recommendations must strictly satisfy minimum and maximum departmental constraints."""
    opt = optimize_staff_allocation(operational_state)

    for rec in opt["recommendations"]:
        code = rec["department_code"]
        rec_staff = rec["recommended_staff"]
        min_c = rec["minimum_staff_constraint"]
        max_c = rec["maximum_staff_constraint"]

        assert rec_staff >= min_c, f"{code} recommendation {rec_staff} violated minimum constraint {min_c}"
        assert rec_staff <= max_c, f"{code} recommendation {rec_staff} violated maximum constraint {max_c}"
        assert len(rec["rationale"]) > 0


def test_optimize_staff_allocation_shift_specific(operational_state):
    """Optimizer must support individual shift allocation and conserve shift-specific staff headcount."""
    opt_morning = optimize_staff_allocation(operational_state, shift="Morning")

    assert opt_morning["shift"] == "Morning"
    assert opt_morning["budget_conserved"] is True
    assert opt_morning["total_allocated_staff"] == opt_morning["total_current_staff"]
    # Total morning staff across departments is ~28
    assert 20 <= opt_morning["total_allocated_staff"] <= 35


def test_optimize_staff_allocation_insufficient_or_excessive_budget(operational_state):
    """Optimizer must reject budgets that cannot meet safety minimums or exceed department physical capacities."""
    # Insufficient budget to meet safety minimums
    with pytest.raises(ValueError, match="insufficient to meet mandatory minimum safety staffing"):
        optimize_staff_allocation(operational_state, total_staff_budget=10)

    # Excessive budget exceeding maximum physical capacities
    with pytest.raises(ValueError, match="exceeds maximum departmental physical capacity limits"):
        optimize_staff_allocation(operational_state, total_staff_budget=250)


def test_rule_based_baseline_comparison(operational_state):
    """Staff allocation output must provide a rule-based baseline comparison conserving budget."""
    opt = optimize_staff_allocation(operational_state)

    rule_comp = opt["rule_based_comparison"]
    assert "method" in rule_comp
    allocs = rule_comp["integer_allocations"]
    assert sum(allocs.values()) == opt["total_staff_budget"]
    for code in ["ED", "ICU", "GEN", "SURG", "PED"]:
        assert code in allocs
        assert allocs[code] >= DEFAULT_MIN_STAFF[code]
