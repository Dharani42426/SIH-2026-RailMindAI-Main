# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RailMind AI â€” Pydantic Schemas for API Request/Response
# These define the shape of data going in/out of the API
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional
from enum import Enum


# â”€â”€â”€ Enums â”€â”€â”€

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Department(str, Enum):
    ENGG = "ENGG"
    SNT = "SNT"
    TRD = "TRD"


class SourceSystem(str, Enum):
    TMS = "TMS"
    SMMS = "SMMS"
    TDMS = "TDMS"


class BlockType(str, Enum):
    TRAFFIC = "TRAFFIC"
    POWER = "POWER"
    DISCONNECTION = "DISCONNECTION"
    INTEGRATED = "INTEGRATED"
    MEGA = "MEGA"


class LineAffected(str, Enum):
    UP = "UP"
    DN = "DN"
    BOTH = "BOTH"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RequestStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RAILWAY SECTION SCHEMAS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class SectionBase(BaseModel):
    section_code: str = Field(..., example="CSMT-KYN")
    section_name: str = Field(..., example="CSMT to Kalyan")
    division: str = Field(..., example="Mumbai Central")
    zone: str = Field(..., example="Central Railway")
    km_start: float = Field(..., example=0.0)
    km_end: float = Field(..., example=54.0)
    track_type: str = Field(default="DBL", example="DBL")
    traction: str = Field(default="AC25KV", example="AC25KV")
    max_speed_kmph: int = Field(default=110)
    trains_per_day: int = Field(default=100)
    is_ghat_section: bool = Field(default=False)


class SectionCreate(SectionBase):
    pass


class SectionResponse(SectionBase):
    id: int
    total_km: float = Field(description="Total section length in KM")
    created_at: datetime

    class Config:
        from_attributes = True


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAINTENANCE TASK SCHEMAS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TaskBase(BaseModel):
    task_code: str = Field(..., example="TMS-MUM-2026-04523")
    source_system: SourceSystem
    department: Department
    section_id: int
    asset_id: Optional[int] = None
    km_from: float = Field(..., example=45.0)
    km_to: float = Field(..., example=47.5)
    task_type: str = Field(..., example="Rail Fracture Repair")
    severity: Severity
    detected_date: date
    due_date: date
    estimated_hours: float = Field(..., example=2.5)
    block_type_required: BlockType
    line_affected: Optional[LineAffected] = None
    speed_restriction: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    is_overdue: bool
    criticality_score: Optional[float] = Field(
        None, description="AI-generated criticality score (0-100)"
    )
    predicted_failure: Optional[date] = Field(
        None, description="LSTM-predicted failure date"
    )
    status: TaskStatus
    created_at: datetime
    block_plan_code: Optional[str] = None

    class Config:
        from_attributes = True


class TaskWithCriticality(TaskResponse):
    """Extended task response with criticality breakdown."""
    criticality_rank: Optional[int] = Field(
        None, description="Rank among all tasks (1 = most critical)"
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAINTENANCE REQUEST SCHEMAS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class MaintenanceRequestBase(BaseModel):
    department: Department
    section_id: int
    work_type: str = Field(..., example="Rail Fracture Repair")
    description: Optional[str] = None
    justification: Optional[str] = None
    km_from: float = Field(..., example=45.0)
    km_to: float = Field(..., example=47.5)
    estimated_hours: float = Field(..., example=2.5)
    block_type_required: BlockType
    preferred_date: date


class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass


class MaintenanceRequestUpdate(BaseModel):
    department: Optional[Department] = None
    section_id: Optional[int] = None
    work_type: Optional[str] = None
    description: Optional[str] = None
    justification: Optional[str] = None
    km_from: Optional[float] = None
    km_to: Optional[float] = None
    estimated_hours: Optional[float] = None
    block_type_required: Optional[BlockType] = None
    preferred_date: Optional[date] = None


class MaintenanceRequestResponse(MaintenanceRequestBase):
    id: int
    request_code: str
    requester_id: int
    status: RequestStatus
    maintenance_task_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaintenanceRequestReview(BaseModel):
    action: str = Field(..., description="ACCEPT or REJECT")
    rejection_reason: Optional[str] = Field(None, description="Required if action is REJECT")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TRAIN SCHEDULE SCHEMAS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TrainBase(BaseModel):
    train_no: str = Field(..., example="12124")
    train_name: str = Field(..., example="Deccan Queen")
    train_type: str = Field(..., example="SF")
    priority: int = Field(..., ge=1, le=5)
    section_id: int
    direction: LineAffected
    entry_km: float
    exit_km: float
    entry_time: time
    exit_time: time
    days_of_run: str = Field(default="DAILY")
    is_special: bool = Field(default=False)
    avg_delay_min: int = Field(default=0)


class TrainCreate(TrainBase):
    pass


class TrainResponse(TrainBase):
    id: int
    is_high_priority: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# BLOCK PLAN SCHEMAS
# ═══════════════════════════════════════════════════════════════

class BlockTaskAssignmentResponse(BaseModel):
    id: int
    task_id: int
    sequence_order: int
    start_offset_min: int
    duration_min: int
    assigned_team: Optional[str] = None
    status: str
    task: TaskResponse

    class Config:
        from_attributes = True


class BlockWindowResponse(BaseModel):
    id: int
    block_code: str
    block_date: date
    start_time: time
    end_time: time
    duration_hrs: float
    km_from: float
    km_to: float
    block_type: BlockType
    line_blocked: LineAffected
    is_integrated: bool
    departments: Optional[str] = None
    status: str
    ai_explanation: Optional[str] = None
    task_count: Optional[int] = None
    task_assignments: list[BlockTaskAssignmentResponse] = []

    class Config:
        from_attributes = True


class BlockPlanResponse(BaseModel):
    id: int
    plan_code: str
    plan_type: str
    section_id: int
    generated_at: datetime
    generated_by: str
    plan_start_date: date
    plan_end_date: date
    total_blocks: Optional[int] = None
    total_block_hrs: Optional[float] = None
    utilization_pct: Optional[float] = None
    optimization_score: Optional[float] = None
    tasks_scheduled: Optional[int] = None
    conflicts_resolved: int = 0
    status: PlanStatus
    approved_by: Optional[str] = None
    safety_report_data: Optional[dict] = None
    block_windows: list[BlockWindowResponse] = []

    class Config:
        from_attributes = True


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# OPTIMIZER REQUEST/RESPONSE SCHEMAS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class GeneratePlanRequest(BaseModel):
    """Request to trigger AI block plan generation."""
    section_id: int = Field(..., description="Section to generate plan for")
    plan_type: str = Field(default="WEEKLY", description="WEEKLY or MONTHLY")
    start_date: date = Field(..., description="Plan start date")
    end_date: Optional[date] = Field(
        None, description="Plan end date (auto-calculated if not provided)"
    )
    include_predictive: bool = Field(
        default=True, description="Include LSTM predictions in scheduling"
    )
    max_solve_time: Optional[int] = Field(
        None, description="Max solver time in seconds (default: 5)"
    )


class WhatIfRequest(BaseModel):
    """Request for what-if scenario simulation."""
    plan_id: int
    changes: list[dict] = Field(
        ..., description="List of changes to simulate",
        example=[{"action": "add_train", "train_no": "22222", "time": "11:30"}]
    )


class OptimizationResult(BaseModel):
    """Response from the AI optimizer."""
    plan: BlockPlanResponse
    solve_time_seconds: float
    tasks_total: int
    tasks_scheduled: int
    tasks_deferred: int
    conflicts_detected: int
    conflicts_resolved: int
    integrated_blocks: int
    kpis: dict = Field(
        description="Key performance indicators",
        example={
            "utilization_pct": 89.5,
            "time_saved_hrs": 12.3,
            "asset_availability_pct": 94.2,
        }
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ANALYTICS / KPI SCHEMAS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class KPIResponse(BaseModel):
    """Dashboard KPI metrics."""
    asset_availability_pct: float
    block_utilization_pct: float
    tasks_pending: int
    tasks_overdue: int
    active_conflicts: int
    total_blocks_this_week: int
    total_block_hours_this_week: float
    integrated_block_pct: float
    avg_criticality_score: float
    departments_breakdown: dict = Field(
        example={"ENGG": 22, "SNT": 14, "TRD": 11}
    )


class BeforeAfterComparison(BaseModel):
    """Before/After AI optimization comparison stats."""
    metric: str
    before_value: float
    after_value: float
    improvement_pct: float
    unit: str


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# NLP COMMAND SCHEMA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class NLPCommandRequest(BaseModel):
    """Natural language command from a railway controller."""
    command: str = Field(
        ...,
        example="Show me available blocks for track tamping on Kalyan-Kasara section next week"
    )


class NLPCommandResponse(BaseModel):
    """Parsed NLP command result."""
    original_command: str
    intent: str = Field(description="Detected intent: QUERY/SCHEDULE/STATUS/HELP")
    entities: dict = Field(
        description="Extracted entities",
        example={"section": "KYN-KAS", "task_type": "track tamping", "timeframe": "next_week"}
    )
    api_action: str = Field(description="Mapped API endpoint to call")
    response_text: str = Field(description="Natural language response")
    ai_engine: Optional[str] = Field(None, description="The AI provider used")
    data: Optional[dict] = None
