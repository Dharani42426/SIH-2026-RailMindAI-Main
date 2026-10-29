# ═══════════════════════════════════════════════════════════════
# RailMind AI — Train Schedule Model
# Maps to the `train_schedules` table
# Represents train timetable data from COA (Control Office Application)
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Numeric, Time, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models import Base


class TrainSchedule(Base):
    """
    Represents a train's schedule on a specific railway section.
    Data sourced from COA (Control Office Application).

    Train priorities (Indian Railways standard):
    1 = Rajdhani/Shatabdi/Vande Bharat (highest priority, cannot be disrupted)
    2 = Superfast Express
    3 = Mail/Express
    4 = Passenger/MEMU/DEMU
    5 = Goods/Freight (lowest priority, can be rerouted)

    Block planning must ensure NO maintenance block overlaps with
    train paths, especially Priority 1-2 trains.
    """
    __tablename__ = "train_schedules"

    id = Column(Integer, primary_key=True, index=True)
    train_no = Column(
        String(10), nullable=False, index=True,
        comment="Train number e.g. '12124'"
    )
    train_name = Column(
        String(100), nullable=False,
        comment="Train name e.g. 'Deccan Queen'"
    )
    train_type = Column(
        String(20), nullable=False, index=True,
        comment="Type: RAJDHANI/SHATABDI/VANDE_BHARAT/SF/EXPRESS/PASS/MEMU/GOODS"
    )
    priority = Column(
        Integer, nullable=False, index=True,
        comment="Priority 1 (highest) to 5 (lowest)"
    )
    section_id = Column(
        Integer, ForeignKey("railway_sections.id"), nullable=False, index=True
    )
    direction = Column(
        String(5), nullable=False,
        comment="Direction: UP/DN"
    )
    entry_km = Column(
        Numeric(8, 2), nullable=False,
        comment="KM where train enters the section"
    )
    exit_km = Column(
        Numeric(8, 2), nullable=False,
        comment="KM where train exits the section"
    )
    entry_time = Column(
        Time, nullable=False,
        comment="Time the train enters the section"
    )
    exit_time = Column(
        Time, nullable=False,
        comment="Time the train exits the section"
    )
    days_of_run = Column(
        String(20), default="DAILY",
        comment="Running days: DAILY/MWF/TTSS/SUN/MON/TUE/WED/THU/FRI/SAT"
    )
    is_special = Column(
        Boolean, default=False,
        comment="Whether this is a special/festival train"
    )
    avg_delay_min = Column(
        Integer, default=0,
        comment="Average delay in minutes (for buffer calculation)"
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ─── Relationships ───
    section = relationship("RailwaySection", back_populates="train_schedules")
    conflicts = relationship("ConflictLog", back_populates="train", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<TrainSchedule(no='{self.train_no}', name='{self.train_name}', "
            f"priority={self.priority}, {self.entry_time}-{self.exit_time})>"
        )

    @property
    def is_high_priority(self) -> bool:
        """Check if this train cannot be disrupted (Priority 1-2)."""
        return self.priority <= 2

    @property
    def duration_minutes(self) -> int:
        """Calculate the duration the train occupies the section."""
        from datetime import datetime, timedelta
        entry = datetime.combine(datetime.today(), self.entry_time)
        exit_ = datetime.combine(datetime.today(), self.exit_time)
        if exit_ < entry:
            exit_ += timedelta(days=1)  # handles midnight crossing
        return int((exit_ - entry).total_seconds() / 60)

    def runs_on_day(self, day_name: str) -> bool:
        """
        Check if the train runs on a specific day.
        day_name: MON/TUE/WED/THU/FRI/SAT/SUN
        """
        if self.days_of_run == "DAILY":
            return True
        day_map = {
            "MWF": ["MON", "WED", "FRI"],
            "TTSS": ["TUE", "THU", "SAT", "SUN"],
        }
        if self.days_of_run in day_map:
            return day_name.upper() in day_map[self.days_of_run]
        return day_name.upper() == self.days_of_run.upper()
