"""
Application configuration using pydantic-settings.

Reads from environment variables and .env file.
Designed for easy migration from SQLite to PostgreSQL.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Hospital Operations & Workflow Optimization"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database — default is SQLite for development.
    # Switch to a PostgreSQL URL for production, e.g.:
    #   DATABASE_URL=postgresql://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite:///./hospital_ops.db"

    # CORS — allowed origins for the frontend dev server
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
