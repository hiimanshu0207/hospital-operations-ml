"""
Integration tests for FastAPI resource optimization and simulation endpoints:
- GET /api/v1/optimization/utilization
- POST /api/v1/optimization/simulate
- POST /api/v1/optimization/allocate
"""


def test_get_utilization_endpoint(client):
    """GET /api/v1/optimization/utilization should return 200 with structured hospital summary and department metrics."""
    response = client.get("/api/v1/optimization/utilization")
    assert response.status_code == 200

    data = response.json()
    assert "hospital_summary" in data
    assert "department_utilization" in data
    assert "active_warnings" in data
    assert "disclaimer" in data

    summary = data["hospital_summary"]
    assert summary["total_beds"] > 0
    assert summary["total_active_staff"] > 0
    assert 0.0 <= summary["overall_bed_utilization_pct"] <= 100.0

    depts = data["department_utilization"]
    assert len(depts) == 5
    dept_codes = {d["department_code"] for d in depts}
    assert dept_codes == {"ED", "ICU", "GEN", "SURG", "PED"}

    for d in depts:
        assert "bed_capacity" in d
        assert "staffing" in d
        assert "queue_and_demand" in d
        assert "estimated_wait_time" in d
        assert d["estimated_wait_time"]["estimated_minutes"] >= 0.0


def test_simulate_endpoint_valid_request(client):
    """POST /api/v1/optimization/simulate should return 200 with baseline vs. simulated comparisons."""
    payload = {
        "arrival_surge_pct": 20.0,
        "staff_adjustments": {"ED": 2, "GEN": -1},
        "bed_capacity_adjustments": {"ED": 5},
        "time_horizon_hours": 12,
    }
    response = client.post("/api/v1/optimization/simulate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "simulation_parameters" in data
    assert "overall_impact" in data
    assert "department_comparisons" in data
    assert "assumptions" in data
    assert "disclaimer" in data

    assert data["simulation_parameters"]["arrival_surge_pct"] == 20.0
    assert len(data["department_comparisons"]) == 5

    ed_comp = next(d for d in data["department_comparisons"] if d["department_code"] == "ED")
    assert ed_comp["delta"]["staff_change"] == 2
    assert ed_comp["delta"]["bed_capacity_change"] == 5
    assert ed_comp["simulated"]["total_beds"] == ed_comp["baseline"]["total_beds"] + 5
    assert ed_comp["simulated"]["active_staff"] == ed_comp["baseline"]["active_staff"] + 2
    assert ed_comp["simulated"]["estimated_wait_time_minutes"] >= 0.0


def test_simulate_endpoint_surge_out_of_bounds_returns_422(client):
    """POST /api/v1/optimization/simulate should return 422 for surge percentages outside [-50%, +100%]."""
    # Over +100%
    res1 = client.post("/api/v1/optimization/simulate", json={"arrival_surge_pct": 125.0})
    assert res1.status_code == 422

    # Under -50%
    res2 = client.post("/api/v1/optimization/simulate", json={"arrival_surge_pct": -65.0})
    assert res2.status_code == 422


def test_simulate_endpoint_staff_below_minimum_returns_422(client):
    """POST /api/v1/optimization/simulate should return 422 if staff reduction violates department minimum safety constraint."""
    payload = {
        "staff_adjustments": {"ED": -20},
    }
    response = client.post("/api/v1/optimization/simulate", json=payload)
    assert response.status_code == 422
    assert "safety minimum" in response.json()["detail"].lower()


def test_simulate_endpoint_invalid_department_returns_422(client):
    """POST /api/v1/optimization/simulate should return 422 for unrecognized department code in adjustments."""
    payload = {
        "staff_adjustments": {"UNKNOWN_WARD": 2},
    }
    response = client.post("/api/v1/optimization/simulate", json=payload)
    assert response.status_code == 422
    assert "unknown department" in response.json()["detail"].lower()


def test_allocate_endpoint_valid_default_request(client):
    """POST /api/v1/optimization/allocate should return 200 with constrained staff allocation conserving budget."""
    response = client.post("/api/v1/optimization/allocate", json={})
    assert response.status_code == 200

    data = response.json()
    assert data["budget_conserved"] is True
    assert data["total_allocated_staff"] == data["total_staff_budget"]
    assert len(data["recommendations"]) == 5
    assert "rule_based_comparison" in data
    assert "governance_notice" in data

    for rec in data["recommendations"]:
        assert rec["department_code"] in ["ED", "ICU", "GEN", "SURG", "PED"]
        assert rec["recommended_staff"] >= rec["minimum_staff_constraint"]
        assert rec["recommended_staff"] <= rec["maximum_staff_constraint"]
        assert len(rec["rationale"]) > 0


def test_allocate_endpoint_shift_filter(client):
    """POST /api/v1/optimization/allocate should support shift-specific optimization."""
    payload = {
        "shift": "Morning",
    }
    response = client.post("/api/v1/optimization/allocate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["shift"] == "Morning"
    assert data["budget_conserved"] is True
    assert data["total_allocated_staff"] == data["total_staff_budget"]


def test_allocate_endpoint_custom_budget(client):
    """POST /api/v1/optimization/allocate should conserve explicitly requested total staff budget."""
    payload = {
        "total_staff_budget": 80,
    }
    response = client.post("/api/v1/optimization/allocate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_staff_budget"] == 80
    assert data["total_allocated_staff"] == 80
    assert data["budget_conserved"] is True


def test_allocate_endpoint_insufficient_budget_returns_422(client):
    """POST /api/v1/optimization/allocate should return 422 if budget is below mandatory safety minimums."""
    payload = {
        "total_staff_budget": 5,
    }
    response = client.post("/api/v1/optimization/allocate", json=payload)
    assert response.status_code == 422
    assert "insufficient" in response.json()["detail"].lower()


def test_allocate_endpoint_invalid_shift_returns_422(client):
    """POST /api/v1/optimization/allocate should return 422 for unrecognized shift."""
    payload = {
        "shift": "Midday",
    }
    response = client.post("/api/v1/optimization/allocate", json=payload)
    assert response.status_code == 422
    assert "invalid shift" in response.json()["detail"].lower()
