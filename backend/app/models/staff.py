"""
Staff ORM model.

Represents healthcare workers and their operational department assignments.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Staff(Base):
    """Staff member and department assignment."""

    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String(30), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    shift = Column(String(20), default="Morning", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    department = relationship("Department", back_populates="staff")

    def __repr__(self) -> str:
        return f"<Staff(staff_id='{self.staff_id}', role='{self.role}', department_id={self.department_id})>"
