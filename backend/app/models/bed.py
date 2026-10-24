"""
Bed ORM model.

Represents physical hospital beds, assigned departments, and occupancy states.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Bed(Base):
    """Physical hospital bed and occupancy tracking."""

    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    bed_number = Column(String(30), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    bed_type = Column(String(50), default="Standard", nullable=False)
    is_occupied = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = relationship("Department", back_populates="beds")
    patient_visits = relationship("PatientVisit", back_populates="bed")

    def __repr__(self) -> str:
        return f"<Bed(bed_number='{self.bed_number}', department_id={self.department_id}, occupied={self.is_occupied})>"
