"""
Tests for Department API endpoints.
"""


def test_list_departments_empty(client):
    """GET /api/v1/departments should return empty list when no departments exist."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_get_department(client):
    """POST /api/v1/departments should create department and GET should retrieve it."""
    payload = {
        "code": "NEURO",
        "name": "Neurology Department",
        "total_beds": 18,
        "target_nurse_to_patient_ratio": 0.30,
    }
    create_res = client.post("/api/v1/departments", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["code"] == "NEURO"
    assert created_data["id"] is not None

    dept_id = created_data["id"]
    get_res = client.get(f"/api/v1/departments/{dept_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Neurology Department"


def test_create_duplicate_department_code_fails(client):
    """POST /api/v1/departments should return 400 for duplicate code."""
    payload = {
        "code": "CARD",
        "name": "Cardiology",
        "total_beds": 15,
        "target_nurse_to_patient_ratio": 0.25,
    }
    res1 = client.post("/api/v1/departments", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/departments", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_get_nonexistent_department_returns_404(client):
    """GET /api/v1/departments/999 should return 404."""
    response = client.get("/api/v1/departments/999")
    assert response.status_code == 404


def test_list_departments_with_seeded_data(seeded_client):
    """GET /api/v1/departments should return 5 seeded departments with occupancy info."""
    response = seeded_client.get("/api/v1/departments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    codes = {d["code"] for d in data}
    assert codes == {"ED", "ICU", "GEN", "SURG", "PED"}
    for dept in data:
        assert dept["total_beds"] > 0
        assert "occupancy_rate" in dept
