# ═══════════════════════════════════════════════════════════════
# RailMind AI — Seed Corridors/Sections
# Loads railway section data from sections.json into the database
# ═══════════════════════════════════════════════════════════════

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection


DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sample_data", "sections.json"
)


def seed_sections(db: Session) -> list[RailwaySection]:
    """
    Load railway sections from sections.json into the database.
    Returns list of created RailwaySection objects.
    Skips sections that already exist (by section_code).
    """
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        sections_data = json.load(f)

    created = []
    for s in sections_data:
        # Check if section already exists
        existing = db.query(RailwaySection).filter_by(
            section_code=s["section_code"]
        ).first()

        if existing:
            print(f"  ⏭️  Section {s['section_code']} already exists, skipping")
            created.append(existing)
            continue

        section = RailwaySection(
            section_code=s["section_code"],
            section_name=s["section_name"],
            division=s["division"],
            zone=s["zone"],
            km_start=s["km_start"],
            km_end=s["km_end"],
            track_type=s.get("track_type", "DBL"),
            traction=s.get("traction", "AC25KV"),
            max_speed_kmph=s.get("max_speed_kmph", 110),
            trains_per_day=s.get("trains_per_day", 100),
            is_ghat_section=s.get("is_ghat_section", False),
            description=s.get("description"),
        )
        db.add(section)
        created.append(section)
        print(f"  ✅ Created section: {s['section_code']} — {s['section_name']}")

    db.commit()
    print(f"\n📊 Total sections: {len(created)}")
    return created


def run():
    """Standalone execution — create tables and seed sections."""
    print("🚂 Seeding Railway Sections...\n")
    create_all_tables()
    db = SessionLocal()
    try:
        sections = seed_sections(db)
        print(f"\n✅ Done! {len(sections)} sections loaded.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
