-- ═══════════════════════════════════════════════════════════════
-- RailMind AI — PostgreSQL Database Schema
-- This file is executed by Docker on first container start
-- For SQLite (local dev), tables are created by SQLAlchemy ORM
-- ═══════════════════════════════════════════════════════════════

-- Table 1: Railway Sections
CREATE TABLE IF NOT EXISTS railway_sections (
    id              SERIAL PRIMARY KEY,
    section_code    VARCHAR(20) UNIQUE NOT NULL,
    section_name    VARCHAR(100) NOT NULL,
    division        VARCHAR(50) NOT NULL,
    zone            VARCHAR(50) NOT NULL,
    km_start        DECIMAL(8,2) NOT NULL,
    km_end          DECIMAL(8,2) NOT NULL,
    track_type      VARCHAR(20) DEFAULT 'DBL',
    traction        VARCHAR(20) DEFAULT 'AC25KV',
    max_speed_kmph  INT DEFAULT 110,
    trains_per_day  INT DEFAULT 100,
    is_ghat_section BOOLEAN DEFAULT FALSE,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Table 2: Railway Assets
CREATE TABLE IF NOT EXISTS railway_assets (
    id              SERIAL PRIMARY KEY,
    asset_code      VARCHAR(30) UNIQUE NOT NULL,
    asset_type      VARCHAR(20) NOT NULL,
    department      VARCHAR(20) NOT NULL,
    section_id      INT REFERENCES railway_sections(id) ON DELETE CASCADE,
    km_location     DECIMAL(8,2) NOT NULL,
    km_end          DECIMAL(8,2),
    equipment_name  VARCHAR(100),
    install_date    DATE,
    last_maintained DATE,
    health_score    DECIMAL(5,2) DEFAULT 100.00,
    status          VARCHAR(20) DEFAULT 'ACTIVE',
    metadata        JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Table 3: Maintenance Tasks
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id                  SERIAL PRIMARY KEY,
    task_code           VARCHAR(30) UNIQUE NOT NULL,
    source_system       VARCHAR(10) NOT NULL,
    department          VARCHAR(20) NOT NULL,
    asset_id            INT REFERENCES railway_assets(id),
    section_id          INT REFERENCES railway_sections(id) ON DELETE CASCADE,
    km_from             DECIMAL(8,2) NOT NULL,
    km_to               DECIMAL(8,2) NOT NULL,
    task_type           VARCHAR(50) NOT NULL,
    severity            VARCHAR(20) NOT NULL,
    detected_date       DATE NOT NULL,
    due_date            DATE NOT NULL,
    estimated_hours     DECIMAL(4,1) NOT NULL,
    block_type_required VARCHAR(30) NOT NULL,
    line_affected       VARCHAR(10),
    speed_restriction   INT,
    is_overdue          BOOLEAN DEFAULT FALSE,
    criticality_score   DECIMAL(5,2),
    predicted_failure   DATE,
    status              VARCHAR(20) DEFAULT 'PENDING',
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Table 4: Train Schedules
CREATE TABLE IF NOT EXISTS train_schedules (
    id              SERIAL PRIMARY KEY,
    train_no        VARCHAR(10) NOT NULL,
    train_name      VARCHAR(100) NOT NULL,
    train_type      VARCHAR(20) NOT NULL,
    priority        INT NOT NULL,
    section_id      INT REFERENCES railway_sections(id) ON DELETE CASCADE,
    direction       VARCHAR(5) NOT NULL,
    entry_km        DECIMAL(8,2) NOT NULL,
    exit_km         DECIMAL(8,2) NOT NULL,
    entry_time      TIME NOT NULL,
    exit_time       TIME NOT NULL,
    days_of_run     VARCHAR(20) DEFAULT 'DAILY',
    is_special      BOOLEAN DEFAULT FALSE,
    avg_delay_min   INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Table 5: Block Plans
CREATE TABLE IF NOT EXISTS block_plans (
    id                  SERIAL PRIMARY KEY,
    plan_code           VARCHAR(30) UNIQUE NOT NULL,
    plan_type           VARCHAR(20) NOT NULL,
    section_id          INT REFERENCES railway_sections(id) ON DELETE CASCADE,
    generated_at        TIMESTAMP DEFAULT NOW(),
    generated_by        VARCHAR(20) DEFAULT 'AI',
    plan_start_date     DATE NOT NULL,
    plan_end_date       DATE NOT NULL,
    total_blocks        INT,
    total_block_hrs     DECIMAL(6,1),
    utilization_pct     DECIMAL(5,2),
    optimization_score  DECIMAL(5,2),
    tasks_scheduled     INT,
    conflicts_resolved  INT DEFAULT 0,
    status              VARCHAR(20) DEFAULT 'DRAFT',
    approved_by         VARCHAR(50),
    approved_at         TIMESTAMP,
    rejection_reason    TEXT
);

-- Table 6: Block Windows
CREATE TABLE IF NOT EXISTS block_windows (
    id              SERIAL PRIMARY KEY,
    plan_id         INT REFERENCES block_plans(id) ON DELETE CASCADE,
    block_code      VARCHAR(30) UNIQUE NOT NULL,
    block_date      DATE NOT NULL,
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    duration_hrs    DECIMAL(4,1) NOT NULL,
    section_id      INT REFERENCES railway_sections(id),
    km_from         DECIMAL(8,2) NOT NULL,
    km_to           DECIMAL(8,2) NOT NULL,
    block_type      VARCHAR(30) NOT NULL,
    line_blocked    VARCHAR(10) NOT NULL,
    is_integrated   BOOLEAN DEFAULT FALSE,
    departments     VARCHAR(100),
    status          VARCHAR(20) DEFAULT 'PLANNED',
    ai_explanation  TEXT
);

-- Table 7: Block Task Assignments
CREATE TABLE IF NOT EXISTS block_task_assignments (
    id              SERIAL PRIMARY KEY,
    block_id        INT REFERENCES block_windows(id) ON DELETE CASCADE,
    task_id         INT REFERENCES maintenance_tasks(id),
    sequence_order  INT DEFAULT 1,
    start_offset_min INT DEFAULT 0,
    duration_min    INT NOT NULL,
    assigned_team   VARCHAR(50),
    status          VARCHAR(20) DEFAULT 'ASSIGNED'
);

-- Table 8: Conflict Log
CREATE TABLE IF NOT EXISTS conflict_log (
    id              SERIAL PRIMARY KEY,
    detected_at     TIMESTAMP DEFAULT NOW(),
    conflict_type   VARCHAR(30) NOT NULL,
    description     TEXT NOT NULL,
    block_id_1      INT REFERENCES block_windows(id) ON DELETE CASCADE,
    block_id_2      INT,
    train_id        INT REFERENCES train_schedules(id),
    resolution      TEXT,
    resolution_type VARCHAR(20),
    resolved        BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMP
);

-- Table 9: Users
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    employee_id     VARCHAR(20) UNIQUE NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE,
    role            VARCHAR(20) NOT NULL,
    department      VARCHAR(20) NOT NULL,
    division        VARCHAR(50),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    last_login      TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════
-- Indexes for performance
-- ═══════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_assets_section ON railway_assets(section_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON railway_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_dept ON railway_assets(department);
CREATE INDEX IF NOT EXISTS idx_tasks_section ON maintenance_tasks(section_id);
CREATE INDEX IF NOT EXISTS idx_tasks_severity ON maintenance_tasks(severity);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON maintenance_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_overdue ON maintenance_tasks(is_overdue);
CREATE INDEX IF NOT EXISTS idx_trains_section ON train_schedules(section_id);
CREATE INDEX IF NOT EXISTS idx_trains_priority ON train_schedules(priority);
CREATE INDEX IF NOT EXISTS idx_blocks_date ON block_windows(block_date);
CREATE INDEX IF NOT EXISTS idx_blocks_section ON block_windows(section_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_type ON conflict_log(conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflicts_resolved ON conflict_log(resolved);
