# ═══════════════════════════════════════════════════════════════
# RailMind AI — Seed Maintenance Tasks
# Loads TMS + SMMS + TDMS defects from JSON files into database
# Creates 47+ unified maintenance tasks
# ═══════════════════════════════════════════════════════════════

import json
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.maintenance_task import MaintenanceTask


SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sample_data"
)

DATA_FILES = [
    ("tms_defects.json", "TMS"),
    ("sms_signals.json", "SMMS"),
    ("tdms_ohe.json", "TDMS"),
]


def seed_maintenance_tasks(db: Session) -> list[MaintenanceTask]:
    """
    Load maintenance tasks from all 3 source system JSON files.
    Maps section_code to section_id from the database.
    Automatically sets is_overdue based on due_date vs today.
    """
    # Build section_code → id mapping
    sections = db.query(RailwaySection).all()
    section_map = {s.section_code: s.id for s in sections}

    if not section_map:
        print("❌ No sections found! Run seed_corridor.py first.")
        return []

    # Check if tasks already exist
    existing_count = db.query(MaintenanceTask).count()
    if existing_count > 0:
        print(f"⏭️  {existing_count} tasks already exist. Skipping seed.")
        return db.query(MaintenanceTask).all()

    created = []
    today = date.today()

    for filename, source_system in DATA_FILES:
        filepath = os.path.join(SAMPLE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filename}, skipping")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            tasks_data = json.load(f)

        print(f"\n📄 Loading {filename} ({source_system}):")

        for t in tasks_data:
            section_code = t["section_code"]
            section_id = section_map.get(section_code)

            if section_id is None:
                print(f"  ⚠️  Section {section_code} not found, skipping task {t['task_code']}")
                continue

            due_date = datetime.strptime(t["due_date"], "%Y-%m-%d").date()
            detected_date = datetime.strptime(t["detected_date"], "%Y-%m-%d").date()

            task = MaintenanceTask(
                task_code=t["task_code"],
                source_system=source_system,
                department=t["department"],
                section_id=section_id,
                km_from=t["km_from"],
                km_to=t["km_to"],
                task_type=t["task_type"],
                severity=t["severity"],
                detected_date=detected_date,
                due_date=due_date,
                estimated_hours=t["estimated_hours"],
                block_type_required=t["block_type_required"],
                line_affected=t.get("line_affected"),
                speed_restriction=t.get("speed_restriction"),
                is_overdue=(due_date < today),
                status="PENDING",
            )
            db.add(task)
            created.append(task)

            severity_icon = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }.get(t["severity"], "⚪")

            print(f"  {severity_icon} {t['task_code']}: {t['task_type']} ({t['severity']})")

    db.commit()

    # Summary stats
    by_dept = {}
    by_severity = {}
    for task in created:
        by_dept[task.department] = by_dept.get(task.department, 0) + 1
        by_severity[task.severity] = by_severity.get(task.severity, 0) + 1

    print(f"\n📊 Total tasks: {len(created)}")
    print(f"   By Department: {by_dept}")
    print(f"   By Severity: {by_severity}")
    overdue = sum(1 for t in created if t.is_overdue)
    print(f"   Overdue: {overdue}")

    return created


def run():
    """Standalone execution."""
    print("🔧 Seeding Maintenance Tasks...\n")
    create_all_tables()
    db = SessionLocal()
    try:
        tasks = seed_maintenance_tasks(db)
        print(f"\n✅ Done! {len(tasks)} maintenance tasks loaded.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
