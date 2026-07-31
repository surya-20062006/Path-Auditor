"""
Database connection, session management, and schema initialization utilities.
Supports PostgreSQL (Production/Staging) and SQLite (Development/Fallback).
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from backend.core.config import settings
from backend.core.logger import logger
from backend.models.schema import Base

# Determine sync DB URL
DB_URL = settings.sync_database_url

# Configure connection arguments
connect_args = {}
if "sqlite" in DB_URL:
    connect_args = {"check_same_thread": False}

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10 if "sqlite" not in DB_URL else 5,
    max_overflow=20 if "sqlite" not in DB_URL else 10,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a transactional DB session and closes it after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all database tables and indexes if they do not exist.
    """
    logger.info("Initializing database schema...", db_url=DB_URL)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully across 11 core tables.")
    except Exception as e:
        logger.error("Failed to initialize database schema", error=str(e))
        raise e


if __name__ == "__main__":
    init_db()
