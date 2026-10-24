"""
FastAPI router for Machine Learning predictions and demand forecasting.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.schemas.prediction import DemandForecastRequest, DemandForecastResponse
from ml.demand_forecast import predict_future_demand, DEPT_CODES

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
