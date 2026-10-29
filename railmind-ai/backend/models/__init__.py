# ═══════════════════════════════════════════════════════════════
# RailMind AI — Database Setup & SQLAlchemy Configuration
# ═══════════════════════════════════════════════════════════════

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from config import get_settings

settings = get_settings()


# ─── SQLAlchemy Base Class ───
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ─── Engine Configuration ───
# SQLite needs special handling for foreign keys and threading
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )

    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL / other databases
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
    )


# ─── Session Factory ───
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session after the request.

    Usage in routes:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """
    Create all database tables. Called on app startup.
    Import all models here so Base.metadata knows about them.
    """
    # Import all models to register them with Base.metadata
    from models.corridor import RailwaySection  # noqa: F401
    from models.asset import RailwayAsset  # noqa: F401
    from models.maintenance_task import MaintenanceTask  # noqa: F401
    from models.maintenance_request import MaintenanceRequest  # noqa: F401
    from models.train_schedule import TrainSchedule  # noqa: F401
    from models.block_plan import BlockPlan, BlockWindow, BlockTaskAssignment, ConflictLog  # noqa: F401
    from models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)


# ─── Export all models for easy imports ───
# Usage: from models import RailwaySection, MaintenanceTask, etc.
__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "create_all_tables",
]
