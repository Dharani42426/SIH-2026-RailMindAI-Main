# 🚀 RailMind AI Backend — Full Implementation Plan

## Current State
**Every file in the backend is empty** — the folder structure exists but contains zero code. We need to build the entire FastAPI backend from the ground up.

## Proposed Build Order

We'll build in **6 phases**, bottom-up (dependencies first → features last):

---

## Phase 1: Foundation (Config + Database Models)
*Everything else depends on this*

### [MODIFY] [config.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/config.py)
- Pydantic `Settings` class with DATABASE_URL, REDIS_URL, app config
- Environment variable loading via `.env`

### [MODIFY] [requirements.txt](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/requirements.txt)
- FastAPI, uvicorn, SQLAlchemy, asyncpg, pydantic, redis
- XGBoost, scikit-learn, PyTorch, ortools, numpy, pandas
- python-socketio, python-dotenv

### [MODIFY] [models/__init__.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/__init__.py)
- SQLAlchemy `Base`, engine, session factory

### [MODIFY] [models/corridor.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/corridor.py)
- `RailwaySection` ORM model (maps to `railway_sections` table from strategy doc)

### [MODIFY] [models/asset.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/asset.py)
- `RailwayAsset` ORM model (track, signal, OHE equipment)

### [MODIFY] [models/maintenance_task.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/maintenance_task.py)
- `MaintenanceTask` ORM model (unified TMS+SMMS+TDMS defects)

### [MODIFY] [models/train_schedule.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/train_schedule.py)
- `TrainSchedule` ORM model (COA timetable data)

### [MODIFY] [models/block_plan.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/block_plan.py)
- `BlockPlan`, `BlockWindow`, `BlockTaskAssignment`, `ConflictLog` ORM models

### [MODIFY] [models/user.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/models/user.py)
- `User` model with roles (Controller, PWI, DEN)

---

## Phase 2: Synthetic Data & Seed Scripts
*We need realistic data before building AI services*

### [MODIFY] Sample data JSON files:
- [tms_defects.json](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/sample_data/tms_defects.json) — 80+ realistic track defects
- [sms_signals.json](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/sample_data/sms_signals.json) — 50+ signal maintenance tasks
- [tdms_ohe.json](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/sample_data/tdms_ohe.json) — 40+ OHE/power tasks
- [coa_timetable.json](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/sample_data/coa_timetable.json) — 150+ train schedules (Mumbai Division)
- [sections.json](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/sample_data/sections.json) — Real IR section data (CSMT-KYN, KYN-KAS, etc.)

### [MODIFY] Seed scripts:
- [seed_corridor.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/seed_corridor.py) — Load sections into DB
- [seed_assets.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/seed_assets.py) — Generate 300+ railway assets
- [seed_maintenance.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/seed_maintenance.py) — Generate 200+ maintenance tasks
- [seed_timetable.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/seed_timetable.py) — Load train schedules

### [NEW] [data/init.sql](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/data/init.sql)
- SQL schema for Docker init (creates all 8 tables)

---

## Phase 3: AI Services (Core Intelligence)
*The 6 AI engines — Priority 1 first*

### 🔴 Priority 1 — CORE

#### [MODIFY] [services/data_integrator.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/data_integrator.py)
- Fetches and merges data from all 4 sources (TMS+SMMS+TDMS+COA)
- Builds unified task list + constraint matrix

#### [MODIFY] [services/criticality_scorer.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/criticality_scorer.py)
- XGBoost model training on synthetic data
- 10 features: severity, days_overdue, traffic_density, safety_impact, etc.
- Predicts criticality score (0-100) for each task
- Save/load model as `.pkl`

#### [MODIFY] [services/conflict_resolver.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/conflict_resolver.py)
- CSP solver to detect train-block conflicts
- Checks: train clashes, dept overlaps, resource conflicts, adjacent conflicts
- Suggests alternative time windows

#### [MODIFY] [services/block_optimizer.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/block_optimizer.py)
- Google OR-Tools CP-SAT solver
- Decision variables: `x[i][d][s]` (task i → day d, slot s), `merge[i][j]`
- Objective: minimize block time + critical delay penalty − integrated block bonus + train disruption penalty
- 12 hard constraints (as specified in strategy doc)
- Target solve time: < 5 seconds

### 🟡 Priority 2 — DIFFERENTIATORS

#### [MODIFY] [services/multi_agent.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/multi_agent.py)
- 3 department agents (ENGG, S&T, TRD) with utility functions
- 4-round negotiation protocol
- Nash Equilibrium arbitration
- Rule-based approach (practical for SIH demo)

#### [MODIFY] [services/predictive_engine.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/predictive_engine.py)
- LSTM model for time-series asset health prediction
- Input: historical health scores over time
- Output: predicted failure date + degradation curve
- Save/load model as `.pt`

### 🟢 Priority 3 — EXTRAS

#### [MODIFY] [services/anomaly_detector.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/anomaly_detector.py)
- Isolation Forest for unusual asset behavior detection

#### [MODIFY] [services/nlp_processor.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/nlp_processor.py)
- Parse natural language commands → structured API calls
- Pattern matching + optional LLM API integration

#### [MODIFY] [services/notification_service.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/services/notification_service.py)
- Alert system for critical events (block conflicts, overdue tasks)

---

## Phase 4: API Routes
*REST endpoints that the frontend will call*

### [MODIFY] [api/__init__.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/__init__.py)
- Main API router with `/api/v1` prefix

### [MODIFY] API Route files:
- [routes/maintenance.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/maintenance.py) — CRUD for maintenance tasks + criticality ranking
- [routes/timetable.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/timetable.py) — Train schedules + corridor availability
- [routes/blocks.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/blocks.py) — Block plan CRUD + approval
- [routes/optimizer.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/optimizer.py) — ⭐ Generate plan, re-optimize, what-if, explain
- [routes/analytics.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/analytics.py) — KPI metrics + before/after comparison
- [routes/notifications.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/notifications.py) — Alert endpoints
- [routes/nlp.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/routes/nlp.py) — NLP command processing

### [MODIFY] WebSocket:
- [api/websockets/live_updates.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/api/websockets/live_updates.py) — Real-time block status stream

---

## Phase 5: App Entry Point + Docker
*Wire everything together*

### [MODIFY] [main.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/main.py)
- FastAPI app with CORS, lifespan events
- Include all routers, mount WebSocket
- Database table creation on startup
- Data seeding endpoint

### [MODIFY] [Dockerfile](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/Dockerfile)
- Python 3.11 slim image, install requirements, expose 8000

### [MODIFY] [docker-compose.yml](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/docker-compose.yml)
- PostgreSQL + Redis + Backend services (from strategy doc)

### [MODIFY] [.env.example](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/.env.example)
- Template environment variables

---

## Phase 6: Testing
*Verify everything works*

### [MODIFY] Test files:
- [tests/test_criticality.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/tests/test_criticality.py)
- [tests/test_optimizer.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/tests/test_optimizer.py)
- [tests/test_conflict.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/tests/test_conflict.py)
- [tests/test_api.py](file:///c:/Users/danni/OneDrive/Desktop/SIH%202026/railmind-ai/backend/tests/test_api.py)

---

## Verification Plan

### Automated Tests
```bash
cd railmind-ai/backend
python -m pytest tests/ -v
```

### Manual Verification
1. Run `uvicorn main:app --reload` and verify Swagger docs at `http://localhost:8000/docs`
2. Test `/api/v1/optimizer/generate-plan` with sample section
3. Verify XGBoost model trains and produces criticality scores
4. Verify OR-Tools optimizer generates valid block plans within 5s
5. Check all API endpoints return correct data

---

> [!IMPORTANT]
> This is a **large build** (~40 files). Shall I proceed with building all 6 phases sequentially? Or would you like me to focus on specific phases first?

> [!NOTE]
> The backend will use **SQLite** for local development (no Docker needed to test). The PostgreSQL config is ready for Docker deployment.
