"""
Pydantic schemas for data validation and API serialization.
"""

from app.schemas.department import (
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)
from app.schemas.staff import (
    StaffBase,
    StaffCreate,
    StaffResponse,
)
from app.schemas.bed import (
    BedBase,
    BedCreate,
    BedOccupancyUpdate,
    BedResponse,
)
from app.schemas.patient_visit import (
    PatientVisitBase,
    PatientVisitCreate,
    PatientVisitUpdate,
    PatientVisitResponse,
    PatientVisitSummary,
)
from app.schemas.prediction import (
    DemandForecastRequest,
    HourlyForecast,
    DemandForecastResponse,
)

__all__ = [
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "StaffBase",
    "StaffCreate",
    "StaffResponse",
    "BedBase",
    "BedCreate",
    "BedOccupancyUpdate",
    "BedResponse",
    "PatientVisitBase",
    "PatientVisitCreate",
    "PatientVisitUpdate",
    "PatientVisitResponse",
    "PatientVisitSummary",
    "DemandForecastRequest",
    "HourlyForecast",
    "DemandForecastResponse",
]
