# ═══════════════════════════════════════════════════════════════
# RailMind AI — Routes Package
# FastAPI router registry
# ═══════════════════════════════════════════════════════════════

from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

# Import and include all route modules
from routes.sections import router as sections_router
from routes.tasks import router as tasks_router
from routes.trains import router as trains_router
from routes.optimizer import router as optimizer_router
from routes.predictions import router as predictions_router
from routes.analytics import router as analytics_router
from routes.nlp import router as nlp_router
from routes.auth import router as auth_router
from routes.requests import router as requests_router

api_router.include_router(sections_router)
api_router.include_router(tasks_router)
api_router.include_router(trains_router)
api_router.include_router(optimizer_router)
api_router.include_router(predictions_router)
api_router.include_router(analytics_router)
api_router.include_router(nlp_router)
api_router.include_router(auth_router)
api_router.include_router(requests_router)
