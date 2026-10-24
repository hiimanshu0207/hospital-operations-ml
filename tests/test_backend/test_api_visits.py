"""
Tests for PatientVisit API endpoints and operational metrics.
"""

from datetime import datetime, timezone, timedelta


def test_list_visits_and_summary_metrics(seeded_client):
    """GET /api/v1/visits and /metrics/summary should return computed stats."""
    # List visits
    res = seeded_client.get("/api/v1/visits?limit=25")
    assert res.status_code == 200
    visits = res.json()
    assert len(visits) == 25
    first = visits[0]
    assert "visit_id" in first
    assert "waiting_time_minutes" in first
    assert first["waiting_time_minutes"] >= 0

    # Summary metrics
    summary_res = seeded_client.get("/api/v1/visits/metrics/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_visits"] == 60
    assert summary["avg_waiting_time_minutes"] >= 0
    assert summary["avg_length_of_stay_minutes"] > 0
    assert "acuity_breakdown" in summary
    assert "department_breakdown" in summary


def test_get_visit_by_id_and_code(seeded_client):
    """GET /api/v1/visits/{identifier} should support integer ID and visit_id string."""
    # Get first visit
    list_res = seeded_client.get("/api/v1/visits?limit=1")
    first_visit = list_res.json()[0]
    pk_id = first_visit["id"]
    code_id = first_visit["visit_id"]

    # By numeric PK
    by_pk = seeded_client.get(f"/api/v1/visits/{pk_id}")
    assert by_pk.status_code == 200
    assert by_pk.json()["visit_id"] == code_id

    # By synthetic visit_id code
    by_code = seeded_client.get(f"/api/v1/visits/{code_id}")
    assert by_code.status_code == 200
    assert by_code.json()["id"] == pk_id


def test_create_valid_patient_visit(client):
    """POST /api/v1/visits should create visit with valid operational data."""
    # Create department first
    dept = client.post("/api/v1/departments", json={
        "code": "ED",
        "name": "Emergency",
        "total_beds": 10,
        "target_nurse_to_patient_ratio": 0.35,
    }).json()

    now = datetime.now(timezone.utc)
    payload = {
        "visit_id": "VIS-MANUAL-001",
        "department_id": dept["id"],
        "patient_age_group": "18-35",
        "acuity_level": 3,
        "arrival_timestamp": now.isoformat(),
        "queue_length_at_arrival": 3,
        "staff_available_at_arrival": 4,
        "service_start_timestamp": (now + timedelta(minutes=20)).isoformat(),
        "service_end_timestamp": (now + timedelta(minutes=140)).isoformat(),
        "waiting_time_minutes": 20.0,
        "length_of_stay_minutes": 120.0,
        "total_duration_minutes": 140.0,
        "admission_required": False,
        "status": "Completed",
    }
    res = client.post("/api/v1/visits", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["visit_id"] == "VIS-MANUAL-001"
    assert data["waiting_time_minutes"] == 20.0


def test_create_visit_rejects_negative_waiting_time(client):
    """POST /api/v1/visits should reject negative waiting duration."""
    dept = client.post("/api/v1/departments", json={
        "code": "ED",
        "name": "Emergency",
        "total_beds": 10,
        "target_nurse_to_patient_ratio": 0.35,
    }).json()

    now = datetime.now(timezone.utc)
    payload = {
        "visit_id": "VIS-INVALID-WAIT",
        "department_id": dept["id"],
        "patient_age_group": "18-35",
        "acuity_level": 3,
        "arrival_timestamp": now.isoformat(),
        "service_start_timestamp": now.isoformat(),
        "service_end_timestamp": (now + timedelta(minutes=60)).isoformat(),
        "waiting_time_minutes": -15.0,  # Negative!
        "length_of_stay_minutes": 60.0,
        "total_duration_minutes": 45.0,
    }
    res = client.post("/api/v1/visits", json=payload)
    assert res.status_code == 422


def test_create_visit_rejects_service_start_before_arrival(client):
    """POST /api/v1/visits should reject timestamps where service starts before arrival."""
    dept = client.post("/api/v1/departments", json={
        "code": "ED",
        "name": "Emergency",
        "total_beds": 10,
        "target_nurse_to_patient_ratio": 0.35,
    }).json()

    now = datetime.now(timezone.utc)
    payload = {
        "visit_id": "VIS-INVALID-TIME",
        "department_id": dept["id"],
        "patient_age_group": "18-35",
        "acuity_level": 2,
        "arrival_timestamp": now.isoformat(),
        "service_start_timestamp": (now - timedelta(minutes=10)).isoformat(),  # Before arrival!
        "service_end_timestamp": (now + timedelta(minutes=60)).isoformat(),
        "waiting_time_minutes": 10.0,
        "length_of_stay_minutes": 70.0,
        "total_duration_minutes": 60.0,
    }
    res = client.post("/api/v1/visits", json=payload)
    assert res.status_code == 422


def test_create_visit_rejects_invalid_acuity(client):
    """POST /api/v1/visits should reject acuity level > 5."""
    dept = client.post("/api/v1/departments", json={
        "code": "ED",
        "name": "Emergency",
        "total_beds": 10,
        "target_nurse_to_patient_ratio": 0.35,
    }).json()

    now = datetime.now(timezone.utc)
    payload = {
        "visit_id": "VIS-INVALID-ACUITY",
        "department_id": dept["id"],
        "patient_age_group": "18-35",
        "acuity_level": 7,  # Invalid! Must be 1-5
        "arrival_timestamp": now.isoformat(),
        "service_start_timestamp": now.isoformat(),
        "service_end_timestamp": (now + timedelta(minutes=60)).isoformat(),
        "waiting_time_minutes": 0.0,
        "length_of_stay_minutes": 60.0,
        "total_duration_minutes": 60.0,
    }
    res = client.post("/api/v1/visits", json=payload)
    assert res.status_code == 422


def test_patient_visits_summary_and_recent_endpoints(seeded_client):
    """GET /api/v1/patient-visits/summary and /recent should return consistent operational telemetry."""
    # Summary via /api/v1/patient-visits/summary
    summary_res = seeded_client.get("/api/v1/patient-visits/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_visits"] == 60
    assert summary["avg_waiting_time_minutes"] >= 0
    assert summary["avg_length_of_stay_minutes"] > 0
    assert summary["total_admissions"] >= 0
    assert isinstance(summary["acuity_breakdown"], dict)
    assert isinstance(summary["department_breakdown"], dict)
    assert len(summary["acuity_breakdown"]) > 0

    # Summary alias via /api/v1/visits/summary
    alias_summary_res = seeded_client.get("/api/v1/visits/summary")
    assert alias_summary_res.status_code == 200
    assert alias_summary_res.json() == summary

    # Recent encounters via /api/v1/patient-visits/recent?limit=8
    recent_res = seeded_client.get("/api/v1/patient-visits/recent?limit=8")
    assert recent_res.status_code == 200
    recent = recent_res.json()
    assert len(recent) == 8

    # Verify response schema fields expected by the dashboard
    first = recent[0]
    assert "id" in first
    assert "visit_id" in first
    assert "patient_age_group" in first
    assert "acuity_level" in first
    assert "queue_length_at_arrival" in first
    assert "staff_available_at_arrival" in first
    assert "waiting_time_minutes" in first
    assert "status" in first
    assert "arrival_timestamp" in first

    # Verify descending ordering by arrival_timestamp
    timestamps = [r["arrival_timestamp"] for r in recent]
    assert timestamps == sorted(timestamps, reverse=True)

    # Recent encounters alias via /api/v1/visits/recent?limit=5
    alias_recent_res = seeded_client.get("/api/v1/visits/recent?limit=5")
    assert alias_recent_res.status_code == 200
    assert len(alias_recent_res.json()) == 5


def test_patient_visits_recent_limit_validation(client):
    """GET /api/v1/patient-visits/recent should reject limits outside 1-100 or non-integer."""
    # limit = 0 (below minimum 1)
    res_zero = client.get("/api/v1/patient-visits/recent?limit=0")
    assert res_zero.status_code == 422

    # limit = -5 (negative)
    res_neg = client.get("/api/v1/patient-visits/recent?limit=-5")
    assert res_neg.status_code == 422

    # limit = 101 (above maximum 100)
    res_max = client.get("/api/v1/patient-visits/recent?limit=101")
    assert res_max.status_code == 422

    # limit = non-integer
    res_str = client.get("/api/v1/patient-visits/recent?limit=invalid")
    assert res_str.status_code == 422


def test_patient_visits_empty_database(client):
    """Endpoints should handle empty database state gracefully without crashing or 404."""
    # Empty summary
    summary_res = client.get("/api/v1/patient-visits/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_visits"] == 0
    assert summary["avg_waiting_time_minutes"] == 0.0
    assert summary["avg_length_of_stay_minutes"] == 0.0
    assert summary["total_admissions"] == 0
    assert summary["acuity_breakdown"] == {}
    assert summary["department_breakdown"] == {}

    # Empty recent encounters
    recent_res = client.get("/api/v1/patient-visits/recent?limit=8")
    assert recent_res.status_code == 200
    assert recent_res.json() == []

