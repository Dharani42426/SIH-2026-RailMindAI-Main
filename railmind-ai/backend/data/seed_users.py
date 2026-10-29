# ═══════════════════════════════════════════════════════════════
# RailMind AI — Seed Demo Users
# Idempotent: only inserts users that do not already exist
# ═══════════════════════════════════════════════════════════════

from sqlalchemy.orm import Session

from models import SessionLocal, create_all_tables
from models.user import User


DEMO_USERS = [
    {
        "employee_id": "AK001",
        "full_name": "A. Kumar",
        "email": "a.kumar@cr.indianrailways.gov.in",
        "role": "CONTROLLER",
        "department": "OPS",
        "division": "Mumbai Central",
    },
    {
        "employee_id": "RS002",
        "full_name": "R. Sharma",
        "email": "r.sharma@cr.indianrailways.gov.in",
        "role": "DEN",
        "department": "ENGG",
        "division": "Mumbai Central",
    },
    {
        "employee_id": "VP003",
        "full_name": "V. Patel",
        "email": "v.patel@cr.indianrailways.gov.in",
        "role": "DSTE",
        "department": "SNT",
        "division": "Mumbai Central",
    },
    {
        "employee_id": "MT004",
        "full_name": "M. Tiwari",
        "email": "m.tiwari@cr.indianrailways.gov.in",
        "role": "DEE",
        "department": "TRD",
        "division": "Mumbai Central",
    },
    {
        "employee_id": "SA005",
        "full_name": "S. Agarwal",
        "email": "s.agarwal@cr.indianrailways.gov.in",
        "role": "ADMIN",
        "department": "OPS",
        "division": "Mumbai Central",
    },
]


def seed_users(db: Session) -> list[User]:
    """
    Seed demo users into the database.
    Idempotent — skips users whose employee_id already exists.
    Does NOT delete or modify any existing users.
    """
    created = []
    skipped = []

    for user_data in DEMO_USERS:
        existing = db.query(User).filter_by(
            employee_id=user_data["employee_id"]
        ).first()

        if existing:
            skipped.append(user_data["employee_id"])
            continue

        user = User(**user_data, is_active=True)
        db.add(user)
        created.append(user)

    if created:
        db.commit()

    for u in created:
        print(f"  [+] Created: {u.employee_id} -- {u.full_name} ({u.role}/{u.department})")
    for emp_id in skipped:
        print(f"  [=] Skipped (exists): {emp_id}")

    return created


if __name__ == "__main__":
    """Standalone execution — seed users."""
    print("[*] Seeding Demo Users...\n")

    create_all_tables()

    db = SessionLocal()
    try:
        users = seed_users(db)
        print(f"\n[OK] Done. Created {len(users)} new user(s).")
    finally:
        db.close()
