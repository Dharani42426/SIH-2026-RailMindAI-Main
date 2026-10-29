# ═══════════════════════════════════════════════════════════════
# RailMind AI — Train Schedule Routes
# Endpoints for train timetable data and conflict checking
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, time
from typing import Optional

from models import get_db
from models.train_schedule import TrainSchedule
from schemas import TrainCreate, TrainResponse

router = APIRouter(prefix="/trains", tags=["Train Schedules"])


@router.get("/", response_model=list[TrainResponse])
def list_trains(
    section_id: Optional[int] = Query(None),
    priority: Optional[int] = Query(None, ge=1, le=5),
    train_type: Optional[str] = Query(None),
    direction: Optional[str] = Query(None, description="UP/DN"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """List train schedules with filters."""
    query = db.query(TrainSchedule)

    if section_id:
        query = query.filter(TrainSchedule.section_id == section_id)
    if priority:
        query = query.filter(TrainSchedule.priority == priority)
    if train_type:
        query = query.filter(TrainSchedule.train_type == train_type.upper())
    if direction:
        query = query.filter(TrainSchedule.direction == direction.upper())

    trains = query.order_by(
        TrainSchedule.priority.asc(),
        TrainSchedule.entry_time.asc(),
    ).limit(limit).all()

    result = []
    for t in trains:
        data = TrainResponse.model_validate(t)
        data.is_high_priority = t.is_high_priority
        result.append(data)

    return result


@router.get("/{train_id}", response_model=TrainResponse)
def get_train(train_id: int, db: Session = Depends(get_db)):
    """Get a single train schedule."""
    train = db.query(TrainSchedule).filter_by(id=train_id).first()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    data = TrainResponse.model_validate(train)
    data.is_high_priority = train.is_high_priority
    return data


@router.get("/section/{section_id}/windows")
def get_train_windows(
    section_id: int,
    target_date: date = Query(default=None, description="Date to check (default: today)"),
    direction: Optional[str] = Query(None, description="UP/DN"),
    db: Session = Depends(get_db),
):
    """
    Get all train windows (occupied times) for a section on a date.
    Shows when each train passes through the section.
    """
    from services.data_integrator import DataIntegrator

    if target_date is None:
        target_date = date.today()

    integrator = DataIntegrator(db)
    windows = integrator.get_train_windows(section_id, target_date, direction)

    return {
        "section_id": section_id,
        "date": target_date.isoformat(),
        "total_trains": len(windows),
        "high_priority_trains": sum(1 for w in windows if w["is_high_priority"]),
        "trains": windows,
    }


@router.get("/section/{section_id}/available")
def get_available_windows(
    section_id: int,
    target_date: date = Query(default=None),
    min_duration: int = Query(60, description="Minimum window duration in minutes"),
    db: Session = Depends(get_db),
):
    """
    Find available time windows for block scheduling.
    Returns gaps between trains where maintenance can be done.
    """
    from services.data_integrator import DataIntegrator

    if target_date is None:
        target_date = date.today()

    integrator = DataIntegrator(db)
    windows = integrator.get_available_windows(
        section_id, target_date, min_duration_minutes=min_duration
    )

    return {
        "section_id": section_id,
        "date": target_date.isoformat(),
        "min_duration_minutes": min_duration,
        "available_windows": len(windows),
        "windows": [
            {
                "start_time": w["start_time"].strftime("%H:%M"),
                "end_time": w["end_time"].strftime("%H:%M"),
                "duration_min": w["duration_min"],
            }
            for w in windows
        ],
    }


@router.get("/section/{section_id}/conflicts")
def check_conflicts(
    section_id: int,
    block_date: date = Query(...),
    block_start: str = Query(..., description="Block start time HH:MM"),
    block_end: str = Query(..., description="Block end time HH:MM"),
    line: str = Query("BOTH", description="UP/DN/BOTH"),
    db: Session = Depends(get_db),
):
    """
    Check if a proposed block window conflicts with any train.
    Returns all conflicting trains and suggested alternatives.
    """
    from services.conflict_resolver import ConflictResolver
    from services.llm_providers import NvidiaProvider

    start = time(*map(int, block_start.split(":")))
    end = time(*map(int, block_end.split(":")))

    resolver = ConflictResolver(db)
    conflicts = resolver.check_train_conflict(
        section_id, block_date, start, end, line
    )

    ai_mitigation = None
    if conflicts:
        try:
            from services.llm_providers import create_llm_router_from_settings
            llm_router = create_llm_router_from_settings()
            prompt = (
                f"You are the RailMind AI Safety Controller. A human controller proposed a maintenance block on "
                f"Section ID {section_id} for date {block_date} from {block_start} to {block_end} (Line: {line}).\n\n"
                f"This proposal caused the following conflicts with the active train timetable:\n"
            )
            for c in conflicts:
                prompt += f"- {c['train_name']} ({c['train_no']}): Priority {c['priority']}. {c['description']}\n"
            
            prompt += (
                "\nProvide a highly concise, authoritative AI mitigation strategy (max 3 sentences). "
                "Suggest shifting the time, changing the line blocked, or prioritizing specific trains. "
                "Do not use markdown formatting. Be direct."
            )
            
            messages = [{"role": "user", "content": prompt}]
            ai_response = llm_router.generate(messages, max_tokens=150, temperature=0.2)
            ai_mitigation = ai_response.content
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AI Mitigation failed: {e}")
            ai_mitigation = "AI Mitigation Engine offline. Fallback to manual controller judgement."

    return {
        "proposed_block": {
            "date": block_date.isoformat(),
            "start": block_start,
            "end": block_end,
            "line": line,
        },
        "has_conflicts": len(conflicts) > 0,
        "total_conflicts": len(conflicts),
        "critical_conflicts": sum(1 for c in conflicts if c["is_high_priority"]),
        "conflicts": conflicts,
        "ai_mitigation": ai_mitigation,
    }
