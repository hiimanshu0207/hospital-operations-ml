"""
PatientVisit ORM model.

Represents synthetic patient operational encounters with arrival, waiting time,
queue status, service milestones, and bed allocations.
Non-identifying academic operational record only.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class PatientVisit(Base):
    """Synthetic operational patient encounter."""

    __tablename__ = "patient_visits"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(40), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    patient_age_group = Column(String(20), nullable=False)
    acuity_level = Column(Integer, nullable=False)  # 1 (Resuscitation) to 5 (Non-urgent)
    arrival_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    queue_length_at_arrival = Column(Integer, default=0, nullable=False)
    staff_available_at_arrival = Column(Integer, default=1, nullable=False)
    service_start_timestamp = Column(DateTime(timezone=True), nullable=False)
    service_end_timestamp = Column(DateTime(timezone=True), nullable=False)
    waiting_time_minutes = Column(Float, nullable=False)
    length_of_stay_minutes = Column(Float, nullable=False)
    total_duration_minutes = Column(Float, nullable=False)
    admission_required = Column(Boolean, default=False, nullable=False)
    bed_id = Column(Integer, ForeignKey("beds.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), default="Completed", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("waiting_time_minutes >= 0", name="chk_positive_waiting_time"),
        CheckConstraint("length_of_stay_minutes >= 0", name="chk_positive_length_of_stay"),
        CheckConstraint("total_duration_minutes >= 0", name="chk_positive_total_duration"),
        CheckConstraint("acuity_level >= 1 AND acuity_level <= 5", name="chk_acuity_range"),
        CheckConstraint("queue_length_at_arrival >= 0", name="chk_non_negative_queue"),
        CheckConstraint("staff_available_at_arrival >= 0", name="chk_non_negative_staff"),
    )

    # Relationships
    department = relationship("Department", back_populates="patient_visits")
    bed = relationship("Bed", back_populates="patient_visits")

    def __repr__(self) -> str:
        return (
            f"<PatientVisit(visit_id='{self.visit_id}', dept_id={self.department_id}, "
            f"wait_time={self.waiting_time_minutes}m, los={self.length_of_stay_minutes}m)>"
        )
