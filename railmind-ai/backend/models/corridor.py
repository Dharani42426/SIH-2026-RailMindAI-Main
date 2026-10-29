# ═══════════════════════════════════════════════════════════════
# RailMind AI — Railway Section / Corridor Model
# Maps to the `railway_sections` table
# Represents physical railway infrastructure sections
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models import Base


class RailwaySection(Base):
    """
    Represents a physical railway section (corridor) on Indian Railways.

    Example: CSMT-KYN (Chhatrapati Shivaji Maharaj Terminus to Kalyan)
    - Sections are the fundamental geographic unit for block planning
    - Each section has KM markers, track type, traction, and traffic density
    - Maintenance tasks, assets, and block plans are all linked to sections
    """
    __tablename__ = "railway_sections"

    id = Column(Integer, primary_key=True, index=True)
    section_code = Column(
        String(20), unique=True, nullable=False, index=True,
        comment="Unique code e.g. 'CSMT-KYN'"
    )
    section_name = Column(
        String(100), nullable=False,
        comment="Full name e.g. 'CSMT to Kalyan'"
    )
    division = Column(
        String(50), nullable=False,
        comment="Railway division e.g. 'Mumbai Central'"
    )
    zone = Column(
        String(50), nullable=False,
        comment="Railway zone e.g. 'Central Railway'"
    )
    km_start = Column(
        Numeric(8, 2), nullable=False,
        comment="Starting KM marker e.g. 0.00"
    )
    km_end = Column(
        Numeric(8, 2), nullable=False,
        comment="Ending KM marker e.g. 54.00"
    )
    track_type = Column(
        String(20), default="DBL",
        comment="Track type: SGL/DBL/TRIPLE/QUAD"
    )
    traction = Column(
        String(20), default="AC25KV",
        comment="Traction type: AC25KV/DC1500V/DIESEL"
    )
    max_speed_kmph = Column(
        Integer, default=110,
        comment="Maximum permissible speed in km/h"
    )
    trains_per_day = Column(
        Integer, default=100,
        comment="Average number of trains per day (traffic density)"
    )
    is_ghat_section = Column(
        Boolean, default=False,
        comment="Whether this is a ghat (mountain) section with special constraints"
    )
    description = Column(
        Text, nullable=True,
        comment="Additional description or notes about the section"
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ─── Relationships ───
    assets = relationship("RailwayAsset", back_populates="section", cascade="all, delete-orphan")
    maintenance_tasks = relationship("MaintenanceTask", back_populates="section", cascade="all, delete-orphan")
    train_schedules = relationship("TrainSchedule", back_populates="section", cascade="all, delete-orphan")
    block_plans = relationship("BlockPlan", back_populates="section", cascade="all, delete-orphan")
    block_windows = relationship("BlockWindow", back_populates="section", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RailwaySection(code='{self.section_code}', name='{self.section_name}')>"

    @property
    def total_km(self) -> float:
        """Calculate the total length of the section in KM."""
        return float(self.km_end - self.km_start)
