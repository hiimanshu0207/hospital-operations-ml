"""
Synthetic hospital operations dataset generator and validator.

Generates realistic, non-identifying operational records:
- Department metadata and bed capacities
- Staff members and shifts
- Physical beds and occupancy
- Patient arrival events, queues, staff availability, service milestones,
  derived waiting times, and lengths of stay.

Validation enforces:
- No negative durations
- Valid timestamps (arrival <= service_start <= service_end)
- Unique synthetic visit IDs
- Bed occupancy never exceeding department capacity
- Valid acuity levels (1-5) and non-negative queues/staff counts.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.staff import Staff
from app.models.bed import Bed
from app.models.patient_visit import PatientVisit


# Standard department operational profiles
DEFAULT_DEPARTMENTS = [
    {"code": "ED", "name": "Emergency Department", "total_beds": 25, "ratio": 0.35},
    {"code": "ICU", "name": "Intensive Care Unit", "total_beds": 12, "ratio": 0.50},
    {"code": "GEN", "name": "General Medicine Ward", "total_beds": 50, "ratio": 0.20},
    {"code": "SURG", "name": "Surgical Care Unit", "total_beds": 20, "ratio": 0.25},
    {"code": "PED", "name": "Pediatric Ward", "total_beds": 15, "ratio": 0.30},
]

AGE_GROUPS = ["0-17", "18-35", "36-50", "51-65", "65+"]
STAFF_ROLES = ["Doctor", "Registered Nurse", "Triage Nurse", "Specialist", "Admin"]
SHIFTS = ["Morning", "Evening", "Night"]


class SyntheticHospitalDataGenerator:
    """Generates synthetic operational data with strict integrity guarantees."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_departments(self) -> pd.DataFrame:
        """Generate hospital department configuration."""
        rows = []
        for i, dept in enumerate(DEFAULT_DEPARTMENTS, start=1):
            rows.append({
                "id": i,
                "code": dept["code"],
                "name": dept["name"],
                "total_beds": dept["total_beds"],
                "target_nurse_to_patient_ratio": dept["ratio"],
                "created_at": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            })
        return pd.DataFrame(rows)

    def generate_staff(self, departments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate staff members distributed across departments and shifts."""
        rows = []
        staff_counter = 1

        for _, dept in departments_df.iterrows():
            dept_code = dept["code"]
            dept_id = int(dept["id"])
            # Allocate staff proportional to bed count and acuity
            num_staff = max(4, int(dept["total_beds"] * dept["target_nurse_to_patient_ratio"] * 2.5))

            for j in range(num_staff):
                role = "Doctor" if j % 5 == 0 else ("Triage Nurse" if j % 4 == 0 and dept_code == "ED" else "Registered Nurse")
                shift = SHIFTS[j % len(SHIFTS)]
                rows.append({
                    "id": staff_counter,
                    "staff_id": f"STF-{dept_code}-{staff_counter:03d}",
                    "role": role,
                    "department_id": dept_id,
                    "shift": shift,
                    "is_active": True,
                    "created_at": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                })
                staff_counter += 1

        return pd.DataFrame(rows)

    def generate_beds(self, departments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate physical bed inventory for each department."""
        rows = []
        bed_counter = 1

        for _, dept in departments_df.iterrows():
            dept_code = dept["code"]
            dept_id = int(dept["id"])
            total_beds = int(dept["total_beds"])

            bed_type = "ICU" if dept_code == "ICU" else ("Emergency" if dept_code == "ED" else ("Pediatric" if dept_code == "PED" else "Standard"))

            for b in range(1, total_beds + 1):
                rows.append({
                    "id": bed_counter,
                    "bed_number": f"{dept_code}-B{b:02d}",
                    "department_id": dept_id,
                    "bed_type": bed_type,
                    "is_occupied": False,
                    "created_at": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                })
                bed_counter += 1

        return pd.DataFrame(rows)

    def generate_patient_visits(
        self,
        departments_df: pd.DataFrame,
        beds_df: pd.DataFrame,
        num_visits: int = 600,
        start_date: str = "2026-01-01",
        days: int = 14,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate operational patient visits with realistic queueing and bed occupancy.

        Returns:
            Tuple of (visits_df, updated_beds_df)
        """
        base_time = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        total_seconds = days * 24 * 3600

        # Non-homogeneous arrival weights by hour of day (higher between 9am - 8pm)
        hour_weights = np.array([
            0.02, 0.01, 0.01, 0.01, 0.02, 0.03,  # 00:00 - 05:00
            0.04, 0.06, 0.07, 0.08, 0.08, 0.08,  # 06:00 - 11:00
            0.07, 0.07, 0.06, 0.06, 0.07, 0.08,  # 12:00 - 17:00
            0.06, 0.05, 0.04, 0.03, 0.03, 0.02   # 18:00 - 23:00
        ])
        hour_weights = hour_weights / hour_weights.sum()

        dept_ids = departments_df["id"].tolist()
        dept_weights = [0.45, 0.08, 0.24, 0.13, 0.10]  # ED receives highest volume

        # Department bed lookup
        dept_beds_map = {}
        for d_id in dept_ids:
            dept_beds_map[d_id] = beds_df[beds_df["department_id"] == d_id]["id"].tolist()

        # Generate timestamps
        # Step 1: Draw random days and hours based on hourly distribution
        arrival_days = self.rng.integers(0, days, size=num_visits)
        arrival_hours = self.rng.choice(24, size=num_visits, p=hour_weights)
        arrival_minutes = self.rng.integers(0, 60, size=num_visits)
        arrival_seconds = self.rng.integers(0, 60, size=num_visits)

        arrivals = []
        for d, h, m, s in zip(arrival_days, arrival_hours, arrival_minutes, arrival_seconds):
            arr_dt = base_time + timedelta(days=int(d), hours=int(h), minutes=int(m), seconds=int(s))
            arrivals.append(arr_dt)

        arrivals.sort()  # Chronological arrival sequence

        # Track active bed occupancy over simulated time: dept_id -> list of (end_time, bed_id)
        active_bed_occupancy: dict[int, list[tuple[datetime, int]]] = {d: [] for d in dept_ids}

        # Track beds currently occupied at end of simulation for beds_df
        final_occupied_bed_ids = set()

        visits = []
        for idx in range(num_visits):
            visit_id = f"VIS-2026-{idx + 1:05d}"
            arr_time = arrivals[idx]

            # Department selection
            dept_id = int(self.rng.choice(dept_ids, p=dept_weights))
            dept_row = departments_df[departments_df["id"] == dept_id].iloc[0]
            dept_capacity = int(dept_row["total_beds"])

            # Clean expired bed occupancies up to current arrival time
            active_bed_occupancy[dept_id] = [
                (end_t, b_id) for (end_t, b_id) in active_bed_occupancy[dept_id] if end_t > arr_time
            ]
            current_occupied_count = len(active_bed_occupancy[dept_id])

            # Patient age group & Acuity Level (ESI 1-5)
            age_group = self.rng.choice(AGE_GROUPS, p=[0.12, 0.28, 0.25, 0.20, 0.15])
            acuity = int(self.rng.choice([1, 2, 3, 4, 5], p=[0.04, 0.16, 0.42, 0.26, 0.12]))

            # Available staff and queue simulation at arrival
            hour = arr_time.hour
            base_staff = 6 if 7 <= hour <= 19 else 3
            staff_available = max(1, int(self.rng.poisson(base_staff)))
            queue_length = max(0, int(self.rng.poisson(lam=max(0.5, 4.0 - acuity + (hour in range(10, 20)) * 2))))

            # Calculate waiting time (minutes)
            # High acuity (1-2) waits very little; lower acuity waits proportionally to queue / staff
            if acuity == 1:
                wait_minutes = round(float(self.rng.uniform(0.5, 4.0)), 1)
            elif acuity == 2:
                wait_minutes = round(float(self.rng.uniform(4.0, 18.0) + (queue_length / max(1, staff_available)) * 2.0), 1)
            elif acuity == 3:
                wait_minutes = round(float(self.rng.uniform(15.0, 45.0) + (queue_length / max(1, staff_available)) * 5.0), 1)
            elif acuity == 4:
                wait_minutes = round(float(self.rng.uniform(30.0, 80.0) + (queue_length / max(1, staff_available)) * 7.0), 1)
            else:  # acuity 5
                wait_minutes = round(float(self.rng.uniform(45.0, 120.0) + (queue_length / max(1, staff_available)) * 8.0), 1)

            # Enforce non-negative wait time
            wait_minutes = max(0.0, wait_minutes)
            service_start = arr_time + timedelta(minutes=wait_minutes)

            # Length of stay (minutes)
            if dept_row["code"] == "ICU":
                los_minutes = round(float(self.rng.uniform(720.0, 2880.0)), 1)  # 12 to 48 hours
                admission_required = True
            elif dept_row["code"] == "SURG":
                los_minutes = round(float(self.rng.uniform(180.0, 1440.0)), 1)  # 3 to 24 hours
                admission_required = self.rng.random() < 0.85
            elif dept_row["code"] == "GEN":
                los_minutes = round(float(self.rng.uniform(240.0, 1800.0)), 1)  # 4 to 30 hours
                admission_required = self.rng.random() < 0.70
            elif dept_row["code"] == "PED":
                los_minutes = round(float(self.rng.uniform(60.0, 480.0)), 1)   # 1 to 8 hours
                admission_required = self.rng.random() < 0.25
            else:  # ED
                los_minutes = round(float(self.rng.uniform(35.0, 360.0)), 1)   # 35m to 6h
                admission_required = (acuity <= 2) and (self.rng.random() < 0.50)

            # Enforce non-negative LOS
            los_minutes = max(5.0, los_minutes)
            service_end = service_start + timedelta(minutes=los_minutes)
            total_duration = round((service_end - arr_time).total_seconds() / 60.0, 1)

            # Bed Assignment strictly respecting capacity
            assigned_bed_id = None
            if admission_required:
                used_bed_ids = {b_id for (_, b_id) in active_bed_occupancy[dept_id]}
                available_beds = [b for b in dept_beds_map[dept_id] if b not in used_bed_ids]

                # STRICT CONSTRAINT: Occupied beds NEVER exceed total capacity
                if available_beds and (len(used_bed_ids) < dept_capacity):
                    assigned_bed_id = available_beds[0]
                    active_bed_occupancy[dept_id].append((service_end, assigned_bed_id))

            # Status determination
            sim_end_cutoff = base_time + timedelta(seconds=total_seconds)
            if service_end <= sim_end_cutoff:
                status = "Completed"
            elif service_start <= sim_end_cutoff:
                status = "In-Progress"
            else:
                status = "Waiting"

            visits.append({
                "id": idx + 1,
                "visit_id": visit_id,
                "department_id": dept_id,
                "patient_age_group": age_group,
                "acuity_level": acuity,
                "arrival_timestamp": arr_time,
                "queue_length_at_arrival": queue_length,
                "staff_available_at_arrival": staff_available,
                "service_start_timestamp": service_start,
                "service_end_timestamp": service_end,
                "waiting_time_minutes": wait_minutes,
                "length_of_stay_minutes": los_minutes,
                "total_duration_minutes": total_duration,
                "admission_required": admission_required,
                "bed_id": assigned_bed_id,
                "status": status,
                "created_at": base_time,
            })

        visits_df = pd.DataFrame(visits)

        # Update bed occupancy status for current simulation snapshot
        updated_beds = beds_df.copy()
        for dept_id, active_list in active_bed_occupancy.items():
            for _, b_id in active_list:
                final_occupied_bed_ids.add(b_id)

        updated_beds["is_occupied"] = updated_beds["id"].isin(final_occupied_bed_ids)

        return visits_df, updated_beds

    def generate_all(
        self,
        num_visits: int = 600,
        start_date: str = "2026-01-01",
        days: int = 14,
    ) -> dict[str, pd.DataFrame]:
        """Generate all four related datasets."""
        departments_df = self.generate_departments()
        staff_df = self.generate_staff(departments_df)
        beds_df = self.generate_beds(departments_df)
        visits_df, updated_beds_df = self.generate_patient_visits(
            departments_df=departments_df,
            beds_df=beds_df,
            num_visits=num_visits,
            start_date=start_date,
            days=days,
        )

        return {
            "departments": departments_df,
            "staff": staff_df,
            "beds": updated_beds_df,
            "patient_visits": visits_df,
        }


def validate_synthetic_data(
    visits_df: pd.DataFrame,
    departments_df: pd.DataFrame,
    beds_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Validate synthetic data against operational integrity rules.

    Raises:
        ValueError: If any validation rule is violated.

    Returns:
        Dictionary of validated metric summaries.
    """
    errors: list[str] = []

    # 1. Non-negative durations
    if (visits_df["waiting_time_minutes"] < 0).any():
        errors.append("Validation Error: Negative waiting times detected.")
    if (visits_df["length_of_stay_minutes"] < 0).any():
        errors.append("Validation Error: Negative length of stay detected.")
    if (visits_df["total_duration_minutes"] < 0).any():
        errors.append("Validation Error: Negative total duration detected.")

    # 2. Timestamp order: arrival <= service_start <= service_end
    invalid_start = visits_df["service_start_timestamp"] < visits_df["arrival_timestamp"]
    if invalid_start.any():
        count = invalid_start.sum()
        errors.append(f"Validation Error: {count} records have service_start earlier than arrival.")

    invalid_end = visits_df["service_end_timestamp"] < visits_df["service_start_timestamp"]
    if invalid_end.any():
        count = invalid_end.sum()
        errors.append(f"Validation Error: {count} records have service_end earlier than service_start.")

    # 3. Duplicate synthetic IDs
    if not visits_df["visit_id"].is_unique:
        duplicates = visits_df[visits_df["visit_id"].duplicated()]["visit_id"].tolist()
        errors.append(f"Validation Error: Duplicate synthetic visit IDs detected: {duplicates[:5]}.")

    # 4. Bed capacity constraints: occupied beds <= total beds per department
    dept_capacity = departments_df.set_index("id")["total_beds"].to_dict()
    occupied_beds_per_dept = beds_df[beds_df["is_occupied"]].groupby("department_id").size().to_dict()

    for dept_id, capacity in dept_capacity.items():
        occupied = occupied_beds_per_dept.get(dept_id, 0)
        if occupied > capacity:
            errors.append(
                f"Validation Error: Department ID {dept_id} has {occupied} occupied beds, "
                f"exceeding capacity of {capacity}."
            )

    # 5. Non-negative queues and staff counts
    if (visits_df["queue_length_at_arrival"] < 0).any():
        errors.append("Validation Error: Negative queue length detected.")
    if (visits_df["staff_available_at_arrival"] < 1).any():
        errors.append("Validation Error: Staff available at arrival must be at least 1.")

    # 6. Acuity level range (1 to 5)
    if not visits_df["acuity_level"].between(1, 5).all():
        errors.append("Validation Error: Acuity level out of valid range [1, 5].")

    if errors:
        raise ValueError("\n".join(errors))

    return {
        "status": "VALID",
        "total_visits": len(visits_df),
        "total_departments": len(departments_df),
        "total_beds": len(beds_df),
        "total_occupied_beds": int(beds_df["is_occupied"].sum()),
        "avg_waiting_time_minutes": round(float(visits_df["waiting_time_minutes"].mean()), 2),
        "avg_length_of_stay_minutes": round(float(visits_df["length_of_stay_minutes"].mean()), 2),
    }


def save_synthetic_datasets(
    output_dir: str | Path = "data",
    seed: int = 42,
    num_visits: int = 600,
) -> dict[str, Path]:
    """Generate and write datasets to CSV files in output_dir."""
    generator = SyntheticHospitalDataGenerator(seed=seed)
    datasets = generator.generate_all(num_visits=num_visits)

    # Validate before persisting
    validate_synthetic_data(
        visits_df=datasets["patient_visits"],
        departments_df=datasets["departments"],
        beds_df=datasets["beds"],
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    paths = {}
    for name, df in datasets.items():
        file_path = out_path / f"{name}.csv"
        df.to_csv(file_path, index=False)
        paths[name] = file_path

    return paths


def seed_database(db: Session, seed: int = 42, num_visits: int = 600) -> dict[str, int]:
    """
    Populate database with reproducible synthetic data.

    Clears existing records and inserts fresh valid operational entities.
    """
    generator = SyntheticHospitalDataGenerator(seed=seed)
    data = generator.generate_all(num_visits=num_visits)

    # Validate before inserting
    validate_synthetic_data(
        visits_df=data["patient_visits"],
        departments_df=data["departments"],
        beds_df=data["beds"],
    )

    # Clear existing data in reverse order of foreign keys
    db.query(PatientVisit).delete()
    db.query(Bed).delete()
    db.query(Staff).delete()
    db.query(Department).delete()
    db.commit()

    # 1. Insert Departments
    dept_objs = []
    for _, r in data["departments"].iterrows():
        dept_objs.append(Department(
            id=int(r["id"]),
            code=r["code"],
            name=r["name"],
            total_beds=int(r["total_beds"]),
            target_nurse_to_patient_ratio=float(r["target_nurse_to_patient_ratio"]),
            created_at=pd.to_datetime(r["created_at"]).to_pydatetime(),
        ))
    db.add_all(dept_objs)
    db.commit()

    # 2. Insert Staff
    staff_objs = []
    for _, r in data["staff"].iterrows():
        staff_objs.append(Staff(
            id=int(r["id"]),
            staff_id=r["staff_id"],
            role=r["role"],
            department_id=int(r["department_id"]),
            shift=r["shift"],
            is_active=bool(r["is_active"]),
            created_at=pd.to_datetime(r["created_at"]).to_pydatetime(),
        ))
    db.add_all(staff_objs)
    db.commit()

    # 3. Insert Beds
    bed_objs = []
    for _, r in data["beds"].iterrows():
        bed_objs.append(Bed(
            id=int(r["id"]),
            bed_number=r["bed_number"],
            department_id=int(r["department_id"]),
            bed_type=r["bed_type"],
            is_occupied=bool(r["is_occupied"]),
            created_at=pd.to_datetime(r["created_at"]).to_pydatetime(),
        ))
    db.add_all(bed_objs)
    db.commit()

    # 4. Insert Patient Visits
    visit_objs = []
    for _, r in data["patient_visits"].iterrows():
        b_id = int(r["bed_id"]) if pd.notna(r["bed_id"]) else None
        visit_objs.append(PatientVisit(
            id=int(r["id"]),
            visit_id=str(r["visit_id"]),
            department_id=int(r["department_id"]),
            patient_age_group=str(r["patient_age_group"]),
            acuity_level=int(r["acuity_level"]),
            arrival_timestamp=pd.to_datetime(r["arrival_timestamp"]).to_pydatetime(),
            queue_length_at_arrival=int(r["queue_length_at_arrival"]),
            staff_available_at_arrival=int(r["staff_available_at_arrival"]),
            service_start_timestamp=pd.to_datetime(r["service_start_timestamp"]).to_pydatetime(),
            service_end_timestamp=pd.to_datetime(r["service_end_timestamp"]).to_pydatetime(),
            waiting_time_minutes=float(r["waiting_time_minutes"]),
            length_of_stay_minutes=float(r["length_of_stay_minutes"]),
            total_duration_minutes=float(r["total_duration_minutes"]),
            admission_required=bool(r["admission_required"]),
            bed_id=b_id,
            status=str(r["status"]),
            created_at=pd.to_datetime(r["created_at"]).to_pydatetime(),
        ))
    db.add_all(visit_objs)
    db.commit()

    return {
        "departments_seeded": len(dept_objs),
        "staff_seeded": len(staff_objs),
        "beds_seeded": len(bed_objs),
        "visits_seeded": len(visit_objs),
    }
