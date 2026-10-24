"""
Pydantic schemas for Department entity.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    """Shared department properties."""
    code: str = Field(..., min_length=2, max_length=20, description="Department code (e.g., ED, ICU)")
    name: str = Field(..., min_length=2, max_length=100, description="Full department name")
    total_beds: int = Field(default=0, ge=0, description="Total bed capacity")
    target_nurse_to_patient_ratio: float = Field(default=0.25, gt=0, le=2.0, description="Target ratio of nurses to patients")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating department fields."""
    name: str | None = Field(default=None, min_length=2, max_length=100)
    total_beds: int | None = Field(default=None, ge=0)
    target_nurse_to_patient_ratio: float | None = Field(default=None, gt=0, le=2.0)


class DepartmentResponse(DepartmentBase):
    """Schema for department API responses."""
    id: int
    created_at: datetime
    occupied_beds: int = 0
    occupancy_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)
