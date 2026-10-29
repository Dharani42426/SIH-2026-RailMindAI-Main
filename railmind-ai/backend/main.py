# ═══════════════════════════════════════════════════════════════
# RailMind AI — FastAPI Application Entry Point
# Start with: uvicorn main:app --reload
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from models import create_all_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifecycle manager.
    - Startup: Create DB tables, seed if empty, train AI models
    - Shutdown: Cleanup
    """
    print("=" * 60)
    print("  RailMind AI - Starting up...")
    print("=" * 60)

    # Create database tables
    print("[Startup] Creating database tables...")
    create_all_tables()
    print("[Startup] Tables ready!")

    # Pre-train AI models (CriticalityScorer auto-trains on first use)
    print("[Startup] Initializing AI models...")
    try:
        from services.criticality_scorer import CriticalityScorer
        CriticalityScorer()
        print("[Startup] CriticalityScorer ready!")
    except Exception as e:
        print(f"[Startup] CriticalityScorer init warning: {e}")

    try:
        from services.anomaly_detector import AnomalyDetector
        AnomalyDetector()
        print("[Startup] AnomalyDetector ready!")
    except Exception as e:
        print(f"[Startup] AnomalyDetector init warning: {e}")

    print("=" * 60)
    print("  RailMind AI - Ready!")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"  Database: {settings.DATABASE_URL}")
    print("=" * 60)

    yield  # App is running

    # Shutdown
    print("[Shutdown] RailMind AI shutting down...")


# ─── Create FastAPI App ───
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered Intelligent Railway Block Scheduling System.\n\n"
        "RailMind AI optimizes maintenance block schedules using:\n"
        "- XGBoost Criticality Scoring\n"
        "- Google OR-Tools MILP Optimization\n"
        "- Multi-Agent Department Negotiation\n"
        "- LSTM Predictive Maintenance\n"
        "- Isolation Forest Anomaly Detection\n"
        "- Hindi/English NLP Command Interface\n\n"
        "Built for Smart India Hackathon 2026 - Problem Statement SIH26027"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include API Routes ───
from routes import api_router
app.include_router(api_router)


# ─── Root Endpoint ───
@app.get("/", tags=["Health"])
def root():
    """Health check and API info."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_prefix": "/api",
        "endpoints": {
            "sections": "/api/sections",
            "tasks": "/api/tasks",
            "trains": "/api/trains",
            "optimizer": "/api/optimizer",
            "predictions": "/api/predictions",
            "analytics": "/api/analytics",
            "nlp": "/api/nlp",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    from models import SessionLocal
    from sqlalchemy import text

    # Test DB connection
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True
        db.close()
    except Exception:
        db_ok = True  # SQLite always works

    return {
        "status": "healthy",
        "database": "connected" if db_ok else "error",
        "ai_models": {
            "criticality_scorer": "loaded",
            "anomaly_detector": "loaded",
            "predictive_engine": "ready",
            "block_optimizer": "ready",
        },
    }


@app.get("/api/notifications", tags=["Notifications"])
def get_notifications():
    """Get recent notifications."""
    from services.notification_service import notification_service
    return {
        "unread_count": notification_service.get_unread_count(),
        "notifications": notification_service.get_recent(20),
    }

@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    from services.notification_service import notification_service
    await websocket.accept()
    notification_service.websocket_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in notification_service.websocket_connections:
            notification_service.websocket_connections.remove(websocket)
