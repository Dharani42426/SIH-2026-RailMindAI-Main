# ═══════════════════════════════════════════════════════════════
# RailMind AI — Maintenance Task Routes
# CRUD + AI-scored task endpoints
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from models.maintenance_task import MaintenanceTask
from schemas import TaskCreate, TaskResponse, TaskWithCriticality

router = APIRouter(prefix="/tasks", tags=["Maintenance Tasks"])


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    section_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None, description="ENGG/SNT/TRD"),
    severity: Optional[str] = Query(None, description="CRITICAL/HIGH/MEDIUM/LOW"),
    status: Optional[str] = Query(None, description="PENDING/SCHEDULED/COMPLETED"),
    overdue_only: bool = Query(False),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """List maintenance tasks with filters."""
    query = db.query(MaintenanceTask)

    if section_id:
        query = query.filter(MaintenanceTask.section_id == section_id)
    if department:
        query = query.filter(MaintenanceTask.department == department.upper())
    if severity:
        query = query.filter(MaintenanceTask.severity == severity.upper())
    if status:
        query = query.filter(MaintenanceTask.status == status.upper())
    if overdue_only:
        query = query.filter(MaintenanceTask.is_overdue == True)

    tasks = query.order_by(
        MaintenanceTask.criticality_score.desc().nullslast(),
        MaintenanceTask.due_date.asc(),
    ).limit(limit).all()

    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/critical", response_model=list[TaskWithCriticality])
def get_critical_tasks(
    section_id: Optional[int] = Query(None),
    top_n: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """
    Get the top N most critical tasks ranked by AI criticality score.
    Scores tasks if they haven't been scored yet.
    """
    from services.criticality_scorer import CriticalityScorer

    # Score all tasks if needed
    query = db.query(MaintenanceTask).filter(
        MaintenanceTask.status.in_(["PENDING", "SCHEDULED"])
    )
    if section_id:
        query = query.filter(MaintenanceTask.section_id == section_id)

    tasks = query.all()

    # Check if scoring is needed
    unscored = [t for t in tasks if t.criticality_score is None]
    if unscored and section_id:
        scorer = CriticalityScorer()
        scorer.score_all_tasks(db, section_id, update_db=True)
        # Re-fetch
        tasks = query.all()

    # Sort by criticality
    tasks.sort(key=lambda t: float(t.criticality_score or 0), reverse=True)
    top_tasks = tasks[:top_n]

    result = []
    for rank, task in enumerate(top_tasks, 1):
        data = TaskWithCriticality.model_validate(task)
        data.criticality_rank = rank
        result.append(data)

    return result


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by ID."""
    task = db.query(MaintenanceTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new maintenance task."""
    existing = db.query(MaintenanceTask).filter_by(
        task_code=task.task_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Task '{task.task_code}' already exists")

    db_task = MaintenanceTask(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return TaskResponse.model_validate(db_task)


@router.post("/{task_id}/score")
def score_task(task_id: int, db: Session = Depends(get_db)):
    """
    Run AI criticality scoring on a single task.
    Returns the score and feature breakdown.
    """
    from services.criticality_scorer import CriticalityScorer
    from services.data_integrator import DataIntegrator

    task = db.query(MaintenanceTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    integrator = DataIntegrator(db)
    features = integrator.enrich_task_features(task)

    scorer = CriticalityScorer()
    score = scorer.predict_score(features)

    # Update DB
    task.criticality_score = score
    db.commit()

    return {
        "task_code": task.task_code,
        "criticality_score": score,
        "features": features,
        "feature_importance": scorer.get_feature_importance()[:10],
    }


@router.get("/stats/summary")
def get_task_stats(
    section_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Get task statistics summary."""
    query = db.query(MaintenanceTask)
    if section_id:
        query = query.filter(MaintenanceTask.section_id == section_id)

    tasks = query.all()
    total = len(tasks)

    by_severity = {}
    by_department = {}
    by_status = {}
    for t in tasks:
        by_severity[t.severity] = by_severity.get(t.severity, 0) + 1
        by_department[t.department] = by_department.get(t.department, 0) + 1
        by_status[t.status] = by_status.get(t.status, 0) + 1

    return {
        "total": total,
        "by_severity": by_severity,
        "by_department": by_department,
        "by_status": by_status,
        "overdue": sum(1 for t in tasks if t.is_overdue),
        "avg_criticality": round(
            sum(float(t.criticality_score or 0) for t in tasks) / max(1, total), 2
        ),
    }
