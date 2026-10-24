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


# ---------------------------------------------------------------------------
# Waiting-Time Prediction API Tests (/api/v1/predictions/waiting-time)
# ---------------------------------------------------------------------------

def test_predict_waiting_time_valid_request(client):
    """POST /api/v1/predictions/waiting-time should return 200 with structured waiting-time estimate."""
    payload = {
        "department_code": "ED",
        "acuity_level": 3,
        "queue_length": 4,
        "staff_available": 3,
        "patient_age_group": "36-50",
    }
    response = client.post("/api/v1/predictions/waiting-time", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["department_code"] == "ED"
    assert data["department_name"] == "Emergency Department"
    assert data["acuity_level"] == 3
    assert data["estimated_waiting_time_minutes"] >= 0.0
    assert 0.0 <= data["confidence_lower"] <= data["estimated_waiting_time_minutes"] <= data["confidence_upper"]
    assert data["model_name"] == "RandomForestRegressor"
    assert data["model_version"] == "1.0.0"
    assert "operational_context" in data
    assert data["operational_context"]["queue_length"] == 4
    assert data["operational_context"]["staff_available"] == 3
    assert "disclaimer" in data
    assert "SIMULATED OPERATIONAL ESTIMATE" in data["disclaimer"]


def test_predict_waiting_time_case_insensitivity(client):
    """POST /api/v1/predictions/waiting-time should accept lowercase department codes."""
    payload = {
        "department_code": "gen",
        "acuity_level": 4,
        "queue_length": 2,
        "staff_available": 4,
    }
    response = client.post("/api/v1/predictions/waiting-time", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["department_code"] == "GEN"
    assert data["department_name"] == "General Medicine Ward"
    assert data["estimated_waiting_time_minutes"] >= 0.0


def test_predict_waiting_time_invalid_department_returns_404(client):
    """POST /api/v1/predictions/waiting-time should return 404 for unknown department code."""
    payload = {
        "department_code": "NEUROLOGY",
        "acuity_level": 2,
    }
    response = client.post("/api/v1/predictions/waiting-time", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_predict_waiting_time_invalid_acuity_returns_422(client):
    """POST /api/v1/predictions/waiting-time should return 422 if acuity < 1 or > 5."""
    res1 = client.post("/api/v1/predictions/waiting-time", json={
        "department_code": "ED",
        "acuity_level": 0,
    })
    assert res1.status_code == 422

    res2 = client.post("/api/v1/predictions/waiting-time", json={
        "department_code": "ED",
        "acuity_level": 6,
    })
    assert res2.status_code == 422


def test_predict_waiting_time_negative_queue_returns_422(client):
    """POST /api/v1/predictions/waiting-time should return 422 if queue_length < 0."""
    response = client.post("/api/v1/predictions/waiting-time", json={
        "department_code": "ED",
        "acuity_level": 3,
        "queue_length": -3,
    })
    assert response.status_code == 422


def test_predict_waiting_time_zero_staff_returns_422(client):
    """POST /api/v1/predictions/waiting-time should return 422 if staff_available < 1."""
    response = client.post("/api/v1/predictions/waiting-time", json={
        "department_code": "ED",
        "acuity_level": 3,
        "staff_available": 0,
    })
    assert response.status_code == 422


def test_predict_waiting_time_missing_model_returns_503(client, monkeypatch):
    """POST /api/v1/predictions/waiting-time should return 503 if model artifact is unavailable."""
    from pathlib import Path
    from app.routers import predictions

    monkeypatch.setattr(predictions, "MODELS_DIR", Path("nonexistent_models_dir_test"))

    payload = {
        "department_code": "ED",
        "acuity_level": 3,
    }
    response = client.post("/api/v1/predictions/waiting-time", json=payload)
    assert response.status_code == 503
    assert "not available" in response.json()["detail"].lower()

