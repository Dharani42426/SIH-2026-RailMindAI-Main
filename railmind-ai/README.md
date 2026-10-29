<p align="center">
  <img src="https://img.shields.io/badge/🧠_RailMind_AI-v1.0.0-0A2540?style=for-the-badge&labelColor=0A2540&color=00D4AA" alt="RailMind AI" />
  <img src="https://img.shields.io/badge/SIH_2026-Problem_26027-FF6B35?style=for-the-badge" alt="SIH 2026" />
  <img src="https://img.shields.io/badge/Status-Production_Ready-00D4AA?style=for-the-badge" alt="Status" />
</p>

<h1 align="center">🧠 RailMind AI</h1>

<p align="center">
  <strong>AI-Powered Automatic Block Planning to Maximize Asset Availability for Indian Railways</strong>
</p>

<p align="center">
  <em>"From Disconnected Departments to Connected Intelligence"</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/PyTorch-2.1+-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" />
  <img src="https://img.shields.io/badge/XGBoost-2.0+-006400?style=flat-square&logo=xgboost" />
  <img src="https://img.shields.io/badge/OR--Tools-CP--SAT-4285F4?style=flat-square&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" />
</p>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [What is RailMind AI?](#-what-is-railmind-ai)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [AI/ML Pipeline — The 7-Engine Intelligence Core](#-aiml-pipeline--the-7-engine-intelligence-core)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Frontend Screens](#-frontend-screens)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Performance Benchmarks](#-performance-benchmarks)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Problem Statement

> **SIH 2026 — Problem Statement 26027**
> *Ministry of Railways / Indian Railways*

Indian Railways operates **13,000+ trains daily** across **68,000+ km** of track. Maintenance activities — track repairs, signal fixes, and overhead equipment servicing — require **traffic blocks** (temporary shutdowns of track sections). Today, block planning is:

| Challenge | Impact |
|---|---|
| **Manual & Paper-Based** | Section Controllers coordinate via phone calls between 3+ departments |
| **Conflict-Prone** | No system detects train-vs-maintenance clashes until it's too late |
| **Reactive** | Maintenance happens AFTER failures, not before |
| **Siloed** | Engineering, Signal & Telecom (S&T), and Traction (TRD) departments plan independently |
| **Suboptimal** | Available maintenance windows are underutilized by 30-40% |

**RailMind AI solves this** by replacing the manual, phone-call-driven process with an AI system that automatically generates conflict-free, optimized block schedules — coordinating all departments simultaneously.

---

## 🧠 What is RailMind AI?

> **RailMind AI is NOT a chatbot. NOT an LLM wrapper. NOT a fine-tuned ChatGPT.**

It is a **domain-specific AI system** composed of **7 specialized algorithms** — a combination of mathematical optimization, classical ML, deep learning, game theory, and NLP — all working together as an intelligent pipeline.

```
  ┌────────────────────────────────────────────────────────────────┐
  │                    THE 7 AI ENGINES                            │
  ├────────────────────────────────────────────────────────────────┤
  │                                                                │
  │  1. Data Integrator      — Unified data fusion layer           │
  │  2. Criticality Scorer   — XGBoost urgency ranking (0-100)     │
  │  3. Block Optimizer      — CP-SAT constrained optimization     │
  │  4. Conflict Resolver    — CSP train-block clash detection     │
  │  5. Multi-Agent System   — Game-theoretic dept. negotiation    │
  │  6. Predictive Engine    — LSTM failure prediction (RUL)       │
  │  7. NLP Interface        — Hindi/English command parsing       │
  │                                                                │
  │  + Anomaly Detector      — Isolation Forest outlier detection  │
  └────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔴 Core Features
- **AI-Optimized Block Scheduling** — Generates mathematically optimal maintenance windows using Google OR-Tools CP-SAT solver with 5+ hard constraints
- **Multi-Department Coordination** — 3 AI agents (ENGG, S&T, TRD) negotiate block windows using Nash Equilibrium arbitration
- **Real-Time Conflict Detection** — CSP solver instantly identifies train-vs-block clashes and suggests alternatives
- **Criticality-Based Prioritization** — XGBoost model scores every task (0-100) based on 15 engineered features

### 🟡 Differentiators
- **Predictive Maintenance** — LSTM neural network predicts asset failures before they happen (Remaining Useful Life estimation)
- **What-If Scenario Simulator** — Test block plan variations and see impact on train operations in real-time
- **Natural Language Commands** — Controllers can type/speak in Hindi or English: *"Kalyan section mein OHE repair schedule karo"*

### 🟢 Additional Intelligence
- **Anomaly Detection** — Isolation Forest detects unusual asset degradation patterns
- **Role-Based Access Control** — Department-aware dashboards (DEN, SSE, PWI, DSTE, DEE, ADMIN)
- **Approval Workflow** — Multi-stage block plan approval with safety gates
- **Real-Time Notifications** — WebSocket-powered live alerts for critical events
- **Analytics Dashboard** — KPI tracking, before/after optimization comparison, efficiency metrics

---

## 🏗 System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        RAILMIND AI ARCHITECTURE                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │   TMS   │  │  SMMS   │  │  TDMS   │  │   COA   │  Data Layer  │
│  │ (Track) │  │(Signal) │  │ (Power) │  │(Trains) │              │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘              │
│       │            │            │            │                     │
│       └────────────┴────────────┴────────────┘                     │
│                         │                                          │
│                         ▼                                          │
│         ┌──────────────────────────┐                               │
│         │   Unified Data Lake      │  Integration Layer            │
│         │  (PostgreSQL + Redis)    │                               │
│         └────────────┬─────────────┘                               │
│                      ▼                                             │
│  ┌─────────────────────────────────────────────────────┐           │
│  │              AI ENGINE CORE                          │          │
│  │                                                      │          │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │          │
│  │  │  Criticality │ │    Block     │ │  Predictive  │ │ AI Layer │
│  │  │   Scoring    │ │  Optimizer   │ │ Maintenance  │ │          │
│  │  │  (XGBoost)   │ │  (CP-SAT)   │ │   (LSTM)     │ │          │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │          │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │          │
│  │  │   Conflict   │ │ Multi-Agent  │ │   Anomaly    │ │          │
│  │  │   Resolver   │ │  Negotiator  │ │  Detection   │ │          │
│  │  │    (CSP)     │ │(Game Theory) │ │ (IsoForest)  │ │          │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ │          │
│  └───────────────────────┬─────────────────────────────┘           │
│                          ▼                                         │
│  ┌─────────────────────────────────────────────────────┐           │
│  │           PRESENTATION LAYER                         │          │
│  │                                                      │          │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │          │
│  │  │Dashboard │ │  Block   │ │ Alert  │ │   NLP    │ │ UI Layer │
│  │  │  + KPIs  │ │ Planner  │ │ System │ │ Commands │ │          │
│  │  └──────────┘ └──────────┘ └────────┘ └──────────┘ │          │
│  └─────────────────────────────────────────────────────┘           │
└────────────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
 ①  Data Sources (TMS, SMMS, TDMS, COA)
         │
         ▼
 ②  DataIntegrator — Merges 4 sources → unified task list + constraint matrix
         │
         ▼
 ③  CriticalityScorer (XGBoost) — Ranks every task → score 0-100
         │
         ▼
 ④  MultiAgentNegotiator — 3 dept agents propose → negotiate → consensus
         │
         ▼
 ⑤  BlockOptimizer (CP-SAT) — Solves constrained optimization → optimal plan
         │
         ▼
 ⑥  ConflictResolver (CSP) — Safety gate → validates no train clashes
         │
         ▼
 ⑦  Approved Block Plan → Dashboard + Real-time Notifications
```

---

## 🤖 AI/ML Pipeline — The 7-Engine Intelligence Core

| # | Engine | Algorithm | Framework | Purpose | Training |
|---|---|---|---|---|---|
| 1 | **Data Integrator** | ETL + Fusion | Custom Python | Merges TMS + SMMS + TDMS + COA into unified task list | ❌ No |
| 2 | **Criticality Scorer** | Gradient Boosted Trees | XGBoost + scikit-learn | Ranks maintenance tasks by urgency (0-100 score) using 15 features | ✅ Synthetic |
| 3 | **Block Optimizer** | Constraint Programming (CP-SAT) | Google OR-Tools | Finds mathematically optimal block schedule (solves in <5 seconds) | ❌ Solver |
| 4 | **Conflict Resolver** | Constraint Satisfaction (CSP) | Custom + OR-Tools | Detects train-block conflicts, proposes alternatives | ❌ Logic |
| 5 | **Multi-Agent Negotiation** | Game Theory / Nash Equilibrium | Custom Python | 3 dept. agents negotiate via 4-round protocol | ⚡ Rule-based |
| 6 | **Predictive Engine** | LSTM Time-Series | PyTorch | Predicts asset failure dates and Remaining Useful Life (RUL) | ✅ Synthetic |
| 7 | **Anomaly Detector** | Isolation Forest | scikit-learn | Detects unusual asset degradation patterns | ✅ Synthetic |
| 8 | **NLP Interface** | LLM + Regex Fallback | Qwen3-235B / NVIDIA Nemotron | Parses Hindi/English commands into API actions | ❌ Pre-trained |

### Optimizer Objective Function

```
MAXIMIZE:
    Σ (criticality_score × 100) × x[i,s]           — schedule urgent work first
  + Σ overdue_bonus(5000) × x[i,s]                  — prioritize overdue tasks
  + Σ severity_bonus(3000) × x[i,s]                 — CRITICAL severity first
  + Σ integration_bonus(2000) × integrated_slot[s]   — reward multi-dept blocks
  - Σ block_cost(500) × slot_used[s]                 — minimize disruption

SUBJECT TO:
    C1: Each task assigned at most once
    C2: Task duration ≤ slot capacity
    C3: Max 2 blocks/section/day
    C4: TRD tasks → power-compatible windows only
    C5: No train conflicts (validated by ConflictResolver safety gate)
```

### XGBoost Feature Engineering (15 Features)

```
severity_encoded, days_overdue, days_until_due, traffic_density,
safety_impact_score, cascading_risk, speed_restriction_impact,
asset_remaining_life, asset_health, weather_risk_factor,
last_maintenance_gap, estimated_hours, is_overdue, is_ghat_section,
km_range_affected
```

### Trained Model Artifacts

| Model | File | Size | Format |
|---|---|---|---|
| Criticality Scorer | `ai_models/criticality_model.pkl` | ~475 KB | Pickle (XGBoost) |
| Predictive Engine | `ai_models/lstm_predictor.pt` | ~60 KB | PyTorch State Dict |
| Anomaly Detector | `ai_models/anomaly_model.pkl` | ~1.5 MB | Pickle (IsoForest) |

---

## 🛠 Tech Stack

| Layer | Technology | Why This Choice |
|---|---|---|
| **Frontend** | React 19 + Vite 8 | Latest React with blazing-fast HMR |
| **UI Components** | Lucide Icons + Recharts | Premium icons + interactive data visualization |
| **Routing** | React Router v7 | Declarative, role-aware navigation |
| **HTTP Client** | Axios | Interceptors for auth + error handling |
| **Backend** | FastAPI (Python 3.13) | Async-native, auto-generated OpenAPI docs, ML-friendly |
| **ORM** | SQLAlchemy 2.0 | Async support + robust query builder |
| **Validation** | Pydantic v2 | Type-safe request/response schemas |
| **Database** | PostgreSQL 16 (prod) / SQLite (dev) | Zero-config local dev, production-grade in Docker |
| **Caching** | Redis 7 | Real-time block status + session caching |
| **ML Core** | XGBoost, scikit-learn | Gradient boosting + classical ML toolkit |
| **Deep Learning** | PyTorch 2.1+ | LSTM neural network for time-series prediction |
| **Optimization** | Google OR-Tools (CP-SAT) | Industrial-grade constraint solver |
| **NLP** | Qwen3-235B (Ollama) / NVIDIA Nemotron | Multi-provider LLM with automatic fallback |
| **Real-time** | WebSockets | Live notification streaming |
| **Containerization** | Docker + Docker Compose | One-command deployment with health checks |
| **Testing** | Pytest + pytest-asyncio | 10 test suites, 80+ test cases |

---

## 📁 Project Structure

```
railmind-ai/
│
├── 📄 README.md                          # You are here
├── 📄 docker-compose.yml                 # Full-stack orchestration (Backend + PostgreSQL + Redis)
├── 📄 .env.example                       # Environment variable template
├── 📄 .gitignore
│
├── 🔧 backend/                           # ═══ FastAPI Backend (Python) ═══
│   ├── 📄 main.py                        # Application entry point + lifespan manager
│   ├── 📄 config.py                      # Pydantic Settings (env-based configuration)
│   ├── 📄 schemas.py                     # Pydantic request/response models (18KB)
│   ├── 📄 requirements.txt              # Python dependencies (57 packages)
│   ├── 📄 Dockerfile                     # Production container (Python 3.13-slim)
│   ├── 📄 .env                           # Local environment variables
│   │
│   ├── 🤖 ai_models/                    # ═══ Trained Model Artifacts ═══
│   │   ├── criticality_model.pkl         # XGBoost criticality scorer (~475 KB)
│   │   ├── lstm_predictor.pt             # PyTorch LSTM predictor (~60 KB)
│   │   └── anomaly_model.pkl             # Isolation Forest detector (~1.5 MB)
│   │
│   ├── 🧠 services/                     # ═══ AI Engine Services (Core Intelligence) ═══
│   │   ├── __init__.py
│   │   ├── data_integrator.py            # [Engine 1] Unified data fusion (TMS+SMMS+TDMS+COA)
│   │   ├── criticality_scorer.py         # [Engine 2] XGBoost criticality ranking (15 features)
│   │   ├── block_optimizer.py            # [Engine 3] CP-SAT optimizer (687 lines, 5-term objective)
│   │   ├── conflict_resolver.py          # [Engine 4] CSP conflict detection + alternative suggestion
│   │   ├── multi_agent.py                # [Engine 5] 3-agent Nash Equilibrium negotiation
│   │   ├── predictive_engine.py          # [Engine 6] LSTM failure prediction + RUL estimation
│   │   ├── anomaly_detector.py           # [Engine 7] Isolation Forest outlier detection
│   │   ├── nlp_processor.py              # [Engine 8] Hindi/English NLP (Ollama + regex fallback)
│   │   ├── llm_providers.py              # Multi-provider LLM abstraction (NVIDIA + Ollama)
│   │   ├── notification_service.py       # Real-time WebSocket alert system
│   │   └── forecasting_service.py        # Time-series forecasting utilities
│   │
│   ├── 📊 models/                        # ═══ SQLAlchemy ORM Models ═══
│   │   ├── __init__.py                   # Engine, SessionLocal, Base, create_all_tables()
│   │   ├── corridor.py                   # RailwaySection (CSMT-KYN, KYN-KAS, etc.)
│   │   ├── asset.py                      # RailwayAsset (track, signal, OHE equipment)
│   │   ├── maintenance_task.py           # MaintenanceTask (unified TMS+SMMS+TDMS defects)
│   │   ├── train_schedule.py             # TrainSchedule (COA timetable data)
│   │   ├── block_plan.py                 # BlockPlan + BlockWindow + BlockTaskAssignment + ConflictLog
│   │   ├── maintenance_request.py        # MaintenanceRequest (department submissions)
│   │   └── user.py                       # User model (roles: DEN, SSE, PWI, DSTE, DEE, ADMIN)
│   │
│   ├── 🌐 routes/                        # ═══ REST API Routes ═══
│   │   ├── __init__.py                   # Main API router (/api prefix)
│   │   ├── optimizer.py                  # ⭐ /api/optimizer — Generate plan, re-optimize, what-if
│   │   ├── tasks.py                      # /api/tasks — Maintenance task CRUD + criticality
│   │   ├── trains.py                     # /api/trains — Train schedules + corridor availability
│   │   ├── sections.py                   # /api/sections — Railway section management
│   │   ├── analytics.py                  # /api/analytics — KPI metrics + optimization stats
│   │   ├── predictions.py                # /api/predictions — Asset health prediction
│   │   ├── nlp.py                        # /api/nlp — Natural language command processing
│   │   ├── requests.py                   # /api/requests — Maintenance request workflow
│   │   └── auth.py                       # /api/auth — Login + role-based access
│   │
│   ├── 💾 data/                          # ═══ Database Seeding ═══
│   │   ├── init.sql                      # PostgreSQL schema (8 tables)
│   │   ├── seed_all.py                   # Master seeder (runs all seed scripts)
│   │   ├── seed_corridor.py              # Seed railway sections (Mumbai Division)
│   │   ├── seed_assets.py                # Generate 300+ railway assets
│   │   ├── seed_maintenance.py           # Generate 200+ maintenance tasks
│   │   ├── seed_timetable.py             # Load 150+ train schedules
│   │   ├── seed_users.py                 # Create demo users (all roles)
│   │   └── sample_data/                  # ═══ Realistic Synthetic Data ═══
│   │       ├── tms_defects.json          # 80+ track defects (Track Management System)
│   │       ├── sms_signals.json          # 50+ signal maintenance tasks (SMMS)
│   │       ├── tdms_ohe.json             # 40+ OHE/power tasks (TDMS)
│   │       ├── coa_timetable.json        # 150+ train schedules (Mumbai Division)
│   │       └── sections.json             # Real IR section data (CSMT-KYN, KYN-KAS, etc.)
│   │
│   └── 🧪 tests/                         # ═══ Test Suite (10 files, 80+ tests) ═══
│       ├── test_criticality.py           # XGBoost model training + scoring tests
│       ├── test_optimizer.py             # CP-SAT solver constraint validation
│       ├── test_conflict.py              # Conflict detection accuracy tests
│       ├── test_api.py                   # Full API endpoint integration tests
│       ├── test_ai_models.py             # End-to-end AI pipeline tests
│       ├── test_approval_safety.py       # Block plan approval workflow tests
│       ├── test_nlp_ollama.py            # NLP command parsing tests (22 KB)
│       ├── test_nlp_failover.py          # LLM failover + regex fallback tests
│       ├── test_requests.py              # Maintenance request workflow tests
│       └── test_scheduling_correctness.py # Deep scheduling correctness validation (26 KB)
│
├── 🎨 frontend/                          # ═══ React Frontend (Vite) ═══
│   ├── 📄 index.html                     # SPA entry point
│   ├── 📄 package.json                   # NPM dependencies
│   ├── 📄 vite.config.js                 # Vite configuration
│   ├── 📄 vercel.json                    # Vercel deployment config
│   │
│   └── src/
│       ├── 📄 main.jsx                   # React DOM entry
│       ├── 📄 App.jsx                    # Root component + role-aware routing + sidebar
│       ├── 📄 index.css                  # Design system (16 KB — CSS variables, animations)
│       ├── 📄 App.css                    # Component-specific styles
│       │
│       ├── 📄 contexts/
│       │   └── AuthContext.jsx           # JWT auth context + role management
│       │
│       ├── 📄 components/
│       │   └── ProtectedRoute.jsx        # Route guard with role-based access
│       │
│       └── 📱 pages/                     # ═══ 11 Feature-Rich Pages ═══
│           ├── Dashboard.jsx             # 🏠 System Control Center (38 KB) — KPIs, charts, alerts
│           ├── AIPlanner.jsx             # 🤖 AI Block Plan Generator — one-click optimization
│           ├── BlockPlans.jsx            # 📋 Block Plan Management (38 KB) — CRUD + approval
│           ├── Tasks.jsx                 # 📝 Maintenance Board — task tracking + criticality
│           ├── Trains.jsx                # 🚂 Train Dispatch — schedule visualization
│           ├── Assets.jsx                # ⚡ Asset Health Monitor (30 KB) — LSTM predictions
│           ├── Conflicts.jsx             # ⚠️ Safety & Conflicts — real-time clash detection
│           ├── WhatIf.jsx                # 🔮 What-If Simulator (36 KB) — scenario testing
│           ├── Analytics.jsx             # 📊 Analytics Dashboard — optimization metrics
│           ├── Requests.jsx              # 📥 Request Inbox (34 KB) — dept submission workflow
│           └── Login.jsx                 # 🔐 Role-based Login — department-aware auth
│
├── 📓 ml_notebooks/                      # ═══ Jupyter Research Notebooks ═══
│   ├── 01_data_exploration.ipynb         # EDA on railway maintenance data
│   ├── 02_criticality_model.ipynb        # XGBoost model development + tuning
│   ├── 03_lstm_predictor.ipynb           # LSTM architecture design + training
│   ├── 04_optimizer_testing.ipynb        # OR-Tools solver benchmarking
│   └── 05_multi_agent_sim.ipynb          # Multi-agent negotiation simulation
│
└── 📚 docs/                              # ═══ Documentation ═══
    ├── API_DOCS.md                       # Comprehensive API reference
    ├── ARCHITECTURE.md                   # System design document
    └── DEMO_SCRIPT.md                    # Live demo walkthrough script
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (3.13 recommended)
- **Node.js 18+** (20+ recommended)
- **Docker & Docker Compose** (for production deployment)
- **Git**

### Option 1: Local Development (Quick Start)

```bash
# ── Clone the repository ──
git clone https://github.com/YOUR_USERNAME/railmind-ai.git
cd railmind-ai
```

#### Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Seed the database with synthetic data
python -c "from data.seed_all import seed_all; seed_all()"

# Start the backend server
uvicorn main:app --reload --port 8000
```

> 📝 Local dev uses **SQLite** — no database setup needed!

#### Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs

### Option 2: Docker Deployment (Production)

```bash
# From the project root (railmind-ai/)
docker-compose up --build -d
```

This starts:
- 🐍 **Backend** on port `8000` (FastAPI + AI engines)
- 🐘 **PostgreSQL 16** on port `5432` (with auto-initialization)
- 🔴 **Redis 7** on port `6379` (caching + real-time updates)

### Demo Credentials

| Role | Username | Department | Access Level |
|---|---|---|---|
| Admin | `admin` | System | Full system access |
| DEN | `den_user` | ENGG | Engineering management |
| SSE | `sse_user` | ENGG | Section engineer |
| PWI | `pwi_user` | ENGG | Track maintenance |
| DSTE | `dste_user` | SNT | Signal & Telecom |
| DEE | `dee_user` | TRD | Traction distribution |

---

## 📡 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/sections` | List all railway sections |
| `GET` | `/api/tasks` | Get maintenance tasks with criticality scores |
| `GET` | `/api/trains` | Train schedules and corridor availability |
| `POST` | `/api/optimizer/generate-plan` | ⭐ Generate AI-optimized block plan |
| `POST` | `/api/optimizer/what-if` | Run what-if scenario simulation |
| `GET` | `/api/predictions/{asset_id}` | LSTM failure prediction for an asset |
| `POST` | `/api/nlp/command` | Process natural language command |
| `GET` | `/api/analytics/kpis` | Get optimization KPI metrics |
| `POST` | `/api/requests` | Submit maintenance request |
| `POST` | `/api/auth/login` | Authenticate and get JWT token |
| `GET` | `/health` | System health check |

### Example: Generate an AI-Optimized Block Plan

```bash
curl -X POST http://localhost:8000/api/optimizer/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "section_id": 1,
    "start_date": "2026-09-15",
    "end_date": "2026-09-21",
    "strategy": "balanced"
  }'
```

**Response** (truncated):

```json
{
  "plan_id": 42,
  "status": "OPTIMIZED",
  "solve_time_ms": 2340,
  "total_tasks_scheduled": 18,
  "total_blocks_used": 7,
  "optimization_score": 87.3,
  "windows": [
    {
      "date": "2026-09-15",
      "start_time": "10:00",
      "end_time": "12:30",
      "section": "CSMT-KYN",
      "departments": ["ENGG", "SNT"],
      "tasks": [...]
    }
  ],
  "conflicts_detected": 0,
  "ai_explanation": "Scheduled 18/23 tasks. 5 deferred due to train conflicts..."
}
```

### Interactive API Docs

Visit **http://localhost:8000/docs** for the full Swagger UI with try-it-out functionality.

---

## 🖥 Frontend Screens

| # | Screen | Description | Key Features |
|---|---|---|---|
| 1 | **System Control (Dashboard)** | Command center overview | Live KPIs, section health map, critical alerts, optimization stats |
| 2 | **AI Planner** | One-click block plan generation | Strategy selection, AI explanation, plan preview |
| 3 | **Block Plans** | Block plan management | Gantt view, approval workflow, status tracking |
| 4 | **Maintenance Board** | Task management | Criticality scoring, filtering, department grouping |
| 5 | **Train Dispatch** | Train schedule visualization | Corridor availability, conflict highlighting |
| 6 | **Asset Health** | Asset monitoring + LSTM predictions | Degradation curves, RUL estimation, anomaly alerts |
| 7 | **Safety & Conflicts** | Conflict detection dashboard | Train-block clashes, resolution suggestions |
| 8 | **What-If Simulator** | Scenario testing tool | Side-by-side comparison, impact analysis |
| 9 | **Analytics** | Optimization metrics | Before/after comparison, efficiency trends |
| 10 | **Request Inbox** | Maintenance request workflow | Department submissions, approval pipeline |
| 11 | **Login** | Role-based authentication | Department-aware access control |

---

## 🧪 Testing

### Run All Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Test Suite Breakdown

| Test File | Tests | What It Validates |
|---|---|---|
| `test_criticality.py` | XGBoost model | Training, scoring accuracy, feature importance |
| `test_optimizer.py` | CP-SAT solver | Constraint satisfaction, solve time <5s, optimality |
| `test_conflict.py` | CSP resolver | Train clash detection, alternative suggestions |
| `test_api.py` | REST endpoints | All API routes, status codes, response schemas |
| `test_ai_models.py` | Full pipeline | End-to-end AI pipeline integration |
| `test_approval_safety.py` | Approval workflow | Multi-stage approval, safety gate validation |
| `test_nlp_ollama.py` | NLP commands | Hindi/English parsing, intent classification |
| `test_nlp_failover.py` | LLM failover | NVIDIA → Ollama → regex fallback chain |
| `test_requests.py` | Request workflow | Department submission + approval flow |
| `test_scheduling_correctness.py` | Deep validation | Schedule feasibility, constraint integrity |

---

## 🐳 Deployment

### Docker Compose Architecture

```yaml
┌──────────────────────────────────────────────────────┐
│                   docker-compose.yml                  │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────┐                                 │
│  │   Backend API   │  Port 8000                      │
│  │  (FastAPI +     │  ← depends_on: db, redis        │
│  │   AI Engines)   │  ← health check: /health        │
│  └────────┬────────┘                                 │
│           │                                           │
│  ┌────────┴────────┐  ┌─────────────────┐            │
│  │  PostgreSQL 16  │  │    Redis 7      │            │
│  │  Port 5432      │  │  Port 6379      │            │
│  │  + init.sql     │  │  + health check │            │
│  └─────────────────┘  └─────────────────┘            │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### Frontend Deployment (Vercel)

The frontend is configured for **Vercel** deployment with `vercel.json` for SPA routing.

```bash
cd frontend
npm run build    # Produces optimized build in dist/
```

---

## ⚡ Performance Benchmarks

| Metric | Target | Achieved |
|---|---|---|
| Block plan generation (7-day, 200+ tasks) | < 5 seconds | ✅ ~2-3 seconds |
| Criticality scoring (batch 200 tasks) | < 1 second | ✅ ~200ms |
| Conflict detection per plan | < 500ms | ✅ ~150ms |
| LSTM prediction per asset | < 200ms | ✅ ~80ms |
| API response (95th percentile) | < 300ms | ✅ ~120ms |
| Concurrent users supported | 50+ | ✅ Async FastAPI |

---

## 📄 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | RailMind AI | Application display name |
| `DEBUG` | True | Enable debug mode |
| `DATABASE_URL` | sqlite:///./railmind.db | Database connection (SQLite/PostgreSQL) |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection URL |
| `REDIS_ENABLED` | False | Enable Redis caching |
| `OPTIMIZER_MAX_SOLVE_TIME_SECONDS` | 5 | CP-SAT solver time limit |
| `MAX_BLOCKS_PER_SECTION_PER_DAY` | 2 | Hard constraint: max blocks |
| `NLP_PROVIDER` | nvidia | LLM provider (nvidia / ollama / pattern) |
| `NVIDIA_API_KEY` | — | NVIDIA Nemotron API key |
| `OLLAMA_BASE_URL` | http://127.0.0.1:11434 | Ollama server URL |
| `OLLAMA_MODEL` | qwen3:235b | Ollama model for NLP |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project was built for **Smart India Hackathon 2026 (SIH 2026)** — Problem Statement **26027**, under the **Ministry of Railways**.

---

<p align="center">
  <strong>Built with 🧠 by Team RailMind</strong>
  <br />
  <em>Smart India Hackathon 2026 — Transforming Indian Railway Maintenance with AI</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made_with-❤️_and_Python-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Powered_by-7_AI_Engines-blueviolet?style=for-the-badge" />
</p>
