"""
FastAPI router for Bed operations and occupancy management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bed import Bed
from app.models.department import Department
from app.schemas.bed import BedCreate, BedOccupancyUpdate, BedResponse, BedSummaryResponse

router = APIRouter(prefix="/beds", tags=["beds"])


@router.get("", response_model=list[BedResponse])
def list_beds(
    department_id: int | None = Query(default=None, description="Filter by department ID"),
    is_occupied: bool | None = Query(default=None, description="Filter by occupancy status"),
    bed_type: str | None = Query(default=None, description="Filter by bed type"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List physical beds with optional department and occupancy filters."""
    query = db.query(Bed)
    if department_id is not None:
        query = query.filter(Bed.department_id == department_id)
    if is_occupied is not None:
        query = query.filter(Bed.is_occupied.is_(is_occupied))
    if bed_type is not None:
        query = query.filter(Bed.bed_type == bed_type)

    return query.offset(offset).limit(limit).all()


@router.get("/summary", response_model=BedSummaryResponse)
def get_beds_summary(db: Session = Depends(get_db)):
    """Retrieve aggregated bed occupancy and availability metrics across the hospital."""
    total = db.query(Bed).count()
    occupied = db.query(Bed).filter(Bed.is_occupied.is_(True)).count()
    available = max(0, total - occupied)
    rate = round(occupied / total, 3) if total > 0 else 0.0
    return BedSummaryResponse(
        total_beds=total,
        occupied_beds=occupied,
        available_beds=available,
        overall_occupancy_rate=rate,
    )


@router.get("/{bed_id}", response_model=BedResponse)
def get_bed(bed_id: int, db: Session = Depends(get_db)):
    """Retrieve single bed details by ID."""
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bed with ID {bed_id} not found",
        )
    return bed


@router.post("", response_model=BedResponse, status_code=status.HTTP_201_CREATED)
def create_bed(bed_in: BedCreate, db: Session = Depends(get_db)):
    """Create and register a new physical hospital bed."""
    dept = db.query(Department).filter(Department.id == bed_in.department_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {bed_in.department_id} does not exist",
        )

    existing = db.query(Bed).filter(Bed.bed_number == bed_in.bed_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bed with number '{bed_in.bed_number}' already exists",
        )

    bed = Bed(
        bed_number=bed_in.bed_number,
        department_id=bed_in.department_id,
        bed_type=bed_in.bed_type,
        is_occupied=bed_in.is_occupied,
    )
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return bed


@router.patch("/{bed_id}/occupancy", response_model=BedResponse)
def update_bed_occupancy(
    bed_id: int,
    occupancy_in: BedOccupancyUpdate,
    db: Session = Depends(get_db),
):
    """
    Update bed occupancy status.

    Validates that setting a bed to occupied does not exceed the department's
    total bed capacity.
    """
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bed with ID {bed_id} not found",
        )

    if occupancy_in.is_occupied and not bed.is_occupied:
        # Check capacity constraint
        dept = db.query(Department).filter(Department.id == bed.department_id).first()
        if dept:
            currently_occupied = db.query(Bed).filter(
                Bed.department_id == dept.id,
                Bed.is_occupied.is_(True),
            ).count()
            if currently_occupied >= dept.total_beds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Cannot occupy bed: Department '{dept.name}' is already at "
                        f"full capacity ({dept.total_beds} beds occupied)."
                    ),
                )

    bed.is_occupied = occupancy_in.is_occupied
    db.commit()
    db.refresh(bed)
    return bed
