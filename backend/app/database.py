"""
Database engine and session configuration.

Uses SQLAlchemy with SQLite for development.
To migrate to PostgreSQL, change DATABASE_URL in .env — no code changes needed.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# SQLite requires connect_args for thread safety
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that provides a database session.

    Yields a session and ensures it is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_override=None) -> None:
    """
    Create all tables in the database if they do not already exist.

    Imports all models to register them on Base.metadata.
    """
    import app.models  # noqa: F401
    target_engine = engine_override or engine
    Base.metadata.create_all(bind=target_engine)
