# ═══════════════════════════════════════════════════════════════
# RailMind AI — Prediction Routes
# Predictive maintenance + anomaly detection endpoints
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db
from models.asset import RailwayAsset

router = APIRouter(prefix="/predictions", tags=["Predictive Maintenance"])


@router.get("/section/{section_id}")
def predict_section_assets(
    section_id: int,
    update_tasks: bool = Query(True, description="Update task failure dates"),
    db: Session = Depends(get_db),
):
    """
    Run predictive analysis for ALL assets in a section.
    Returns predicted failure dates and remaining useful life.
    """
    from services.predictive_engine import PredictiveEngine

    engine = PredictiveEngine()
    predictions = engine.predict_all_assets(db, section_id, update_tasks=update_tasks)

    if not predictions:
        raise HTTPException(status_code=404, detail="No assets found for this section")

    return {
        "section_id": section_id,
        "total_assets": len(predictions),
        "model_used": predictions[0]["model_used"] if predictions else "N/A",
        "risk_summary": {
            "critical": sum(1 for p in predictions if p["risk_level"] == "CRITICAL"),
            "high": sum(1 for p in predictions if p["risk_level"] == "HIGH"),
            "medium": sum(1 for p in predictions if p["risk_level"] == "MEDIUM"),
            "low": sum(1 for p in predictions if p["risk_level"] == "LOW"),
        },
        "predictions": predictions[:20],  # Top 20 riskiest
    }


@router.get("/asset/{asset_id}")
def predict_single_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """
    Predict remaining useful life for a single asset.
    Returns health trajectory for next 12 months.
    """
    from services.predictive_engine import PredictiveEngine
    from models.corridor import RailwaySection

    asset = db.query(RailwayAsset).filter_by(id=asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    section = db.query(RailwaySection).filter_by(id=asset.section_id).first()
    is_ghat = section.is_ghat_section if section else False

    engine = PredictiveEngine()
    prediction = engine.predict_remaining_life(asset, is_ghat=is_ghat)

    return prediction


@router.get("/section/{section_id}/risk-summary")
def get_risk_summary(
    section_id: int,
    db: Session = Depends(get_db),
):
    """Get risk summary for dashboard display."""
    from services.predictive_engine import PredictiveEngine

    engine = PredictiveEngine()
    summary = engine.get_section_risk_summary(db, section_id)
    return summary


@router.get("/section/{section_id}/anomalies")
def detect_anomalies(
    section_id: int,
    db: Session = Depends(get_db),
):
    """
    Detect anomalous maintenance patterns in a section.
    Uses Isolation Forest ML model.
    """
    from services.anomaly_detector import AnomalyDetector

    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(db, section_id)

    return {
        "section_id": section_id,
        "total_anomalies": len(anomalies),
        "anomalies": anomalies,
    }
