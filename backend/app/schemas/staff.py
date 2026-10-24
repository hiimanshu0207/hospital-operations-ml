"""
Pydantic schemas for Staff entity.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class StaffBase(BaseModel):
    """Shared staff properties."""
    staff_id: str = Field(..., min_length=3, max_length=30, description="Unique staff code (e.g. STF-ED-001)")
    role: str = Field(..., min_length=2, max_length=50, description="Healthcare role (Doctor, Nurse, etc.)")
    department_id: int = Field(..., gt=0, description="Assigned department ID")
    shift: str = Field(default="Morning", max_length=20, description="Operational shift")
    is_active: bool = Field(default=True, description="Active employment status")


class StaffCreate(StaffBase):
    """Schema for adding new staff."""
    pass


class StaffResponse(StaffBase):
    """Schema for staff API response."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
