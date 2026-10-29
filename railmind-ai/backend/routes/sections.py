# ═══════════════════════════════════════════════════════════════
# RailMind AI — Section Routes
# CRUD endpoints for railway sections/corridors
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from models.corridor import RailwaySection
from schemas import SectionCreate, SectionResponse

router = APIRouter(prefix="/sections", tags=["Railway Sections"])


@router.get("/", response_model=list[SectionResponse])
def list_sections(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    division: Optional[str] = Query(None, description="Filter by division"),
    ghat_only: bool = Query(False, description="Only ghat sections"),
    db: Session = Depends(get_db),
):
    """List all railway sections with optional filters."""
    query = db.query(RailwaySection)

    if zone:
        query = query.filter(RailwaySection.zone == zone)
    if division:
        query = query.filter(RailwaySection.division == division)
    if ghat_only:
        query = query.filter(RailwaySection.is_ghat_section == True)

    sections = query.order_by(RailwaySection.km_start).all()

    # Add total_km as computed property
    result = []
    for s in sections:
        data = SectionResponse.model_validate(s)
        data.total_km = s.total_km
        result.append(data)

    return result


@router.get("/{section_id}", response_model=SectionResponse)
def get_section(section_id: int, db: Session = Depends(get_db)):
    """Get a single section by ID."""
    section = db.query(RailwaySection).filter_by(id=section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    result = SectionResponse.model_validate(section)
    result.total_km = section.total_km
    return result


@router.get("/code/{section_code}", response_model=SectionResponse)
def get_section_by_code(section_code: str, db: Session = Depends(get_db)):
    """Get a section by its code (e.g., 'KYN-KAS')."""
    section = db.query(RailwaySection).filter_by(
        section_code=section_code.upper()
    ).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_code}' not found")

    result = SectionResponse.model_validate(section)
    result.total_km = section.total_km
    return result


@router.post("/", response_model=SectionResponse, status_code=201)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new railway section."""
    existing = db.query(RailwaySection).filter_by(
        section_code=section.section_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Section '{section.section_code}' already exists"
        )

    db_section = RailwaySection(**section.model_dump())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)

    result = SectionResponse.model_validate(db_section)
    result.total_km = db_section.total_km
    return result


@router.get("/{section_id}/summary")
def get_section_summary(section_id: int, db: Session = Depends(get_db)):
    """Get a comprehensive summary of a section including asset health and task counts."""
    from services.data_integrator import DataIntegrator

    section = db.query(RailwaySection).filter_by(id=section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    integrator = DataIntegrator(db)
    asset_health = integrator.get_asset_health_summary(section_id)
    tasks = integrator.get_pending_tasks(section_id)
    dept_tasks = integrator.get_tasks_by_department(section_id)

    return {
        "section": {
            "id": section.id,
            "code": section.section_code,
            "name": section.section_name,
            "km_range": f"{section.km_start}-{section.km_end}",
            "total_km": section.total_km,
            "trains_per_day": section.trains_per_day,
            "is_ghat": section.is_ghat_section,
        },
        "assets": asset_health,
        "tasks": {
            "total_pending": len(tasks),
            "by_department": {dept: len(t) for dept, t in dept_tasks.items()},
            "critical": sum(1 for t in tasks if t.severity == "CRITICAL"),
            "overdue": sum(1 for t in tasks if t.is_overdue),
        },
    }
