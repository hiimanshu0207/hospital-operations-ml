"""
FastAPI application entry point.

Provides the /health endpoint and CORS middleware.
Router modules will be included here as features are added.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API for Hospital Operations & Workflow Optimization. "
        "Provides endpoints for patient-demand analysis, waiting-time "
        "prediction, bed-occupancy monitoring, and resource allocation."
    ),
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
