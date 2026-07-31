import os
import secrets
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Enterprise Application Settings using Pydantic Settings.
    Configurable via environment variables or .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App Environment
    APP_NAME: str = "Decision Path Auditor"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = ["*"]

    # Database URLs (Defaulting to SQLite fallback if Postgres not provided)
    DATABASE_URL: str = Field(
        default="sqlite:///./audit_logs.db",
        description="SQLAlchemy DB connection string (PostgreSQL in production)"
    )

    # Redis & Celery Config
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and rate limiting"
    )
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker Redis DB"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result store DB"
    )

    # AI & LLM Provider Configuration
    DEFAULT_LLM_PROVIDER: str = Field(default="openai", description="openai | anthropic | gemini")
    DEFAULT_MODEL_NAME: str = Field(default="gpt-4-turbo", description="Model identifier")
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # AWS S3 Storage & Archival Config
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_AUDIT_BUCKET_NAME: str = "decision-path-auditor-traces"
    ENABLE_S3_ARCHIVAL: bool = False

    # Security, JWT & AES-GCM PII Encryption
    JWT_SECRET_KEY: str = Field(
        default="enterprise-secret-key-for-decision-path-auditor-2026",
        description="Secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AES_GCM_SECRET_KEY: str = Field(
        default="0123456789abcdef0123456789abcdef",
        description="32-byte secret key for AES-256-GCM encryption of original PII tokens"
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.DATABASE_URL.lower()

    @property
    def sync_database_url(self) -> str:
        """Ensure correct SQLAlchemy URL driver prefix."""
        if "postgresql+asyncpg" in self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        return self.DATABASE_URL


settings = Settings()
