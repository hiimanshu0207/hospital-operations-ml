"""
FastAPI router for hospital resource utilization, what-if simulation, and staff allocation optimization.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.optimization import (
    ResourceUtilizationResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    StaffAllocationRequest,
    StaffAllocationResponse,
)
from ml.optimization import (
    load_hospital_operational_state,
    calculate_department_utilization,
    simulate_what_if_scenario,
    optimize_staff_allocation,
)

router = APIRouter(prefix="/optimization", tags=["optimization"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
DATA_DIR = PROJECT_ROOT / "data"


@router.get(
    "/utilization",
    response_model=ResourceUtilizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Departmental resource utilization and capacity analysis",
)
def get_resource_utilization(
    db: Session = Depends(get_db),
):
    """
    Retrieve real-time departmental bed utilization, staff availability, queue pressures,
    and ML estimated waiting-time indicators.

    Distinguishes observed operational data from predictive estimators and flags active capacity warnings.
    """
    try:
        state = load_hospital_operational_state(db=db, data_dir=DATA_DIR)
        return calculate_department_utilization(state, models_dir=MODELS_DIR)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate resource utilization: {str(exc)}",
        )


@router.post(
    "/simulate",
    response_model=WhatIfSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run what-if scenario simulation",
)
def simulate_scenario(
    request: WhatIfSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Simulate hypothetical operational scenarios (arrival surges, staff adjustments, bed capacity changes).

    Validates:
    - Arrival surge bounds (-50% to +100%)
    - Minimum staff safety constraints
    - Non-negative bed allocations
    - Pure non-mutating transformation
    """
    try:
        state = load_hospital_operational_state(db=db, data_dir=DATA_DIR)
        result = simulate_what_if_scenario(
            state=state,
            arrival_surge_pct=request.arrival_surge_pct,
            staff_adjustments=request.staff_adjustments,
            bed_capacity_adjustments=request.bed_capacity_adjustments,
            time_horizon_hours=request.time_horizon_hours,
            simulation_seed=request.simulation_seed,
            models_dir=MODELS_DIR,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run what-if simulation: {str(exc)}",
        )


@router.post(
    "/allocate",
    response_model=StaffAllocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Optimize staff allocation across departments",
)
def allocate_staff(
    request: StaffAllocationRequest,
    db: Session = Depends(get_db),
):
    """
    Generate transparent, constraint-aware staff allocation recommendations.

    Formulation:
    - Balanced objective minimizing weighted waiting pressure and churn penalty.
    - Conserves total staff budget (headcount conservation).
    - Enforces department safety minimums and maximum physical capacities.
    - Provides rule-based baseline comparison and clinical rationale.
    """
    try:
        state = load_hospital_operational_state(db=db, data_dir=DATA_DIR)
        result = optimize_staff_allocation(
            state=state,
            shift=request.shift,
            total_staff_budget=request.total_staff_budget,
            min_staff_per_dept=request.min_staff_per_dept,
            max_staff_per_dept=request.max_staff_per_dept,
            priority_weights=request.priority_weights,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize staff allocation: {str(exc)}",
        )
