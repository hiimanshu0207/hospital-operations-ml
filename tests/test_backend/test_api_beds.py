"""
Tests for Bed API endpoints and occupancy management.
"""


def test_create_and_get_bed(client):
    """POST /api/v1/beds creates a bed and GET /api/v1/beds/{id} retrieves it."""
    # First create department
    dept_res = client.post("/api/v1/departments", json={
        "code": "TEST_DEPT",
        "name": "Test Dept",
        "total_beds": 5,
        "target_nurse_to_patient_ratio": 0.25,
    })
    dept_id = dept_res.json()["id"]

    # Create bed
    bed_payload = {
        "bed_number": "TEST-01",
        "department_id": dept_id,
        "bed_type": "Standard",
        "is_occupied": False,
    }
    create_res = client.post("/api/v1/beds", json=bed_payload)
    assert create_res.status_code == 201
    bed_data = create_res.json()
    assert bed_data["bed_number"] == "TEST-01"

    # Get bed
    get_res = client.get(f"/api/v1/beds/{bed_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["bed_type"] == "Standard"


def test_create_bed_invalid_department_returns_404(client):
    """POST /api/v1/beds with invalid department_id returns 404."""
    payload = {
        "bed_number": "BAD-01",
        "department_id": 9999,
        "bed_type": "Standard",
        "is_occupied": False,
    }
    res = client.post("/api/v1/beds", json=payload)
    assert res.status_code == 404


def test_update_bed_occupancy_and_capacity_constraint(client):
    """PATCH /api/v1/beds/{id}/occupancy should update status and respect capacity."""
    # Create department with total_beds = 1
    dept_res = client.post("/api/v1/departments", json={
        "code": "MINI",
        "name": "Mini Dept",
        "total_beds": 1,
        "target_nurse_to_patient_ratio": 0.5,
    })
    dept_id = dept_res.json()["id"]

    # Create 2 physical beds in this department
    b1 = client.post("/api/v1/beds", json={
        "bed_number": "MINI-01",
        "department_id": dept_id,
        "is_occupied": False,
    }).json()
    b2 = client.post("/api/v1/beds", json={
        "bed_number": "MINI-02",
        "department_id": dept_id,
        "is_occupied": False,
    }).json()

    # Occupy bed 1 -> succeeds
    patch1 = client.patch(f"/api/v1/beds/{b1['id']}/occupancy", json={"is_occupied": True})
    assert patch1.status_code == 200
    assert patch1.json()["is_occupied"] is True

    # Occupy bed 2 -> should fail because capacity is 1
    patch2 = client.patch(f"/api/v1/beds/{b2['id']}/occupancy", json={"is_occupied": True})
    assert patch2.status_code == 400
    assert "full capacity" in patch2.json()["detail"]


def test_list_beds_with_filters(seeded_client):
    """GET /api/v1/beds supports department_id and is_occupied filters."""
    # Get all beds
    all_res = seeded_client.get("/api/v1/beds?limit=200")
    assert all_res.status_code == 200
    all_beds = all_res.json()
    assert len(all_beds) == 122

    # Filter by department 1 (ED)
    ed_res = seeded_client.get("/api/v1/beds?department_id=1&limit=50")
    assert ed_res.status_code == 200
    assert len(ed_res.json()) == 25
