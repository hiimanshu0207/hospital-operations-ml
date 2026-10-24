"""
Tests for Prediction API endpoints (/api/v1/predictions/demand).
"""


def test_forecast_demand_valid_request(client):
    """POST /api/v1/predictions/demand should return 200 with structured 24h forecast."""
    payload = {
        "department_code": "ED",
        "horizon_hours": 24,
    }
    response = client.post("/api/v1/predictions/demand", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["department_code"] == "ED"
    assert data["horizon_hours"] == 24
    assert len(data["hourly_forecasts"]) == 24
    assert data["total_predicted_arrivals"] >= 0
    assert "disclaimer" in data
    assert "Simulated-data estimate" in data["disclaimer"]

    # Verify each hourly forecast
    for hf in data["hourly_forecasts"]:
        assert "timestamp" in hf
        assert "predicted_arrivals" in hf
        assert hf["predicted_arrivals"] >= 0


def test_forecast_demand_case_insensitivity(client):
    """POST /api/v1/predictions/demand should accept lowercase department codes."""
    payload = {
        "department_code": "icu",
        "horizon_hours": 12,
    }
    response = client.post("/api/v1/predictions/demand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["department_code"] == "ICU"
    assert len(data["hourly_forecasts"]) == 12


def test_forecast_demand_invalid_department_returns_404(client):
    """POST /api/v1/predictions/demand should return 404 for unknown department code."""
    payload = {
        "department_code": "INVALID_DEPT",
        "horizon_hours": 24,
    }
    response = client.post("/api/v1/predictions/demand", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_forecast_demand_invalid_horizon_returns_422(client):
    """POST /api/v1/predictions/demand should return 422 if horizon < 1 or > 72."""
    # Horizon 0
    res1 = client.post("/api/v1/predictions/demand", json={
        "department_code": "ED",
        "horizon_hours": 0,
    })
    assert res1.status_code == 422

    # Horizon 100 (> 72)
    res2 = client.post("/api/v1/predictions/demand", json={
        "department_code": "ED",
        "horizon_hours": 100,
    })
    assert res2.status_code == 422
