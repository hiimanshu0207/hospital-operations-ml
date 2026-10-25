"""
Pydantic schemas for Bed entity.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BedBase(BaseModel):
    """Shared bed properties."""
    bed_number: str = Field(..., min_length=2, max_length=30, description="Unique bed identifier")
    department_id: int = Field(..., gt=0, description="Department ID where bed is located")
    bed_type: str = Field(default="Standard", max_length=50, description="Type of bed")
    is_occupied: bool = Field(default=False, description="Whether the bed is currently occupied")


class BedCreate(BedBase):
    """Schema for registering a new bed."""
    pass


class BedOccupancyUpdate(BaseModel):
    """Schema for updating bed occupancy status."""
    is_occupied: bool = Field(..., description="Target occupancy status")


class BedResponse(BedBase):
    """Schema for bed API responses."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BedSummaryResponse(BaseModel):
    """Aggregated bed inventory and occupancy telemetry."""
    total_beds: int
    occupied_beds: int
    available_beds: int
    overall_occupancy_rate: float

