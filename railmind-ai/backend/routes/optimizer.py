# ═══════════════════════════════════════════════════════════════
# RailMind AI — Optimizer Routes
# AI block plan generation and what-if simulation
# THE MAIN SHOW for SIH judges
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional

from models import get_db
from models.block_plan import BlockPlan, BlockTaskAssignment
from models.maintenance_task import MaintenanceTask
from models.maintenance_request import MaintenanceRequest
from schemas import GeneratePlanRequest, WhatIfRequest, BlockPlanResponse

router = APIRouter(prefix="/optimizer", tags=["AI Optimizer"])


def _format_blocks(blocks: list) -> list:
    """Format block dicts for API response."""
    formatted = []
    for b in blocks:
        formatted.append({
            "block_code": b["block_code"],
            "date": b["block_date"].isoformat() if hasattr(b["block_date"], 'isoformat') else str(b["block_date"]),
            "start_time": b["start_time"].strftime("%H:%M") if hasattr(b["start_time"], 'strftime') else str(b["start_time"]),
            "end_time": b["end_time"].strftime("%H:%M") if hasattr(b["end_time"], 'strftime') else str(b["end_time"]),
            "duration_hrs": b["duration_hrs"],
            "block_type": b["block_type"],
            "line": b["line_blocked"],
            "is_integrated": b["is_integrated"],
            "departments": b["departments"],
            "km_range": f"{b['km_from']:.1f}-{b['km_to']:.1f}",
            "tasks_count": b["task_count"],
            "tasks": [t["task"].task_code for t in b["tasks"]],
        })
    return formatted


@router.post("/generate")
def generate_block_plan(
    request: GeneratePlanRequest,
    db: Session = Depends(get_db),
):
    """
    Generate an AI-optimized block schedule.

    This is the CORE endpoint that runs the full AI pipeline:
    1. Data Integration (merge TMS+SMMS+TDMS+COA)
    2. Criticality Scoring (XGBoost)
    3. Multi-Agent Negotiation (3 dept agents)
    4. Block Optimization (OR-Tools CP-SAT)
    5. Safety Gate Validation (ConflictResolver)
    6. Plan saved to database (only if safe)

    Returns the complete plan with explanations and safety report.
    """
    from services.block_optimizer import BlockOptimizer
    from services.multi_agent import MultiAgentNegotiator
    from services.notification_service import notification_service

    end_date = request.end_date
    if end_date is None:
        days = 7 if request.plan_type == "WEEKLY" else 30
        end_date = request.start_date + timedelta(days=days - 1)

    # Step 1: Run multi-agent negotiation to get department priority weights
    negotiation_weights = None
    negotiation_summary = None
    try:
        negotiator = MultiAgentNegotiator(db)
        neg_result = negotiator.negotiate(request.section_id, request.start_date)
        if not neg_result.get("error"):
            # Convert agent utilities to relative weights for the optimizer
            utilities = neg_result.get("agent_utilities", {})
            if utilities:
                max_util = max(utilities.values()) if utilities.values() else 1
                negotiation_weights = {
                    dept: max(0.5, util / max(1, max_util))
                    for dept, util in utilities.items()
                }
            negotiation_summary = {
                "departments_negotiated": list(utilities.keys()),
                "utilities": utilities,
                "is_balanced": neg_result.get("is_balanced", False),
                "integrated_opportunities": len(neg_result.get("integrated_blocks", [])),
            }
    except Exception as e:
        print(f"[Optimizer] Negotiation warning: {e}")

    # Step 2: Run optimization with negotiation weights
    optimizer = BlockOptimizer(db)
    try:
        result = optimizer.generate_plan(
            section_id=request.section_id,
            start_date=request.start_date,
            end_date=end_date,
            plan_type=request.plan_type,
            negotiation_weights=negotiation_weights,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Send notification
    if result.get("plan"):
        notification_service.alert_plan_generated(result["plan"], result["stats"])

    # Format response
    blocks_formatted = _format_blocks(result.get("blocks", []))

    return {
        "plan_id": result["plan"].id if result.get("plan") else None,
        "plan_code": result["plan"].plan_code if result.get("plan") else None,
        "status": result["plan"].status if result.get("plan") else result.get("stats", {}).get("solver_status", "NO_TASKS"),
        "solve_time_seconds": result.get("solve_time_seconds", 0),
        "stats": result.get("stats", {}),
        "blocks": blocks_formatted,
        "explanations": result.get("explanations", []),
        "safety_report": result.get("safety_report", {}),
        "negotiation": negotiation_summary,
    }


@router.get("/plans")
def list_plans(
    section_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None, description="DRAFT/APPROVED/ACTIVE/COMPLETED"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """List all block plans."""
    from sqlalchemy.orm import joinedload
    from models.block_plan import BlockWindow, BlockTaskAssignment

    query = db.query(BlockPlan).options(
        joinedload(BlockPlan.block_windows).joinedload(BlockWindow.task_assignments).joinedload(BlockTaskAssignment.task)
    )

    if section_id:
        query = query.filter(BlockPlan.section_id == section_id)
    if status:
        query = query.filter(BlockPlan.status == status.upper())

    plans = query.order_by(BlockPlan.generated_at.desc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "plan_code": p.plan_code,
            "plan_type": p.plan_type,
            "section_id": p.section_id,
            "date_range": f"{p.plan_start_date} to {p.plan_end_date}",
            "total_blocks": p.total_blocks,
            "total_block_hrs": float(p.total_block_hrs) if p.total_block_hrs else 0,
            "utilization_pct": float(p.utilization_pct) if p.utilization_pct else 0,
            "tasks_scheduled": p.tasks_scheduled,
            "status": p.status,
            "generated_at": p.generated_at.isoformat() if p.generated_at else None,
            "generated_by": p.generated_by,
            "optimization_score": float(p.optimization_score) if p.optimization_score else None,
            "conflicts_resolved": p.conflicts_resolved,
            "safety_report_data": p.safety_report_data,
            "rejection_reason": getattr(p, 'rejection_reason', None),
            "block_windows": [
                {
                    "block_code": b.block_code,
                    "block_date": b.block_date.isoformat() if b.block_date else None,
                    "start_time": b.start_time.isoformat() if b.start_time else None,
                    "end_time": b.end_time.isoformat() if b.end_time else None,
                    "duration_hrs": float(b.duration_hrs),
                    "km_from": float(b.km_from),
                    "km_to": float(b.km_to),
                    "block_type": b.block_type.value if hasattr(b.block_type, 'value') else b.block_type,
                    "line_blocked": b.line_blocked.value if hasattr(b.line_blocked, 'value') else b.line_blocked,
                    "is_integrated": b.is_integrated,
                    "departments": b.departments,
                    "ai_explanation": b.ai_explanation,
                    "task_assignments": [
                        {
                            "sequence_order": ta.sequence_order,
                            "start_offset_min": ta.start_offset_min,
                            "duration_min": ta.duration_min,
                            "task": {
                                "task_code": ta.task.task_code,
                                "work_type": ta.task.task_type,
                                "department": ta.task.department.value if hasattr(ta.task.department, 'value') else ta.task.department,
                                "km_from": float(ta.task.km_from),
                                "km_to": float(ta.task.km_to)
                            } if ta.task else {}
                        }
                        for ta in b.task_assignments
                    ]
                }
                for b in p.block_windows
            ]
        }
        for p in plans
    ]


@router.post("/plans/{plan_id}/approve")
def approve_plan(
    plan_id: int,
    approved_by: str = Query(..., description="Controller name/ID"),
    db: Session = Depends(get_db),
):
    """Approve a block plan (Controller action)."""
    from datetime import datetime
    from models.block_plan import BlockWindow
    from services.conflict_resolver import ConflictResolver
    from fastapi.responses import JSONResponse

    plan = db.query(BlockPlan).filter_by(id=plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.status != "DRAFT":
        raise HTTPException(status_code=400, detail=f"Plan is already {plan.status}")

    # Reconstruct blocks for safety validation
    blocks = db.query(BlockWindow).filter_by(plan_id=plan.id).all()
    if blocks:
        blocks_by_date = {}
        for b in blocks:
            if b.block_date not in blocks_by_date:
                blocks_by_date[b.block_date] = []
            blocks_by_date[b.block_date].append(b)

        resolver = ConflictResolver(db)
        violations = []
        total_checks = 0

        for b_date, day_blocks in blocks_by_date.items():
            proposed = []
            for b in day_blocks:
                proposed.append({
                    "start_time": b.start_time,
                    "end_time": b.end_time,
                    "line": b.line_blocked,
                    "block_code": b.block_code,
                    "section_id": b.section_id,
                    "tasks": []  # Tasks not required for train clash validation
                })

            report = resolver.validate_block_plan(plan.section_id, b_date, proposed)
            total_checks += 1
            
            if not report["valid"]:
                for conflict in report["conflicts"]:
                    if conflict["type"] == "TRAIN_CLASH":
                        violations.append({
                            "date": b_date.isoformat() if hasattr(b_date, 'isoformat') else str(b_date),
                            "type": conflict["type"],
                            "description": conflict["description"]
                        })

        if len(violations) > 0:
            # Plan is no longer safe due to timetable changes
            plan.status = "REJECTED"
            plan.rejection_reason = "Safety re-validation failed during approval."
            
            safety_report_dict = {
                "safe": False,
                "violations": violations,
                "checks_passed": total_checks
            }
            plan.safety_report_data = safety_report_dict
            db.commit()
            
            return JSONResponse(
                status_code=409,
                content={
                    "status": "BLOCKED",
                    "reason": "Safety conflicts detected against current train schedules.",
                    "safety_report": safety_report_dict
                }
            )
            
        else:
            # Safe! Save the passing safety report
            plan.safety_report_data = {
                "safe": True,
                "violations": [],
                "checks_passed": total_checks
            }

    plan.status = "APPROVED"
    plan.approved_by = approved_by
    plan.approved_at = datetime.now()
    
    # Update tasks and requests to SCHEDULED
    for block in blocks:
        block.status = "ACTIVE"
        for assignment in block.task_assignments:
            task = assignment.task
            if task:
                task.status = "SCHEDULED"
                # Find associated request and update it
                req = db.query(MaintenanceRequest).filter(MaintenanceRequest.maintenance_task_id == task.id).first()
                if req:
                    req.status = "SCHEDULED"

    db.commit()

    return {"message": f"Plan {plan.plan_code} approved by {approved_by}", "status": "APPROVED"}

@router.post("/plans/{plan_id}/reject")
def reject_plan(
    plan_id: int,
    reason: str = Query(..., description="Rejection reason"),
    db: Session = Depends(get_db),
):
    """Reject a block plan with reason."""
    plan = db.query(BlockPlan).filter_by(id=plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.status = "REJECTED"
    plan.rejection_reason = reason
    db.commit()

    return {"message": f"Plan {plan.plan_code} rejected", "reason": reason}


@router.post("/negotiate")
def run_negotiation(
    section_id: int = Query(...),
    target_date: date = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Run multi-agent negotiation for a section.
    3 department AI agents negotiate for block windows.
    Returns the negotiation log and agreed allocations.
    """
    from services.multi_agent import MultiAgentNegotiator

    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    negotiator = MultiAgentNegotiator(db)
    result = negotiator.negotiate(section_id, target_date)

    # Format allocated tasks
    formatted_allocations = {}
    for dept, tasks in result.get("allocated_tasks", {}).items():
        formatted_allocations[dept] = [
            {
                "task_code": t.task_code if hasattr(t, 'task_code') else str(t),
                "task_type": t.task_type if hasattr(t, 'task_type') else "",
                "severity": t.severity if hasattr(t, 'severity') else "",
                "criticality_score": float(t.criticality_score) if hasattr(t, 'criticality_score') and t.criticality_score else None,
            }
            for t in tasks
        ]

    return {
        "section_id": section_id,
        "date": target_date.isoformat(),
        "allocated_tasks": formatted_allocations,
        "integrated_blocks": [
            {
                "departments": ib["departments"],
                "tasks": [t.task_code for t in ib["tasks"]],
                "km_overlap": ib["km_overlap"],
                "savings_hours": ib.get("savings_hours", 0),
                "description": ib["description"],
            }
            for ib in result.get("integrated_blocks", [])
        ],
        "agent_utilities": result.get("agent_utilities", {}),
        "is_balanced": result.get("is_balanced", False),
        "total_rounds": result.get("total_rounds", 4),
        "negotiation_log": result.get("negotiation_log", []),
    }


@router.post("/what-if")
def what_if_simulation(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
):
    """
    What-If scenario simulation.

    Takes an existing plan and a list of changes, re-runs optimization
    with the modifications, and returns the comparison.

    Supported change actions:
    - {"action": "remove_train", "train_no": "12124"}
    - {"action": "add_window", "start_time": "14:00", "end_time": "15:30"}
    - {"action": "change_task_severity", "task_code": "TMS-...", "severity": "CRITICAL"}
    - {"action": "remove_window", "start_time": "10:00", "end_time": "11:00"}
    """
    from services.block_optimizer import BlockOptimizer
    from models.block_plan import BlockWindow
    from models.train_schedule import TrainSchedule
    from models.maintenance_task import MaintenanceTask

    # Load original plan
    plan = db.query(BlockPlan).filter_by(id=request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    original_blocks = db.query(BlockWindow).filter_by(plan_id=plan.id).all()
    original_summary = {
        "plan_code": plan.plan_code,
        "total_blocks": plan.total_blocks,
        "total_block_hrs": float(plan.total_block_hrs or 0),
        "tasks_scheduled": plan.tasks_scheduled,
        "utilization_pct": float(plan.utilization_pct or 0),
    }

    # Apply changes
    change_descriptions = []
    for change in request.changes:
        action = change.get("action", "")

        if action in ["remove_train", "cancel_train"]:
            train_no = change.get("train_no", "")
            train = db.query(TrainSchedule).filter_by(
                train_no=train_no, section_id=plan.section_id
            ).first()
            if train:
                db.delete(train)
                change_descriptions.append(f"Removed train {train_no} ({train.train_name})")

        elif action == "delay_train":
            train_no = change.get("train_no", "")
            delay_mins = int(change.get("delay_minutes", 0))
            train = db.query(TrainSchedule).filter_by(
                train_no=train_no, section_id=plan.section_id
            ).first()
            if train and delay_mins > 0:
                from datetime import datetime, timedelta
                dummy_date = datetime.today()
                entry_dt = datetime.combine(dummy_date, train.entry_time) + timedelta(minutes=delay_mins)
                exit_dt = datetime.combine(dummy_date, train.exit_time) + timedelta(minutes=delay_mins)
                train.entry_time = entry_dt.time()
                train.exit_time = exit_dt.time()
                train.avg_delay_min = (train.avg_delay_min or 0) + delay_mins
                change_descriptions.append(f"Delayed train {train_no} by {delay_mins} mins")

        elif action == "add_train":
            from datetime import datetime
            train_no = change.get("train_no", "SPECIAL-01")
            entry_str = change.get("entry_time", "12:00")
            exit_str = change.get("exit_time", "14:00")
            new_train = TrainSchedule(
                train_no=train_no,
                train_name=change.get("train_name", "Special Train"),
                train_type="EXPRESS",
                priority=2,
                section_id=plan.section_id,
                direction="BOTH",
                entry_km=0.0,
                exit_km=54.0,
                entry_time=datetime.strptime(entry_str, "%H:%M").time(),
                exit_time=datetime.strptime(exit_str, "%H:%M").time(),
                is_special=True
            )
            db.add(new_train)
            change_descriptions.append(f"Added special train {train_no} ({entry_str}-{exit_str})")

        elif action == "add_critical_task":
            from datetime import datetime
            task_code = change.get("task_code", "EMERGENCY-001")
            new_task = MaintenanceTask(
                task_code=task_code,
                source_system="TMS",
                department="ENGG",
                section_id=plan.section_id,
                km_from=float(change.get("km_from", 0)),
                km_to=float(change.get("km_to", 5)),
                task_type="Emergency Repair",
                severity="CRITICAL",
                detected_date=datetime.today().date(),
                due_date=datetime.today().date(),
                estimated_hours=float(change.get("duration", 2.0)),
                block_type_required="TRAFFIC",
                line_affected="BOTH",
                status="PENDING"
            )
            db.add(new_task)
            change_descriptions.append(f"Injected emergency critical task {task_code} ({new_task.km_from}-{new_task.km_to} KM)")

        elif action == "change_task_severity":
            task_code = change.get("task_code", "")
            new_severity = change.get("severity", "HIGH")
            task = db.query(MaintenanceTask).filter_by(task_code=task_code).first()
            if task:
                old_sev = task.severity
                task.severity = new_severity.upper()
                change_descriptions.append(
                    f"Changed {task_code} severity: {old_sev} → {new_severity.upper()}"
                )

        else:
            change_descriptions.append(f"Unsupported action: {action}")

    db.flush()

    # Re-run optimization with modified data
    optimizer = BlockOptimizer(db)
    try:
        modified_result = optimizer.generate_plan(
            section_id=plan.section_id,
            start_date=plan.plan_start_date,
            end_date=plan.plan_end_date,
            plan_type=plan.plan_type,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Re-optimization failed: {str(e)}")

    modified_blocks = _format_blocks(modified_result.get("blocks", []))
    modified_stats = modified_result.get("stats", {})

    # Rollback the changes (this is a simulation, not permanent)
    db.rollback()

    # Generate explanation using LLM
    try:
        from services.llm_providers import create_llm_router_from_settings
        import json
        llm_router = create_llm_router_from_settings()
        
        prompt = f"""
        Act as an expert Railway Operations AI. I just ran a What-If simulation.
        Original Plan: {original_summary['total_blocks']} blocks, {original_summary['tasks_scheduled']} tasks scheduled.
        Changes Injected: {change_descriptions}
        Modified Plan: {modified_stats.get('total_blocks', 0)} blocks, {modified_stats.get('tasks_scheduled', 0)} tasks scheduled, Utilization: {modified_stats.get('utilization_pct', 0)}%.
        Safety Report: {json.dumps(modified_result.get('safety_report', {}))}

        Provide a very concise, professional strategic assessment (max 3 sentences) of how these perturbations affected the operational schedule. Focus on the variance and safety.
        """
        
        response = llm_router.generate([{"role": "user", "content": prompt}])
        explanation_text = response.content.strip()
    except Exception as e:
        import logging
        logger = logging.getLogger("railmind.optimizer")
        logger.warning(f"What-If LLM generation failed, falling back to static string. Error: {e}")
        explanation_text = (
            f"What-if simulation applied {len(change_descriptions)} change(s). "
            f"Modified plan has {modified_stats.get('total_blocks', 0)} blocks "
            f"scheduling {modified_stats.get('tasks_scheduled', 0)} tasks "
            f"(original: {original_summary['total_blocks']} blocks, "
            f"{original_summary['tasks_scheduled']} tasks)."
        )

    return {
        "original_plan": original_summary,
        "modified_plan": {
            "total_blocks": modified_stats.get("total_blocks", 0),
            "total_block_hrs": modified_stats.get("total_block_hours", 0),
            "tasks_scheduled": modified_stats.get("tasks_scheduled", 0),
            "utilization_pct": modified_stats.get("utilization_pct", 0),
        },
        "changes_applied": change_descriptions,
        "modified_blocks": modified_blocks,
        "affected_tasks": modified_stats.get("tasks_total", 0),
        "explanation": explanation_text,
        "safety_report": modified_result.get("safety_report", {}),
    }
