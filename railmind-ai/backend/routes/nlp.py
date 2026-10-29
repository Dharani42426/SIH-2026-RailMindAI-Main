# ═══════════════════════════════════════════════════════════════
# RailMind AI — NLP Routes
# Natural language command endpoint for controllers
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import get_db
from schemas import NLPCommandRequest, NLPCommandResponse

router = APIRouter(prefix="/nlp", tags=["NLP Interface"])


@router.post("/command", response_model=NLPCommandResponse)
def process_nlp_command(
    request: NLPCommandRequest,
    db: Session = Depends(get_db),
):
    """
    Process a natural language command from a railway controller.

    Supports Hindi and English commands like:
    - "Show available blocks for Kalyan-Kasara section"
    - "Kalyan section mein rail fracture ka status"
    - "Top 5 critical tasks"
    - "Schedule emergency block for OHE repair"
    - "Help"

    Returns parsed intent, entities, and a natural language response.
    """
    from services.nlp_processor import NLPProcessor

    processor = NLPProcessor()
    result = processor.process_command(request.command)

    # If the intent maps to a data query, try to fetch actual data
    data = None
    try:
        if result["intent"] == "QUERY_TASKS" and result["entities"].get("section"):
            from services.data_integrator import DataIntegrator
            from models.corridor import RailwaySection

            section_code = result["entities"]["section"]
            section = db.query(RailwaySection).filter_by(
                section_code=section_code
            ).first()

            if section:
                integrator = DataIntegrator(db)
                tasks = integrator.get_pending_tasks(section.id)
                limit = result["entities"].get("limit", 10)
                data = {
                    "tasks": [
                        {
                            "code": t.task_code,
                            "type": t.task_type,
                            "severity": t.severity,
                            "due_date": t.due_date.isoformat(),
                            "criticality": float(t.criticality_score) if t.criticality_score else None,
                        }
                        for t in tasks[:limit]
                    ],
                    "total": len(tasks),
                }
                result["response_text"] += f"\n\nFound {len(tasks)} pending tasks for {section_code}."

        elif result["intent"] == "STATUS" and result["entities"].get("section"):
            from services.data_integrator import DataIntegrator
            from models.corridor import RailwaySection

            section_code = result["entities"]["section"]
            section = db.query(RailwaySection).filter_by(
                section_code=section_code
            ).first()

            if section:
                integrator = DataIntegrator(db)
                health = integrator.get_asset_health_summary(section.id)
                data = health
                result["response_text"] = (
                    f"Section {section_code} ({section.section_name}):\n"
                    f"- Total assets: {health['total']}\n"
                    f"- Average health: {health['avg_health']:.1f}%\n"
                    f"- Critical assets: {health['critical']}\n"
                    f"- Status: {'GOOD' if health['avg_health'] > 75 else 'NEEDS ATTENTION'}"
                )

        elif result["intent"] in ("OPTIMIZE", "SCHEDULE") and result["entities"].get("section"):
            from services.block_optimizer import BlockOptimizer
            from models.corridor import RailwaySection
            from datetime import timedelta

            section_code = result["entities"]["section"]
            section = db.query(RailwaySection).filter_by(
                section_code=section_code
            ).first()

            if section:
                from datetime import date as date_type
                start = date_type.today() + timedelta(days=1)
                end = start + timedelta(days=6)
                optimizer = BlockOptimizer(db)
                opt_result = optimizer.generate_plan(
                    section_id=section.id,
                    start_date=start,
                    end_date=end,
                    plan_type="WEEKLY",
                )
                stats = opt_result.get("stats", {})
                data = {
                    "plan_code": opt_result["plan"].plan_code if opt_result.get("plan") else None,
                    "stats": stats,
                }
                result["response_text"] = (
                    f"AI-optimized block plan generated for {section_code}:\n"
                    f"- Total blocks: {stats.get('total_blocks', 0)}\n"
                    f"- Tasks scheduled: {stats.get('tasks_scheduled', 0)}\n"
                    f"- Utilization: {stats.get('utilization_pct', 0):.1f}%\n"
                    f"- Integrated blocks: {stats.get('integrated_blocks', 0)}\n"
                    f"Plan status: {opt_result['plan'].status if opt_result.get('plan') else 'FAILED'}"
                )

        elif result["intent"] == "PREDICT" and result["entities"].get("section"):
            from services.predictive_engine import PredictiveEngine
            from models.corridor import RailwaySection

            section_code = result["entities"]["section"]
            section = db.query(RailwaySection).filter_by(
                section_code=section_code
            ).first()

            if section:
                engine = PredictiveEngine()
                predictions = engine.predict_all_assets(db, section.id, update_tasks=False)
                risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for p in predictions:
                    risk_counts[p["risk_level"]] = risk_counts.get(p["risk_level"], 0) + 1

                data = {
                    "total_assets": len(predictions),
                    "risk_distribution": risk_counts,
                    "top_5_at_risk": predictions[:5],
                }
                result["response_text"] = (
                    f"Predictive analysis for {section_code}:\n"
                    f"- Total assets analyzed: {len(predictions)}\n"
                    f"- Critical risk: {risk_counts['CRITICAL']}\n"
                    f"- High risk: {risk_counts['HIGH']}\n"
                    f"- Medium risk: {risk_counts['MEDIUM']}\n"
                    f"- Low risk: {risk_counts['LOW']}"
                )

    except Exception as e:
        result["response_text"] += f"\n(Data fetch error: {str(e)})"

    return NLPCommandResponse(
        original_command=result["original_command"],
        intent=result["intent"],
        entities=result["entities"],
        api_action=result["api_action"],
        response_text=result["response_text"],
        ai_engine=result.get("ai_engine"),
        data=data,
    )


@router.get("/suggestions")
def get_command_suggestions():
    """Get example NLP commands for the UI autocomplete."""
    return {
        "suggestions": [
            "Show available blocks for Kalyan-Kasara section next week",
            "Top 5 critical tasks",
            "Show overdue tasks for Engineering department",
            "Status of Kasara ghat section",
            "Schedule block for track tamping on Thane-Kalyan",
            "Optimize schedule for CSMT-Dadar section",
            "Predict failures for Kasara section",
            "Kalyan section mein pending tasks dikhao",
            "OHE repair ke liye block kab available hai?",
            "Help",
        ]
    }
