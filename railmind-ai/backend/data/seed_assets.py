# ═══════════════════════════════════════════════════════════════
# RailMind AI — Seed Railway Assets
# Generates 300+ realistic railway assets (track, signal, OHE)
# for all sections in the database
# ═══════════════════════════════════════════════════════════════

import os
import sys
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.asset import RailwayAsset


# ─── Asset Templates ───
TRACK_ASSETS = [
    ("60kg Rail Segment", "TRACK", "ENGG"),
    ("PSC Sleeper Set", "TRACK", "ENGG"),
    ("Point & Crossing", "TRACK", "ENGG"),
    ("Fish Plate Joint", "TRACK", "ENGG"),
    ("Ballast Bed", "TRACK", "ENGG"),
    ("Concrete Sleeper Set", "TRACK", "ENGG"),
    ("SEJ (Switch Expansion Joint)", "TRACK", "ENGG"),
    ("Glued Insulated Joint", "TRACK", "ENGG"),
]

SIGNAL_ASSETS = [
    ("Color Light Signal", "SIGNAL", "SNT"),
    ("Point Machine (Siemens)", "SIGNAL", "SNT"),
    ("Track Circuit (AFTC)", "SIGNAL", "SNT"),
    ("Axle Counter", "SIGNAL", "SNT"),
    ("Relay Interlocking Panel", "SIGNAL", "SNT"),
    ("Block Instrument", "SIGNAL", "SNT"),
    ("OFC Junction Box", "SIGNAL", "SNT"),
    ("Data Logger", "SIGNAL", "SNT"),
]

OHE_ASSETS = [
    ("Contact Wire 107 sqmm", "OHE", "TRD"),
    ("Catenary Wire", "OHE", "TRD"),
    ("OHE Mast (Steel Tubular)", "OHE", "TRD"),
    ("Cantilever Assembly", "OHE", "TRD"),
    ("9-Disc Insulator String", "OHE", "TRD"),
    ("Booster Transformer", "OHE", "TRD"),
    ("Section Insulator", "OHE", "TRD"),
    ("ATD (Auto Tension Device)", "OHE", "TRD"),
]

BRIDGE_ASSETS = [
    ("Steel Girder Bridge", "BRIDGE", "ENGG"),
    ("RCC Box Culvert", "BRIDGE", "ENGG"),
    ("Arch Bridge (Masonry)", "BRIDGE", "ENGG"),
]


def generate_health_score(install_date: date, is_ghat: bool) -> float:
    """
    Generate realistic health score based on asset age and location.
    Older assets and ghat section assets degrade faster.
    """
    age_days = (date.today() - install_date).days
    age_years = age_days / 365.25

    # Base degradation: ~2-4% per year
    base_degradation = random.uniform(2.0, 4.0) * age_years

    # Ghat sections degrade 30% faster
    if is_ghat:
        base_degradation *= 1.3

    # Add random variation
    variation = random.uniform(-5, 10)
    health = max(5.0, min(100.0, 100.0 - base_degradation + variation))

    return round(health, 2)


def generate_status(health: float) -> str:
    """Determine asset status based on health score."""
    if health >= 80:
        return "ACTIVE"
    elif health >= 50:
        return "DEGRADED"
    elif health >= 20:
        return "DEGRADED"
    else:
        return "FAILED"


def seed_assets(db: Session) -> list[RailwayAsset]:
    """
    Generate realistic railway assets for all sections in the database.
    Creates ~30 assets per section (varies by section length and type).
    """
    sections = db.query(RailwaySection).all()
    if not sections:
        print("❌ No sections found! Run seed_corridor.py first.")
        return []

    # Check if assets already exist
    existing_count = db.query(RailwayAsset).count()
    if existing_count > 0:
        print(f"⏭️  {existing_count} assets already exist. Skipping seed.")
        return db.query(RailwayAsset).all()

    created = []
    asset_counter = {"TRACK": 0, "SIGNAL": 0, "OHE": 0, "BRIDGE": 0}

    for section in sections:
        section_length = float(section.km_end - section.km_start)
        is_ghat = section.is_ghat_section

        # Number of assets proportional to section length
        num_track = max(5, int(section_length / 3))
        num_signal = max(3, int(section_length / 5))
        num_ohe = max(3, int(section_length / 4))
        num_bridge = max(1, int(section_length / 15))

        all_templates = (
            [(t, num_track) for t in TRACK_ASSETS[:random.randint(3, len(TRACK_ASSETS))]] +
            [(t, num_signal) for t in SIGNAL_ASSETS[:random.randint(3, len(SIGNAL_ASSETS))]] +
            [(t, num_ohe) for t in OHE_ASSETS[:random.randint(3, len(OHE_ASSETS))]] +
            [(t, num_bridge) for t in BRIDGE_ASSETS[:random.randint(1, len(BRIDGE_ASSETS))]]
        )

        for (equip_name, asset_type, dept), count in all_templates:
            for i in range(max(1, count // len(TRACK_ASSETS))):
                asset_counter[asset_type] = asset_counter.get(asset_type, 0) + 1
                code_prefix = {
                    "TRACK": "TRK", "SIGNAL": "SIG", "OHE": "OHE", "BRIDGE": "BRG"
                }[asset_type]

                # Random KM within section
                km_loc = round(
                    random.uniform(float(section.km_start), float(section.km_end)),
                    2
                )
                km_end_val = round(km_loc + random.uniform(0.5, 2.0), 2) if asset_type == "TRACK" else None

                # Random install date (1-20 years ago)
                install = date.today() - timedelta(
                    days=random.randint(365, 365 * 20)
                )
                last_maint = date.today() - timedelta(
                    days=random.randint(30, 365)
                )

                health = generate_health_score(install, is_ghat)

                asset = RailwayAsset(
                    asset_code=f"{code_prefix}-{section.section_code}-{asset_counter[asset_type]:04d}",
                    asset_type=asset_type,
                    department=dept,
                    section_id=section.id,
                    km_location=km_loc,
                    km_end=km_end_val,
                    equipment_name=equip_name,
                    install_date=install,
                    last_maintained=last_maint,
                    health_score=health,
                    status=generate_status(health),
                )
                db.add(asset)
                created.append(asset)

        print(f"  ✅ Section {section.section_code}: generated {len(created)} assets so far")

    db.commit()
    print(f"\n📊 Total assets: {len(created)}")
    print(f"   TRACK: {asset_counter.get('TRACK', 0)}")
    print(f"   SIGNAL: {asset_counter.get('SIGNAL', 0)}")
    print(f"   OHE: {asset_counter.get('OHE', 0)}")
    print(f"   BRIDGE: {asset_counter.get('BRIDGE', 0)}")
    return created


def run():
    """Standalone execution."""
    print("🔧 Seeding Railway Assets...\n")
    create_all_tables()
    db = SessionLocal()
    try:
        assets = seed_assets(db)
        print(f"\n✅ Done! {len(assets)} assets generated.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
