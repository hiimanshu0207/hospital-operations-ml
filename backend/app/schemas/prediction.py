"""
Pydantic schemas for Machine Learning prediction and forecasting endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class DemandForecastRequest(BaseModel):
    """Request payload for hourly patient demand forecasting."""
    department_code: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Department code to forecast (e.g., ED, ICU, GEN, SURG, PED)",
        examples=["ED"],
    )
    horizon_hours: int = Field(
        default=24,
        ge=1,
        le=72,
        description="Forecasting window in hours ahead (1 to 72 hours)",
        examples=[24],
    )
    start_time: datetime | None = Field(
        default=None,
        description="Starting timestamp for forecast (defaults to current UTC time)",
    )


class HourlyForecast(BaseModel):
    """Forecast for an individual hour."""
    timestamp: str
    hour: int
    predicted_arrivals: float
    confidence_lower: float
    confidence_upper: float


class DemandForecastResponse(BaseModel):
    """Response payload for patient demand forecast."""
    department_code: str
    department_name: str
    horizon_hours: int
    model_name: str
    model_version: str
    forecast_generated_at: str
    total_predicted_arrivals: float
    hourly_forecasts: list[HourlyForecast]
    disclaimer: str
