"""
FastAPI router for Department operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.department import Department
from app.models.bed import Bed
from app.schemas.department import DepartmentCreate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    """List all hospital departments along with computed bed occupancy metrics."""
    departments = db.query(Department).all()

    # Calculate current occupied beds per department
    occupancy_counts = dict(
        db.query(Bed.department_id, func.count(Bed.id))
        .filter(Bed.is_occupied.is_(True))
        .group_by(Bed.department_id)
        .all()
    )

    results = []
    for dept in departments:
        occupied = occupancy_counts.get(dept.id, 0)
        rate = round(occupied / dept.total_beds, 3) if dept.total_beds > 0 else 0.0
        results.append(
            DepartmentResponse(
                id=dept.id,
                code=dept.code,
                name=dept.name,
                total_beds=dept.total_beds,
                target_nurse_to_patient_ratio=dept.target_nurse_to_patient_ratio,
                created_at=dept.created_at,
                occupied_beds=occupied,
                occupancy_rate=rate,
            )
        )
    return results


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single department by ID."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )

    occupied = db.query(Bed).filter(Bed.department_id == dept.id, Bed.is_occupied.is_(True)).count()
    rate = round(occupied / dept.total_beds, 3) if dept.total_beds > 0 else 0.0

    return DepartmentResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        total_beds=dept.total_beds,
        target_nurse_to_patient_ratio=dept.target_nurse_to_patient_ratio,
        created_at=dept.created_at,
        occupied_beds=occupied,
        occupancy_rate=rate,
    )


@router.get("/{department_id}/metrics", response_model=DepartmentResponse)
def get_department_metrics(department_id: int, db: Session = Depends(get_db)):
    """Retrieve operational telemetry and occupancy metrics for a single department."""
    return get_department(department_id=department_id, db=db)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    """Create a new hospital department."""
    existing = db.query(Department).filter(Department.code == dept_in.code.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code '{dept_in.code}' already exists",
        )

    dept = Department(
        code=dept_in.code.upper(),
        name=dept_in.name,
        total_beds=dept_in.total_beds,
        target_nurse_to_patient_ratio=dept_in.target_nurse_to_patient_ratio,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return DepartmentResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        total_beds=dept.total_beds,
        target_nurse_to_patient_ratio=dept.target_nurse_to_patient_ratio,
        created_at=dept.created_at,
        occupied_beds=0,
        occupancy_rate=0.0,
    )
