"""
FastAPI application routers.
"""

from app.routers.departments import router as departments_router
from app.routers.beds import router as beds_router
from app.routers.patient_visits import router as visits_router
from app.routers.admin import router as admin_router

__all__ = [
    "departments_router",
    "beds_router",
    "visits_router",
    "admin_router",
]
