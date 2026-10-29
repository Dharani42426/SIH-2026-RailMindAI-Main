# ═══════════════════════════════════════════════════════════════
# RailMind AI — Seed Train Timetable
# Loads COA timetable data from coa_timetable.json into database
# ═══════════════════════════════════════════════════════════════

import json
import os
import sys
from datetime import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.train_schedule import TrainSchedule


DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sample_data", "coa_timetable.json"
)


def parse_time(time_str: str) -> time:
    """Parse time string (HH:MM) to time object."""
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def seed_timetable(db: Session) -> list[TrainSchedule]:
    """
    Load train schedules from coa_timetable.json into the database.
    Maps section_code to section_id.
    """
    # Build section_code → id mapping
    sections = db.query(RailwaySection).all()
    section_map = {s.section_code: s.id for s in sections}

    if not section_map:
        print("❌ No sections found! Run seed_corridor.py first.")
        return []

    # Check if schedules already exist
    existing_count = db.query(TrainSchedule).count()
    if existing_count > 0:
        print(f"⏭️  {existing_count} schedules already exist. Skipping seed.")
        return db.query(TrainSchedule).all()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        trains_data = json.load(f)

    created = []
    seen_trains = set()

    for t in trains_data:
        section_code = t["section_code"]
        section_id = section_map.get(section_code)

        if section_id is None:
            print(f"  ⚠️  Section {section_code} not found, skipping train {t['train_no']}")
            continue

        schedule = TrainSchedule(
            train_no=t["train_no"],
            train_name=t["train_name"],
            train_type=t.get("train_type", "EXPRESS"),
            priority=t["priority"],
            section_id=section_id,
            direction=t["direction"],
            entry_km=t["entry_km"],
            exit_km=t["exit_km"],
            entry_time=parse_time(t["entry_time"]),
            exit_time=parse_time(t["exit_time"]),
            days_of_run=t.get("days_of_run", "DAILY"),
            is_special=t.get("is_special", False),
            avg_delay_min=t.get("avg_delay_min", 0),
        )
        db.add(schedule)
        created.append(schedule)

        # Track unique train names for summary
        train_key = f"{t['train_no']}-{t['train_name']}"
        if train_key not in seen_trains:
            priority_icon = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "⚪"}.get(t["priority"], "⚪")
            print(f"  {priority_icon} {t['train_no']} {t['train_name']} (P{t['priority']}, {t.get('train_type', 'EXPRESS')})")
            seen_trains.add(train_key)

    db.commit()

    # Summary stats
    by_priority = {}
    by_type = {}
    for s in created:
        by_priority[s.priority] = by_priority.get(s.priority, 0) + 1
        by_type[s.train_type] = by_type.get(s.train_type, 0) + 1

    print(f"\n📊 Total schedule entries: {len(created)}")
    print(f"   Unique trains: {len(seen_trains)}")
    print(f"   By Priority: {by_priority}")
    print(f"   By Type: {by_type}")

    return created


def run():
    """Standalone execution."""
    print("🚆 Seeding Train Timetable...\n")
    create_all_tables()
    db = SessionLocal()
    try:
        schedules = seed_timetable(db)
        print(f"\n✅ Done! {len(schedules)} schedule entries loaded.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
