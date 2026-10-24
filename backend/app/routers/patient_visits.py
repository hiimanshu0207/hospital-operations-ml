"""
FastAPI router for PatientVisit operations and operational metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.patient_visit import PatientVisit
from app.models.department import Department
from app.models.bed import Bed
from app.schemas.patient_visit import (
    PatientVisitCreate,
    PatientVisitResponse,
    PatientVisitSummary,
)

router = APIRouter(tags=["patient_visits"])


@router.get("", response_model=list[PatientVisitResponse])
def list_visits(
    department_id: int | None = Query(default=None, description="Filter by department ID"),
    acuity_level: int | None = Query(default=None, ge=1, le=5, description="Filter by acuity level (1-5)"),
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List operational patient encounters with filtering and pagination."""
    query = db.query(PatientVisit)
    if department_id is not None:
        query = query.filter(PatientVisit.department_id == department_id)
    if acuity_level is not None:
        query = query.filter(PatientVisit.acuity_level == acuity_level)
    if status_filter is not None:
        query = query.filter(PatientVisit.status == status_filter)

    return query.order_by(PatientVisit.arrival_timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/recent", response_model=list[PatientVisitResponse])
def get_recent_visits(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of recent patient visits to return"),
    db: Session = Depends(get_db),
):
    """Retrieve the most recent patient visits ordered by arrival timestamp descending."""
    return (
        db.query(PatientVisit)
        .order_by(PatientVisit.arrival_timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/summary", response_model=PatientVisitSummary)
@router.get("/metrics/summary", response_model=PatientVisitSummary)
def get_visits_summary(db: Session = Depends(get_db)):
    """Compute high-level operational statistics across all patient visits."""
    total = db.query(PatientVisit).count()
    if total == 0:
        return PatientVisitSummary(
            total_visits=0,
            avg_waiting_time_minutes=0.0,
            avg_length_of_stay_minutes=0.0,
            total_admissions=0,
            acuity_breakdown={},
            department_breakdown={},
        )

    avg_wait = db.query(func.avg(PatientVisit.waiting_time_minutes)).scalar() or 0.0
    avg_los = db.query(func.avg(PatientVisit.length_of_stay_minutes)).scalar() or 0.0
    admissions = db.query(PatientVisit).filter(PatientVisit.admission_required.is_(True)).count()

    acuity_rows = (
        db.query(PatientVisit.acuity_level, func.count(PatientVisit.id))
        .group_by(PatientVisit.acuity_level)
        .all()
    )
    acuity_breakdown = {int(k): int(v) for k, v in acuity_rows}

    dept_rows = (
        db.query(Department.code, func.count(PatientVisit.id))
        .join(PatientVisit, PatientVisit.department_id == Department.id)
        .group_by(Department.code)
        .all()
    )
    department_breakdown = {str(k): int(v) for k, v in dept_rows}

    return PatientVisitSummary(
        total_visits=total,
        avg_waiting_time_minutes=round(float(avg_wait), 2),
        avg_length_of_stay_minutes=round(float(avg_los), 2),
        total_admissions=admissions,
        acuity_breakdown=acuity_breakdown,
        department_breakdown=department_breakdown,
    )


@router.get("/{identifier}", response_model=PatientVisitResponse)
def get_visit(identifier: str, db: Session = Depends(get_db)):
    """Retrieve visit by integer primary key or synthetic visit_id code."""
    if identifier.isdigit():
        visit = db.query(PatientVisit).filter(PatientVisit.id == int(identifier)).first()
    else:
        visit = db.query(PatientVisit).filter(PatientVisit.visit_id == identifier).first()

    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient visit '{identifier}' not found",
        )
    return visit


@router.post("", response_model=PatientVisitResponse, status_code=status.HTTP_201_CREATED)
def create_visit(visit_in: PatientVisitCreate, db: Session = Depends(get_db)):
    """
    Create a new synthetic operational patient visit record.

    Validates:
    - Department existence
    - Duplicate visit_id prevention
    - Bed assignment validity and capacity limits
    """
    # Department verification
    dept = db.query(Department).filter(Department.id == visit_in.department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {visit_in.department_id} not found",
        )

    # Unique visit_id verification
    existing = db.query(PatientVisit).filter(PatientVisit.visit_id == visit_in.visit_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Visit with ID '{visit_in.visit_id}' already exists",
        )

    # Bed allocation verification if specified
    if visit_in.bed_id is not None:
        bed = db.query(Bed).filter(Bed.id == visit_in.bed_id).first()
        if not bed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bed with ID {visit_in.bed_id} not found",
            )
        if bed.department_id != visit_in.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bed {bed.bed_number} does not belong to department {dept.name}",
            )
        if bed.is_occupied:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bed {bed.bed_number} is already occupied",
            )
        bed.is_occupied = True

    visit = PatientVisit(
        visit_id=visit_in.visit_id,
        department_id=visit_in.department_id,
        patient_age_group=visit_in.patient_age_group,
        acuity_level=visit_in.acuity_level,
        arrival_timestamp=visit_in.arrival_timestamp,
        queue_length_at_arrival=visit_in.queue_length_at_arrival,
        staff_available_at_arrival=visit_in.staff_available_at_arrival,
        service_start_timestamp=visit_in.service_start_timestamp,
        service_end_timestamp=visit_in.service_end_timestamp,
        waiting_time_minutes=visit_in.waiting_time_minutes,
        length_of_stay_minutes=visit_in.length_of_stay_minutes,
        total_duration_minutes=visit_in.total_duration_minutes,
        admission_required=visit_in.admission_required,
        bed_id=visit_in.bed_id,
        status=visit_in.status,
    )

    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit
