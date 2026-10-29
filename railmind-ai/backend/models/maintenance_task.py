# ═══════════════════════════════════════════════════════════════
# RailMind AI — Maintenance Task Model
# Maps to the `maintenance_tasks` table
# Unified model for TMS + SMMS + TDMS defects/tasks
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime,
    Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models import Base


class MaintenanceTask(Base):
    """
    Unified maintenance task model that merges data from 3 Indian Railways systems:
    - TMS (Track Management System) — track defects, rail fractures, geometry issues
    - SMMS (Signal Maintenance Management System) — signal failures, point machine defects
    - TDMS (Traction Distribution Management System) — OHE wear, power supply issues

    Each task has:
    - A criticality_score (0-100) computed by the XGBoost AI model
    - A predicted_failure date from the LSTM predictive engine
    - Required block type (TRAFFIC/POWER/DISCONNECTION)
    - Status tracking through the block planning lifecycle
    """
    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_code = Column(
        String(30), unique=True, nullable=False, index=True,
        comment="Unique task code e.g. 'TMS-MUM-2026-04523'"
    )
    source_system = Column(
        String(10), nullable=False, index=True,
        comment="Source system: TMS/SMMS/TDMS"
    )
    department = Column(
        String(20), nullable=False, index=True,
        comment="Responsible department: ENGG/SNT/TRD"
    )
    asset_id = Column(
        Integer, ForeignKey("railway_assets.id"), nullable=True, index=True
    )
    section_id = Column(
        Integer, ForeignKey("railway_sections.id"), nullable=False, index=True
    )
    km_from = Column(
        Numeric(8, 2), nullable=False,
        comment="Start KM of affected area"
    )
    km_to = Column(
        Numeric(8, 2), nullable=False,
        comment="End KM of affected area"
    )
    task_type = Column(
        String(50), nullable=False,
        comment="Type of work e.g. 'Rail Fracture Repair', 'Signal Cable Replacement'"
    )
    severity = Column(
        String(20), nullable=False, index=True,
        comment="Severity level: CRITICAL/HIGH/MEDIUM/LOW"
    )
    detected_date = Column(
        Date, nullable=False,
        comment="Date the defect was detected"
    )
    due_date = Column(
        Date, nullable=False,
        comment="Deadline for completion"
    )
    estimated_hours = Column(
        Numeric(4, 1), nullable=False,
        comment="Estimated block hours needed for the task"
    )
    block_type_required = Column(
        String(30), nullable=False,
        comment="Block type needed: TRAFFIC/POWER/DISCONNECTION/INTEGRATED"
    )
    line_affected = Column(
        String(10), nullable=True,
        comment="Which line is affected: UP/DN/BOTH"
    )
    speed_restriction = Column(
        Integer, nullable=True,
        comment="Speed restriction imposed (km/h), if any"
    )
    is_overdue = Column(
        Boolean, default=False, index=True,
        comment="Whether the task has passed its due date"
    )

    # ─── AI-Generated Fields ───
    criticality_score = Column(
        Numeric(5, 2), nullable=True,
        comment="AI-generated criticality score (0-100) from XGBoost model"
    )
    predicted_failure = Column(
        Date, nullable=True,
        comment="Predicted failure date from LSTM model"
    )

    # ─── Status Tracking ───
    status = Column(
        String(20), default="PENDING", index=True,
        comment="Task status: PENDING/SCHEDULED/IN_PROGRESS/COMPLETED/CANCELLED"
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ─── Relationships ───
    asset = relationship("RailwayAsset", back_populates="maintenance_tasks")
    section = relationship("RailwaySection", back_populates="maintenance_tasks")
    block_assignments = relationship(
        "BlockTaskAssignment", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<MaintenanceTask(code='{self.task_code}', type='{self.task_type}', "
            f"severity='{self.severity}', score={self.criticality_score})>"
        )

    @property
    def severity_numeric(self) -> int:
        """Convert severity to numeric value for ML features."""
        severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return severity_map.get(self.severity, 0)

    @property
    def affected_km_range(self) -> float:
        """Calculate the KM range affected by this task."""
        return float(self.km_to - self.km_from)

    @property
    def block_plan_code(self) -> str | None:
        """Get the plan code of the block this task is assigned to."""
        if self.block_assignments and len(self.block_assignments) > 0:
            assignment = self.block_assignments[0]
            if assignment.block and assignment.block.plan:
                return assignment.block.plan.plan_code
        return None
