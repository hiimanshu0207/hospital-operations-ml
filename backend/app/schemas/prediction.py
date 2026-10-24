"""
Pydantic schemas for Machine Learning prediction and forecasting endpoints.
"""

from datetime import datetime
from typing import Any
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


class WaitingTimePredictionRequest(BaseModel):
    """Request payload for estimated patient waiting-time prediction."""
    department_code: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Hospital department code (e.g., ED, ICU, GEN, SURG, PED)",
        examples=["ED"],
    )
    acuity_level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Emergency Severity Index / Triage Acuity (1: Resuscitation to 5: Non-urgent)",
        examples=[3],
    )
    queue_length: int = Field(
        default=0,
        ge=0,
        description="Number of patients currently queued/waiting in the department at arrival",
        examples=[3],
    )
    staff_available: int = Field(
        default=4,
        ge=1,
        description="Active staff members available in the department at arrival",
        examples=[4],
    )
    patient_age_group: str = Field(
        default="36-50",
        description="Patient age demographic category (0-17, 18-35, 36-50, 51-65, 65+)",
        examples=["36-50"],
    )
    arrival_time: datetime | None = Field(
        default=None,
        description="Patient arrival timestamp (defaults to current UTC time)",
    )


class WaitingTimePredictionResponse(BaseModel):
    """Response payload for patient waiting-time prediction."""
    department_code: str
    department_name: str
    acuity_level: int
    estimated_waiting_time_minutes: float
    confidence_lower: float
    confidence_upper: float
    model_name: str
    model_version: str
    prediction_generated_at: str
    operational_context: dict[str, Any]
    disclaimer: str

