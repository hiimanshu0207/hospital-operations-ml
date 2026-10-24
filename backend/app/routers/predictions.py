"""
FastAPI router for Machine Learning predictions and demand forecasting.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.schemas.prediction import (
    DemandForecastRequest,
    DemandForecastResponse,
    WaitingTimePredictionRequest,
    WaitingTimePredictionResponse,
)
from ml.demand_forecast import predict_future_demand, DEPT_CODES
from ml.waiting_time import predict_waiting_time

router = APIRouter(prefix="/predictions", tags=["predictions"])

# Resolve models directory relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"


@router.post(
    "/demand",
    response_model=DemandForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Forecast hourly patient arrival demand",
)
def forecast_patient_demand(
    request: DemandForecastRequest,
    db: Session = Depends(get_db),
):
    """
    Predict hourly patient arrivals for a specific hospital department over a future horizon.

    Validates:
    - Department code existence in hospital configuration
    - Forecasting horizon bounds (1 to 72 hours)
    - Model availability in artifact storage

    Returns structured timestamped forecasts with confidence bounds and simulation disclaimer.
    """
    dept_code = request.department_code.upper()

    # Validate department existence
    dept = db.query(Department).filter(Department.code == dept_code).first()
    if not dept and dept_code not in DEPT_CODES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department '{request.department_code}' not found. Supported: {DEPT_CODES}",
        )

    # Check model artifact presence
    model_path = MODELS_DIR / "demand_forecast_model.joblib"
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Demand forecasting model artifact is not available. "
                "Please run `python ml/demand_forecast.py` to train and serialize the model."
            ),
        )

    try:
        forecast_result = predict_future_demand(
            department_code=dept_code,
            horizon_hours=request.horizon_hours,
            start_time=request.start_time,
            models_dir=MODELS_DIR,
        )
        return forecast_result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate demand forecast: {str(exc)}",
        )


@router.post(
    "/waiting-time",
    response_model=WaitingTimePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict estimated patient waiting time in minutes",
)
def predict_patient_waiting_time(
    request: WaitingTimePredictionRequest,
    db: Session = Depends(get_db),
):
    """
    Predict estimated patient waiting time in minutes from operational conditions at arrival.

    Validates:
    - Department code existence
    - Acuity level (1 to 5)
    - Non-negative queue length and available staff >= 1
    - Model pipeline availability in artifact storage

    Returns estimated waiting time, confidence bounds, and operational disclaimer.
    """
    dept_code = request.department_code.upper()

    # Validate department existence in database or known configuration
    dept = db.query(Department).filter(Department.code == dept_code).first()
    if not dept and dept_code not in DEPT_CODES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department '{request.department_code}' not found. Supported: {DEPT_CODES}",
        )

    # Check model artifact presence
    model_path = MODELS_DIR / "waiting_time_pipeline.joblib"
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Waiting-time prediction model artifact is not available. "
                "Please run `python ml/waiting_time.py` to train and serialize the model."
            ),
        )

    try:
        prediction_result = predict_waiting_time(
            department_code=dept_code,
            acuity_level=request.acuity_level,
            queue_length=request.queue_length,
            staff_available=request.staff_available,
            patient_age_group=request.patient_age_group,
            arrival_time=request.arrival_time,
            models_dir=MODELS_DIR,
        )
        return prediction_result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate waiting-time prediction: {str(exc)}",
        )

