# ═══════════════════════════════════════════════════════════════
# RailMind AI — User Model
# Maps to the `users` table
# Represents railway personnel with role-based access
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime
)
from sqlalchemy.sql import func

from models import Base


class User(Base):
    """
    Represents a railway official who uses the RailMind AI system.

    Roles and their permissions:
    - CONTROLLER: Section Controller — can approve/reject block plans,
                  view all data, trigger AI optimization
    - DEN: Divisional Engineer — can submit maintenance requests (Engineering)
    - SSE: Senior Section Engineer — can submit maintenance requests
    - DSTE: Divisional Signal & Telecom Engineer — S&T department head
    - DEE: Divisional Electrical Engineer — TRD department head
    - PWI: Permanent Way Inspector — field-level track inspection
    - SI: Signal Inspector — field-level signal inspection
    - ADMIN: System administrator

    Departments:
    - ENGG: Engineering (track, bridges, structures)
    - SNT: Signal & Telecom
    - TRD: Traction Distribution (OHE, power)
    - OPS: Operations (controllers)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        String(20), unique=True, nullable=False, index=True,
        comment="Railway employee ID"
    )
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    role = Column(
        String(20), nullable=False, index=True,
        comment="Role: CONTROLLER/DEN/SSE/DSTE/DEE/PWI/SI/ADMIN"
    )
    department = Column(
        String(20), nullable=False, index=True,
        comment="Department: ENGG/SNT/TRD/OPS"
    )
    division = Column(
        String(50), nullable=True,
        comment="Railway division e.g. 'Mumbai Central'"
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return (
            f"<User(emp_id='{self.employee_id}', name='{self.full_name}', "
            f"role='{self.role}', dept='{self.department}')>"
        )

    @property
    def can_approve_plans(self) -> bool:
        """Only Controllers and Admins can approve block plans."""
        return self.role in ("CONTROLLER", "ADMIN")

    @property
    def can_submit_tasks(self) -> bool:
        """Engineers and Inspectors can submit maintenance tasks."""
        return self.role in ("DEN", "SSE", "DSTE", "DEE", "PWI", "SI", "ADMIN")

    @property
    def can_trigger_optimizer(self) -> bool:
        """Only Controllers and Admins can trigger AI optimization."""
        return self.role in ("CONTROLLER", "ADMIN")
