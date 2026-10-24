"""
Tests for SQLAlchemy domain models.

Verifies table creation, CRUD operations, relationships, and integrity constraints.
"""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.department import Department
from app.models.staff import Staff
from app.models.bed import Bed
from app.models.patient_visit import PatientVisit


def test_create_department_and_relationships(db_session):
    """Department should support related beds and staff."""
    dept = Department(
        code="ED",
        name="Emergency Department",
        total_beds=20,
        target_nurse_to_patient_ratio=0.35,
    )
    db_session.add(dept)
    db_session.commit()

    assert dept.id is not None
    assert dept.code == "ED"

    # Add bed
    bed = Bed(bed_number="ED-01", department_id=dept.id, bed_type="Emergency", is_occupied=False)
    # Add staff
    staff = Staff(staff_id="STF-ED-001", role="Doctor", department_id=dept.id, shift="Morning")

    db_session.add_all([bed, staff])
    db_session.commit()

    db_session.refresh(dept)
    assert len(dept.beds) == 1
    assert len(dept.staff) == 1
    assert dept.beds[0].bed_number == "ED-01"
    assert dept.staff[0].staff_id == "STF-ED-001"


def test_department_unique_code_constraint(db_session):
    """Department code must be unique."""
    d1 = Department(code="ICU", name="Intensive Care Unit", total_beds=10)
    d2 = Department(code="ICU", name="Duplicate ICU", total_beds=12)
    db_session.add(d1)
    db_session.commit()

    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_bed_unique_number_constraint(db_session):
    """Bed numbers must be unique across the hospital."""
    dept = Department(code="GEN", name="General Ward", total_beds=20)
    db_session.add(dept)
    db_session.commit()

    b1 = Bed(bed_number="B-101", department_id=dept.id)
    b2 = Bed(bed_number="B-101", department_id=dept.id)
    db_session.add(b1)
    db_session.commit()

    db_session.add(b2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_create_patient_visit(db_session):
    """Patient visit should persist with all operational attributes."""
    dept = Department(code="SURG", name="Surgery Ward", total_beds=15)
    db_session.add(dept)
    db_session.commit()

    bed = Bed(bed_number="SURG-01", department_id=dept.id, is_occupied=True)
    db_session.add(bed)
    db_session.commit()

    now = datetime.now(timezone.utc)
    visit = PatientVisit(
        visit_id="VIS-2026-TEST01",
        department_id=dept.id,
        patient_age_group="36-50",
        acuity_level=2,
        arrival_timestamp=now,
        queue_length_at_arrival=2,
        staff_available_at_arrival=4,
        service_start_timestamp=now + timedelta(minutes=15),
        service_end_timestamp=now + timedelta(minutes=180),
        waiting_time_minutes=15.0,
        length_of_stay_minutes=165.0,
        total_duration_minutes=180.0,
        admission_required=True,
        bed_id=bed.id,
        status="Completed",
    )
    db_session.add(visit)
    db_session.commit()

    assert visit.id is not None
    assert visit.department.code == "SURG"
    assert visit.bed.bed_number == "SURG-01"


def test_patient_visit_negative_wait_time_constraint(db_session):
    """Database check constraint should prevent negative waiting time."""
    dept = Department(code="PED", name="Pediatrics", total_beds=10)
    db_session.add(dept)
    db_session.commit()

    now = datetime.now(timezone.utc)
    invalid_visit = PatientVisit(
        visit_id="VIS-INVALID-01",
        department_id=dept.id,
        patient_age_group="0-17",
        acuity_level=3,
        arrival_timestamp=now,
        service_start_timestamp=now,
        service_end_timestamp=now + timedelta(minutes=30),
        waiting_time_minutes=-10.0,  # Negative!
        length_of_stay_minutes=30.0,
        total_duration_minutes=20.0,
    )
    db_session.add(invalid_visit)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
