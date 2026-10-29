# ═══════════════════════════════════════════════════════════════
# RailMind AI — Railway Asset Model
# Maps to the `railway_assets` table
# Represents track, signal, and OHE equipment inventory
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models import Base


class RailwayAsset(Base):
    """
    Represents a railway asset (equipment) that requires maintenance.

    Asset types:
    - TRACK: Rails, sleepers, ballast, points/crossings
    - SIGNAL: Color light signals, point machines, track circuits
    - OHE: Overhead equipment, pantograph, masts, cantilevers
    - BRIDGE: Railway bridges and culverts

    Each asset belongs to a department:
    - ENGG: Engineering (track & structures)
    - SNT: Signal & Telecom
    - TRD: Traction Distribution (power/OHE)
    """
    __tablename__ = "railway_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(
        String(30), unique=True, nullable=False, index=True,
        comment="Unique asset code e.g. 'TRK-KYN-045'"
    )
    asset_type = Column(
        String(20), nullable=False, index=True,
        comment="Asset category: TRACK/SIGNAL/OHE/BRIDGE"
    )
    department = Column(
        String(20), nullable=False, index=True,
        comment="Responsible department: ENGG/SNT/TRD"
    )
    section_id = Column(
        Integer, ForeignKey("railway_sections.id"), nullable=False, index=True
    )
    km_location = Column(
        Numeric(8, 2), nullable=False,
        comment="KM marker for point assets"
    )
    km_end = Column(
        Numeric(8, 2), nullable=True,
        comment="End KM for range-based assets (e.g., track segments)"
    )
    equipment_name = Column(
        String(100), nullable=True,
        comment="Specific equipment name e.g. 'Color Light Signal', '60kg Rail'"
    )
    install_date = Column(
        Date, nullable=True,
        comment="Date the asset was installed"
    )
    last_maintained = Column(
        Date, nullable=True,
        comment="Date of last maintenance activity"
    )
    health_score = Column(
        Numeric(5, 2), default=100.00,
        comment="Current health percentage (0-100). AI updates this."
    )
    status = Column(
        String(20), default="ACTIVE", index=True,
        comment="Asset status: ACTIVE/DEGRADED/FAILED/DECOMMISSIONED"
    )
    metadata_json = Column(
        "metadata", JSON, nullable=True,
        comment="Flexible extra fields stored as JSON"
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ─── Relationships ───
    section = relationship("RailwaySection", back_populates="assets")
    maintenance_tasks = relationship("MaintenanceTask", back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RailwayAsset(code='{self.asset_code}', type='{self.asset_type}', health={self.health_score}%)>"

    @property
    def is_critical(self) -> bool:
        """Asset is critical if health drops below 50%."""
        return float(self.health_score) < 50.0

    @property
    def age_days(self) -> int | None:
        """Calculate asset age in days from install date."""
        if self.install_date:
            from datetime import date
            return (date.today() - self.install_date).days
        return None
