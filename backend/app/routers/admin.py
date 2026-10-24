"""
Administrative and synthetic data management endpoints.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.models.staff import Staff
from app.models.bed import Bed
from app.models.patient_visit import PatientVisit
from app.services.synthetic_generator import seed_database

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed", status_code=status.HTTP_200_OK)
def trigger_seed(
    seed: int = Query(default=42, description="Random seed for reproducible dataset generation"),
    num_visits: int = Query(default=600, ge=50, le=5000, description="Total patient encounters to simulate"),
    db: Session = Depends(get_db),
):
    """
    Seed database with fresh, reproducible synthetic hospital operational records.

    Generates departments, staff, physical beds, and patient visits while enforcing
    all operational integrity constraints.
    """
    result = seed_database(db=db, seed=seed, num_visits=num_visits)
    return {
        "status": "success",
        "message": "Database successfully populated with synthetic hospital data",
        "seed": seed,
        "details": result,
    }


@router.get("/counts")
def get_entity_counts(db: Session = Depends(get_db)):
    """Return database record counts across all domain entities."""
    return {
        "departments": db.query(Department).count(),
        "staff": db.query(Staff).count(),
        "beds": db.query(Bed).count(),
        "patient_visits": db.query(PatientVisit).count(),
    }
