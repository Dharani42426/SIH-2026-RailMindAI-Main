# ═══════════════════════════════════════════════════════════════
# RailMind AI — Maintenance Request Model
# Maps to the `maintenance_requests` table
# Represents departmental requests before they become Tasks
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime,
    Text, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models import Base


class MaintenanceRequest(Base):
    """
    Represents a departmental request for maintenance.
    
    A MaintenanceRequest goes through a lifecycle:
    DRAFT → SUBMITTED → UNDER_REVIEW → ACCEPTED | REJECTED
    
    If ACCEPTED, it spawns a MaintenanceTask for the AI optimizer.
    """
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(
        String(30), unique=True, nullable=False, index=True,
        comment="Unique request code e.g. 'REQ-ENGG-2026-001'"
    )
    requester_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
        comment="The user who created this request"
    )
    department = Column(
        String(20), nullable=False, index=True,
        comment="Responsible department: ENGG/SNT/TRD"
    )
    section_id = Column(
        Integer, ForeignKey("railway_sections.id"), nullable=False, index=True
    )
    work_type = Column(
        String(50), nullable=False,
        comment="Type of work e.g. 'Rail Fracture Repair', 'Signal Cable Replacement'"
    )
    description = Column(
        Text, nullable=True,
        comment="Detailed description of the work required"
    )
    justification = Column(
        Text, nullable=True,
        comment="Operational reason / justification for the request"
    )
    km_from = Column(
        Numeric(8, 2), nullable=False,
        comment="Start KM of affected area"
    )
    km_to = Column(
        Numeric(8, 2), nullable=False,
        comment="End KM of affected area"
    )
    estimated_hours = Column(
        Numeric(4, 1), nullable=False,
        comment="Estimated block hours needed for the task"
    )
    block_type_required = Column(
        String(30), nullable=False,
        comment="Block type needed: TRAFFIC/POWER/DISCONNECTION/INTEGRATED"
    )
    preferred_date = Column(
        Date, nullable=False,
        comment="Preferred date for the maintenance window"
    )
    
    # ─── Status Tracking ───
    status = Column(
        String(20), default="DRAFT", index=True,
        comment="Request status: DRAFT/SUBMITTED/UNDER_REVIEW/ACCEPTED/REJECTED"
    )
    maintenance_task_id = Column(
        Integer, ForeignKey("maintenance_tasks.id"), nullable=True, index=True,
        comment="The resulting AI task, if accepted"
    )
    rejection_reason = Column(
        Text, nullable=True,
        comment="Reason if the request is rejected by controller"
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ─── Relationships ───
    requester = relationship("User", foreign_keys=[requester_id])
    section = relationship("RailwaySection")
    task = relationship("MaintenanceTask", foreign_keys=[maintenance_task_id])

    def __repr__(self):
        return (
            f"<MaintenanceRequest(code='{self.request_code}', type='{self.work_type}', "
            f"status='{self.status}')>"
        )
