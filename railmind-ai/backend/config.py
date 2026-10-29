# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RailMind AI â€” Backend Configuration
# Pydantic Settings for environment-based configuration
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    All settings can be overridden via environment variables.
    """

    # â”€â”€â”€ App Settings â”€â”€â”€
    APP_NAME: str = "RailMind AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Automatic Block Planning for Indian Railways"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # â”€â”€â”€ Database Settings â”€â”€â”€
    # Default to SQLite for local development (no Docker needed)
    # Switch to PostgreSQL for production/Docker deployment
    DATABASE_URL: str = Field(
        default="sqlite:///./railmind.db",
        description="Database connection URL. Use PostgreSQL for production."
    )

    # â”€â”€â”€ Redis Settings â”€â”€â”€
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and real-time updates"
    )
    REDIS_ENABLED: bool = Field(
        default=False,
        description="Set to True when Redis is available (Docker deployment)"
    )

    # ─── CORS Settings ───
    CORS_ORIGINS: list[str] = ["*"]

    # ─── AI Model Paths ───
    MODEL_DIR: str = "ai_models"
    CRITICALITY_MODEL_PATH: str = "ai_models/criticality_model.pkl"
    LSTM_MODEL_PATH: str = "ai_models/lstm_predictor.pt"
    ANOMALY_MODEL_PATH: str = "ai_models/anomaly_model.pkl"
    PREDICTIVE_MODEL_PATH: str = "ai_models/lstm_predictor.pt"

    # â”€â”€â”€ Optimizer Settings â”€â”€â”€
    OPTIMIZER_MAX_SOLVE_TIME_SECONDS: int = 5
    OPTIMIZER_DEFAULT_BLOCK_WINDOW_START: str = "10:00"
    OPTIMIZER_DEFAULT_BLOCK_WINDOW_END: str = "13:00"
    MAX_BLOCKS_PER_SECTION_PER_DAY: int = 2
    MIN_GAP_BETWEEN_BLOCKS_MINUTES: int = 30

    # â”€â”€â”€ Scheduler Settings â”€â”€â”€
    DEFAULT_PLAN_DAYS: int = 7  # Weekly plan by default
    BLOCK_BUFFER_MINUTES: int = 15  # Extra time buffer for each block

    # NLP / LLM Settings
    # "nvidia" = Nemotron primary + Qwen fallback
    # "ollama" = Qwen-only via Ollama
    # "pattern" = regex-only (no LLM)
    NLP_PROVIDER: str = "nvidia"

    # NVIDIA Nemotron (Primary)
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_TIMEOUT_SECONDS: int = 60

    # Ollama / Qwen3-235B (Secondary fallback)
    OLLAMA_BASE_URL: str = "http://10.10.50.250:11434"
    OLLAMA_MODEL: str = "qwen3:235b"
    OLLAMA_TIMEOUT_SECONDS: int = 120
    OLLAMA_FALLBACK_ENABLED: bool = True

    # Test mode for fallback testing
    LLM_TEST_FORCE_PRIMARY_FAILURE: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance. Call this to get the app configuration.
    Uses @lru_cache so the .env file is only read once.
    """
    return Settings()
