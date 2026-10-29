# ═══════════════════════════════════════════════════════════════
# RailMind AI — Master Seed Script
# Runs all seed scripts in the correct order
# Usage: python data/seed_all.py
# ═══════════════════════════════════════════════════════════════

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, create_all_tables
from data.seed_corridor import seed_sections
from data.seed_assets import seed_assets
from data.seed_maintenance import seed_maintenance_tasks
from data.seed_timetable import seed_timetable
from data.seed_users import seed_users


def seed_all():
    """Run all seed scripts in dependency order."""
    print("=" * 60)
    print("🚂 RailMind AI — Database Seeder")
    print("=" * 60)

    # Step 0: Create all tables
    print("\n📋 Creating database tables...")
    create_all_tables()
    print("✅ Tables created!\n")

    db = SessionLocal()
    try:
        # Step 1: Sections (no dependencies)
        print("─" * 60)
        print("STEP 1: Railway Sections")
        print("─" * 60)
        sections = seed_sections(db)

        # Step 2: Assets (depends on sections)
        print("\n" + "─" * 60)
        print("STEP 2: Railway Assets")
        print("─" * 60)
        assets = seed_assets(db)

        # Step 3: Maintenance Tasks (depends on sections)
        print("\n" + "─" * 60)
        print("STEP 3: Maintenance Tasks")
        print("─" * 60)
        tasks = seed_maintenance_tasks(db)

        # Step 4: Train Timetable (depends on sections)
        print("\n" + "─" * 60)
        print("STEP 4: Train Timetable")
        print("─" * 60)
        schedules = seed_timetable(db)

        # Step 5: Users (no dependencies)
        print("\n" + "─" * 60)
        print("STEP 5: Demo Users")
        print("─" * 60)
        users = seed_users(db)

        # Final Summary
        print("\n" + "=" * 60)
        print("🎉 DATABASE SEED COMPLETE!")
        print("=" * 60)
        print(f"  📍 Sections:          {len(sections)}")
        print(f"  🔧 Assets:            {len(assets)}")
        print(f"  🔨 Maintenance Tasks: {len(tasks)}")
        print(f"  🚆 Train Schedules:   {len(schedules)}")
        print(f"  👤 Users:             {len(users)}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
