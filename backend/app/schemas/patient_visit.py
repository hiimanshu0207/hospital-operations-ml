"""
Pydantic schemas for PatientVisit entity with comprehensive validation.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientVisitBase(BaseModel):
    """Shared patient visit properties with operational constraints."""
    visit_id: str = Field(..., min_length=5, max_length=40, description="Synthetic encounter ID")
    department_id: int = Field(..., gt=0, description="Department ID")
    patient_age_group: str = Field(..., description="Age category (e.g., 18-35)")
    acuity_level: int = Field(..., ge=1, le=5, description="Triage acuity level 1 (most severe) to 5 (least severe)")
    arrival_timestamp: datetime = Field(..., description="Arrival timestamp")
    queue_length_at_arrival: int = Field(default=0, ge=0, description="Queue length at patient arrival")
    staff_available_at_arrival: int = Field(default=1, ge=1, description="Staff on duty at arrival")
    service_start_timestamp: datetime = Field(..., description="Timestamp when clinical service commenced")
    service_end_timestamp: datetime = Field(..., description="Timestamp when service completed / discharged")
    waiting_time_minutes: float = Field(..., ge=0, description="Waiting duration in minutes")
    length_of_stay_minutes: float = Field(..., ge=0, description="Length of stay in minutes")
    total_duration_minutes: float = Field(..., ge=0, description="Total duration (wait + LOS) in minutes")
    admission_required: bool = Field(default=False, description="Whether inpatient bed admission was needed")
    bed_id: int | None = Field(default=None, description="Assigned physical bed ID if admitted")
    status: str = Field(default="Completed", max_length=30, description="Visit status")

    @model_validator(mode="after")
    def validate_timestamps_and_durations(self) -> Any:
        """Validate sequential timestamps and duration consistency."""
        if self.service_start_timestamp < self.arrival_timestamp:
            raise ValueError("service_start_timestamp cannot be earlier than arrival_timestamp")

        if self.service_end_timestamp < self.service_start_timestamp:
            raise ValueError("service_end_timestamp cannot be earlier than service_start_timestamp")

        if self.waiting_time_minutes < 0:
            raise ValueError("waiting_time_minutes must be non-negative")

        if self.length_of_stay_minutes < 0:
            raise ValueError("length_of_stay_minutes must be non-negative")

        if self.total_duration_minutes < 0:
            raise ValueError("total_duration_minutes must be non-negative")

        return self


class PatientVisitCreate(PatientVisitBase):
    """Schema for registering a patient visit."""
    pass


class PatientVisitUpdate(BaseModel):
    """Schema for updating patient visit fields."""
    status: str | None = None
    admission_required: bool | None = None
    bed_id: int | None = None


class PatientVisitResponse(PatientVisitBase):
    """Schema for patient visit API responses."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientVisitSummary(BaseModel):
    """High-level operational summary statistics for patient visits."""
    total_visits: int
    avg_waiting_time_minutes: float
    avg_length_of_stay_minutes: float
    total_admissions: int
    acuity_breakdown: dict[int, int]
    department_breakdown: dict[str, int]
