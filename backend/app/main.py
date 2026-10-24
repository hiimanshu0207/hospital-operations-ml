"""
FastAPI application entry point.

Provides the /health endpoint, CORS middleware, database lifespan initialization,
and operational domain routers under /api/v1.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers.departments import router as departments_router
from app.routers.beds import router as beds_router
from app.routers.patient_visits import router as visits_router
from app.routers.admin import router as admin_router
from app.routers.predictions import router as predictions_router
from app.routers.optimization import router as optimization_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Initializes database tables on application startup.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API for Hospital Operations & Workflow Optimization. "
        "Provides endpoints for patient-demand analysis, waiting-time "
        "prediction, bed-occupancy monitoring, and resource allocation."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the React dev server to call this API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include API Routers under /api/v1
# ---------------------------------------------------------------------------
app.include_router(departments_router, prefix="/api/v1")
app.include_router(beds_router, prefix="/api/v1")
app.include_router(visits_router, prefix="/api/v1/visits")
app.include_router(visits_router, prefix="/api/v1/patient-visits")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(optimization_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """
    Returns the application's health status.

    Used by the frontend, monitoring tools, and deployment pipelines
    to verify the API is running.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
