"""
Department ORM model.

Represents hospital operational departments (e.g., Emergency, ICU, General Ward).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    """Hospital department entity."""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    total_beds = Column(Integer, default=0, nullable=False)
    target_nurse_to_patient_ratio = Column(Float, default=0.25, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    staff = relationship("Staff", back_populates="department", cascade="all, delete-orphan")
    beds = relationship("Bed", back_populates="department", cascade="all, delete-orphan")
    patient_visits = relationship("PatientVisit", back_populates="department", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Department(code='{self.code}', name='{self.name}', total_beds={self.total_beds})>"
