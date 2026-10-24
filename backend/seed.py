"""
CLI script to initialize SQLite database and populate with synthetic operational data.

Also saves CSV copies into the /data directory for exploratory analysis.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app imports resolve cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import init_db, SessionLocal
from app.services.synthetic_generator import seed_database, save_synthetic_datasets


def main():
    print("=" * 60)
    print("Hospital Operations — Database Initialization & Seeding")
    print("=" * 60)

    print("\n1. Initializing database schema...")
    init_db()
    print("   ✓ SQLAlchemy tables verified/created.")

    print("\n2. Populating SQLite database with synthetic records...")
    db = SessionLocal()
    try:
        results = seed_database(db=db, seed=42, num_visits=600)
        print(f"   ✓ Departments seeded: {results['departments_seeded']}")
        print(f"   ✓ Staff seeded:       {results['staff_seeded']}")
        print(f"   ✓ Beds seeded:        {results['beds_seeded']}")
        print(f"   ✓ Visits seeded:      {results['visits_seeded']}")
    finally:
        db.close()

    print("\n3. Exporting validated CSV datasets to data/ directory...")
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    csv_paths = save_synthetic_datasets(output_dir=data_dir, seed=42, num_visits=600)
    for name, p in csv_paths.items():
        print(f"   ✓ Saved {name}.csv -> {p.name}")

    print("\n" + "=" * 60)
    print("Seeding complete! Database and data/ are ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
