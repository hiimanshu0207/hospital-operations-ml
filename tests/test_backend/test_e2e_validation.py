"""
End-to-end integration and model validation test suite.

Validates:
1. All six dashboard view endpoints against the FastAPI backend
2. Demand forecasting & waiting-time prediction with valid and invalid inputs
3. Clinical monotonicity and triage acuity ordering
4. What-if simulation constraints (staff safety minimums, bed capacity, non-mutation)
5. Staff allocation constraints (exact budget conservation, integer rounding, bounds)
6. Output non-negativity and prediction reproducibility
7. Target leakage safeguards (prohibited column rejection)
8. Empty database state resilience and missing model artifact handling (503 Service Unavailable)
"""

from pathlib import Path
import pytest
from app.schemas.prediction import DemandForecastResponse, WaitingTimePredictionResponse
from app.schemas.optimization import ResourceUtilizationResponse, WhatIfSimulationResponse, StaffAllocationResponse
from ml.features import HospitalFeaturePipeline, PROHIBITED_LEAKAGE_COLUMNS


# ---------------------------------------------------------------------------
# 1. All Six Dashboard Views E2E Testing
# ---------------------------------------------------------------------------

def test_dashboard_view_1_overview_telemetry(seeded_client):
    """View 1: Hospital Overview consumes health, utilization, summary, and recent encounters."""
    # Health check
    res_health = seeded_client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # Utilization
    res_util = seeded_client.get("/api/v1/optimization/utilization")
    assert res_util.status_code == 200
    util = res_util.json()
    assert "hospital_summary" in util
    assert "department_utilization" in util
    assert "active_warnings" in util
    assert "disclaimer" in util
    assert util["hospital_summary"]["total_beds"] > 0
    assert util["hospital_summary"]["total_active_staff"] > 0
    assert 0.0 <= util["hospital_summary"]["operational_stress_index"] <= 100.0

    # Summary
    res_summary = seeded_client.get("/api/v1/patient-visits/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_visits"] > 0
    assert summary["avg_waiting_time_minutes"] >= 0.0
    assert summary["avg_length_of_stay_minutes"] > 0.0

    # Recent encounters stream
    res_recent = seeded_client.get("/api/v1/patient-visits/recent?limit=8")
    assert res_recent.status_code == 200
    recent = res_recent.json()
    assert len(recent) == 8
    first = recent[0]
    for key in ["id", "visit_id", "patient_age_group", "acuity_level", "queue_length_at_arrival", "waiting_time_minutes", "status"]:
        assert key in first


def test_dashboard_view_2_department_operations(seeded_client):
    """View 2: Department Operations consumes departments list, per-department metrics, and utilization."""
    res_depts = seeded_client.get("/api/v1/departments")
    assert res_depts.status_code == 200
    depts = res_depts.json()
    assert len(depts) == 5
    dept_codes = {d["code"] for d in depts}
    assert dept_codes == {"ED", "ICU", "GEN", "SURG", "PED"}

    # Check metrics for each department
    for d in depts:
        res_metrics = seeded_client.get(f"/api/v1/departments/{d['id']}/metrics")
        assert res_metrics.status_code == 200
        metrics = res_metrics.json()
        assert "occupancy_rate" in metrics
        assert "total_beds" in metrics
        assert metrics["total_beds"] >= 0


def test_dashboard_view_3_demand_forecast(seeded_client):
    """View 3: Demand Forecast produces valid hourly forecasts with Poisson confidence bands."""
    for dept in ["ED", "ICU", "GEN", "SURG", "PED"]:
        for horizon in [12, 24, 48]:
            res = seeded_client.post(
                "/api/v1/predictions/demand",
                json={"department_code": dept, "horizon_hours": horizon},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["department_code"] == dept
            assert data["horizon_hours"] == horizon
            assert len(data["hourly_forecasts"]) == horizon
            assert data["total_predicted_arrivals"] >= 0.0

            # Confidence bounds validity
            for h in data["hourly_forecasts"]:
                assert h["predicted_arrivals"] >= 0.0
                assert h["confidence_lower"] >= 0.0
                assert h["confidence_upper"] >= h["confidence_lower"]
            assert "disclaimer" in data


def test_dashboard_view_4_waiting_time_prediction(seeded_client):
    """View 4: Waiting-Time Predictor outputs non-negative minutes and 95% uncertainty interval."""
    for acuity in [1, 2, 3, 4, 5]:
        res = seeded_client.post(
            "/api/v1/predictions/waiting-time",
            json={
                "department_code": "ED",
                "acuity_level": acuity,
                "queue_length": 6,
                "staff_available": 4,
                "patient_age_group": "36-50",
            },
        )
        assert res.status_code == 200
        pred = res.json()
        assert pred["acuity_level"] == acuity
        assert pred["estimated_waiting_time_minutes"] >= 0.0
        assert pred["confidence_lower"] >= 0.0
        assert pred["confidence_upper"] >= pred["confidence_lower"]
        assert "model_name" in pred
        assert "disclaimer" in pred


def test_dashboard_view_5_what_if_simulation(seeded_client):
    """View 5: What-if Simulation computes baseline vs simulated impacts under surges and reallocations."""
    res = seeded_client.post(
        "/api/v1/optimization/simulate",
        json={
            "arrival_surge_pct": 20.0,
            "staff_adjustments": {"ED": 2, "GEN": -1},
            "bed_capacity_adjustments": {"ED": 5},
            "time_horizon_hours": 12,
            "simulation_seed": 42,
        },
    )
    assert res.status_code == 200
    sim = res.json()
    assert "overall_impact" in sim
    assert "department_comparisons" in sim
    assert len(sim["department_comparisons"]) == 5
    assert len(sim["assumptions"]) > 0
    assert "disclaimer" in sim

    # Impact fields
    impact = sim["overall_impact"]
    assert impact["average_baseline_wait_minutes"] >= 0.0
    assert impact["average_simulated_wait_minutes"] >= 0.0
    assert impact["surge_severity"] in ["Normal", "Moderate", "Critical"]


def test_dashboard_view_6_staff_allocation(seeded_client):
    """View 6: Staff Allocation Optimizer conserves budget and honors safety bounds."""
    for shift in ["All", "Morning", "Evening", "Night"]:
        res = seeded_client.post(
            "/api/v1/optimization/allocate",
            json={"shift": shift},
        )
        assert res.status_code == 200
        alloc = res.json()
        assert alloc["budget_conserved"] is True
        assert alloc["total_allocated_staff"] == alloc["total_staff_budget"]
        assert len(alloc["recommendations"]) == 5
        assert alloc["optimizer_status"] in ["CONVERGED", "FALLBACK_TO_BOUNDED"]

        for rec in alloc["recommendations"]:
            assert rec["minimum_staff_constraint"] <= rec["recommended_staff"] <= rec["maximum_staff_constraint"]
            assert isinstance(rec["recommended_staff"], int)
            assert len(rec["rationale"]) > 0


# ---------------------------------------------------------------------------
# 2. Demand Forecasting Input Validation
# ---------------------------------------------------------------------------

def test_demand_forecasting_invalid_inputs(client):
    """POST /api/v1/predictions/demand rejects invalid department codes and horizons."""
    # Unknown department
    res_dept = client.post("/api/v1/predictions/demand", json={"department_code": "UNKNOWN", "horizon_hours": 24})
    assert res_dept.status_code == 404

    # Horizon = 0
    res_zero = client.post("/api/v1/predictions/demand", json={"department_code": "ED", "horizon_hours": 0})
    assert res_zero.status_code == 422

    # Horizon negative
    res_neg = client.post("/api/v1/predictions/demand", json={"department_code": "ED", "horizon_hours": -5})
    assert res_neg.status_code == 422

    # Horizon > 72 hours
    res_large = client.post("/api/v1/predictions/demand", json={"department_code": "ED", "horizon_hours": 73})
    assert res_large.status_code == 422

    # Non-integer horizon
    res_str = client.post("/api/v1/predictions/demand", json={"department_code": "ED", "horizon_hours": "twenty"})
    assert res_str.status_code == 422


# ---------------------------------------------------------------------------
# 3. Waiting-Time Prediction Input Validation & Monotonicity
# ---------------------------------------------------------------------------

def test_waiting_time_invalid_inputs(client):
    """POST /api/v1/predictions/waiting-time rejects invalid acuity, queue, and staff values."""
    # Acuity level = 0
    res_acuity_0 = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "ED", "acuity_level": 0, "queue_length": 3, "staff_available": 4},
    )
    assert res_acuity_0.status_code == 422

    # Acuity level = 6
    res_acuity_6 = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "ED", "acuity_level": 6, "queue_length": 3, "staff_available": 4},
    )
    assert res_acuity_6.status_code == 422

    # Negative queue
    res_neg_q = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "ED", "acuity_level": 3, "queue_length": -1, "staff_available": 4},
    )
    assert res_neg_q.status_code == 422

    # Zero staff
    res_zero_staff = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "ED", "acuity_level": 3, "queue_length": 3, "staff_available": 0},
    )
    assert res_zero_staff.status_code == 422

    # Unknown department
    res_unknown_dept = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "XYZ", "acuity_level": 3, "queue_length": 3, "staff_available": 4},
    )
    assert res_unknown_dept.status_code == 404


def test_waiting_time_clinical_triage_acuity_ordering(seeded_client):
    """ESI Level 1 (Resuscitation) must predict significantly shorter wait time than ESI Level 5 (Non-urgent)."""
    base_params = {
        "department_code": "ED",
        "queue_length": 5,
        "staff_available": 4,
        "patient_age_group": "36-50",
    }
    pred_esi1 = seeded_client.post("/api/v1/predictions/waiting-time", json={**base_params, "acuity_level": 1}).json()
    pred_esi5 = seeded_client.post("/api/v1/predictions/waiting-time", json={**base_params, "acuity_level": 5}).json()

    wait_esi1 = pred_esi1["estimated_waiting_time_minutes"]
    wait_esi5 = pred_esi5["estimated_waiting_time_minutes"]

    assert wait_esi1 >= 0.0
    assert wait_esi5 >= 0.0
    # Clinical reality: Resuscitation patients are prioritized immediately over non-urgent patients
    assert wait_esi1 < wait_esi5, f"Expected ESI 1 ({wait_esi1}m) to wait less than ESI 5 ({wait_esi5}m)"


# ---------------------------------------------------------------------------
# 4. What-If Simulation Constraints
# ---------------------------------------------------------------------------

def test_simulation_surge_bounds(seeded_client):
    """Simulation rejects arrival surge percentages outside [-50.0%, +100.0%]."""
    # Below -50%
    res_low = seeded_client.post(
        "/api/v1/optimization/simulate",
        json={"arrival_surge_pct": -55.0},
    )
    assert res_low.status_code == 422

    # Above +100%
    res_high = seeded_client.post(
        "/api/v1/optimization/simulate",
        json={"arrival_surge_pct": 110.0},
    )
    assert res_high.status_code == 422


def test_simulation_staff_safety_minimums_enforced(seeded_client):
    """Simulation rejects staff reductions that breach departmental safety minimums."""
    # Attempting to remove 20 staff from ED (violates minimum safety threshold of 4)
    res = seeded_client.post(
        "/api/v1/optimization/simulate",
        json={
            "staff_adjustments": {"ED": -20},
        },
    )
    assert res.status_code == 422
    assert "safety minimum" in res.json()["detail"].lower()


def test_simulation_bed_eviction_prevention(seeded_client):
    """Simulation rejects bed closures that exceed available beds (cannot evict occupied inpatients)."""
    # Attempting to remove 20 beds from ICU when beds are occupied
    res = seeded_client.post(
        "/api/v1/optimization/simulate",
        json={
            "bed_capacity_adjustments": {"ICU": -20},
        },
    )
    assert res.status_code == 422
    assert "cannot be reduced" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Staff Allocation Constraints & Workforce Conservation
# ---------------------------------------------------------------------------

def test_staff_allocation_workforce_conservation(seeded_client):
    """Allocated headcount matches target budget exactly across shifts."""
    for shift, test_budget in [("All", 84), ("Morning", 30), ("Evening", 30), ("Night", 24)]:
        res = seeded_client.post(
            "/api/v1/optimization/allocate",
            json={"shift": shift, "total_staff_budget": test_budget},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["budget_conserved"] is True
        assert data["total_allocated_staff"] == test_budget

        alloc_sum = sum(r["recommended_staff"] for r in data["recommendations"])
        assert alloc_sum == test_budget, f"Sum of allocated staff {alloc_sum} != budget {test_budget}"


def test_staff_allocation_rejects_insufficient_budget(seeded_client):
    """Allocation rejects budget lower than mandatory minimum staffing requirements."""
    res = seeded_client.post(
        "/api/v1/optimization/allocate",
        json={"shift": "All", "total_staff_budget": 5},  # 5 is far below sum of min staff
    )
    assert res.status_code == 422
    assert "insufficient" in res.json()["detail"].lower()


def test_staff_allocation_rejects_invalid_shift(client):
    """Allocation rejects non-existent shift names."""
    res = client.post("/api/v1/optimization/allocate", json={"shift": "Graveyard"})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 6. Reproducibility & Output Non-Negativity
# ---------------------------------------------------------------------------

def test_demand_forecast_reproducibility(seeded_client):
    """Demand forecasting with same inputs produces identical deterministic forecasts."""
    req = {"department_code": "ED", "horizon_hours": 24}
    res1 = seeded_client.post("/api/v1/predictions/demand", json=req).json()
    res2 = seeded_client.post("/api/v1/predictions/demand", json=req).json()

    assert res1["total_predicted_arrivals"] == res2["total_predicted_arrivals"]
    assert res1["hourly_forecasts"] == res2["hourly_forecasts"]


def test_waiting_time_reproducibility(seeded_client):
    """Waiting time model inference produces identical predictions for identical inputs."""
    req = {
        "department_code": "GEN",
        "acuity_level": 3,
        "queue_length": 4,
        "staff_available": 3,
        "patient_age_group": "51-65",
    }
    res1 = seeded_client.post("/api/v1/predictions/waiting-time", json=req).json()
    res2 = seeded_client.post("/api/v1/predictions/waiting-time", json=req).json()

    assert res1["estimated_waiting_time_minutes"] == res2["estimated_waiting_time_minutes"]
    assert res1["confidence_lower"] == res2["confidence_lower"]
    assert res1["confidence_upper"] == res2["confidence_upper"]


def test_simulation_seed_reproducibility(seeded_client):
    """Simulation with identical seed produces identical results."""
    req = {
        "arrival_surge_pct": 25.0,
        "staff_adjustments": {"ED": 2},
        "simulation_seed": 999,
    }
    res1 = seeded_client.post("/api/v1/optimization/simulate", json=req).json()
    res2 = seeded_client.post("/api/v1/optimization/simulate", json=req).json()

    assert res1["overall_impact"] == res2["overall_impact"]
    assert res1["department_comparisons"] == res2["department_comparisons"]


# ---------------------------------------------------------------------------
# 7. Target Leakage Safeguards
# ---------------------------------------------------------------------------

def test_feature_pipeline_rejects_target_leakage_columns():
    """Feature pipeline must raise ValueError if future milestone columns are passed."""
    import pandas as pd

    pipeline = HospitalFeaturePipeline()
    for col in PROHIBITED_LEAKAGE_COLUMNS:
        leaked_df = pd.DataFrame([{
            "arrival_timestamp": "2026-10-23T10:00:00Z",
            "queue_length_at_arrival": 3,
            "staff_available_at_arrival": 4,
            "acuity_level": 3,
            "patient_age_group": "36-50",
            "department_id": 1,
            col: 100,  # Prohibited post-arrival column!
        }])
        with pytest.raises(ValueError) as exc:
            pipeline.fit(leaked_df)
        assert "target leakage" in str(exc.value).lower()


# ---------------------------------------------------------------------------
# 8. Empty Database State Resilience
# ---------------------------------------------------------------------------

def test_empty_database_all_endpoints_resilience(client):
    """All GET/POST endpoints must handle completely empty database without crashing (500)."""
    # Health check
    assert client.get("/health").status_code == 200

    # Departments & Beds
    assert client.get("/api/v1/departments").status_code == 200
    assert client.get("/api/v1/beds").status_code == 200
    assert client.get("/api/v1/beds/summary").status_code == 200

    # Patient visits
    res_summary = client.get("/api/v1/patient-visits/summary")
    assert res_summary.status_code == 200
    assert res_summary.json()["total_visits"] == 0

    res_recent = client.get("/api/v1/patient-visits/recent?limit=8")
    assert res_recent.status_code == 200
    assert res_recent.json() == []

    # Utilization (falls back gracefully to CSV baseline if DB unseeded)
    res_util = client.get("/api/v1/optimization/utilization")
    assert res_util.status_code == 200

    # Predictions (model artifacts are standalone)
    res_demand = client.post("/api/v1/predictions/demand", json={"department_code": "ED", "horizon_hours": 12})
    assert res_demand.status_code == 200

    res_wait = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "ED", "acuity_level": 3, "queue_length": 2, "staff_available": 3},
    )
    assert res_wait.status_code == 200


# ---------------------------------------------------------------------------
# 9. Unavailable Model Artifact Handling (503 Service Unavailable)
# ---------------------------------------------------------------------------

def test_missing_demand_model_artifact_returns_503(client, monkeypatch, tmp_path):
    """When demand model artifact file is missing, returns HTTP 503 Service Unavailable."""
    import app.routers.predictions as pred_router
    monkeypatch.setattr(pred_router, "MODELS_DIR", tmp_path / "empty_models")

    res = client.post("/api/v1/predictions/demand", json={"department_code": "ED", "horizon_hours": 12})
    assert res.status_code == 503
    assert "artifact is not available" in res.json()["detail"].lower()


def test_missing_waiting_time_model_artifact_returns_503(client, monkeypatch, tmp_path):
    """When waiting-time model artifact file is missing, returns HTTP 503 Service Unavailable."""
    import app.routers.predictions as pred_router
    monkeypatch.setattr(pred_router, "MODELS_DIR", tmp_path / "empty_models")

    res = client.post(
        "/api/v1/predictions/waiting-time",
        json={"department_code": "ED", "acuity_level": 3, "queue_length": 2, "staff_available": 3},
    )
    assert res.status_code == 503
    assert "artifact is not available" in res.json()["detail"].lower()
