#!/usr/bin/env python3
"""
Decision Path Auditor - Enterprise AI Governance SaaS Platform
Server Bootstrapper Script
"""
import uvicorn
from backend.core.config import settings
from backend.core.logger import logger


def main():
    logger.info(
        "Starting Decision Path Auditor API Server",
        env=settings.ENVIRONMENT,
        port=settings.PORT,
        db=settings.DATABASE_URL
    )
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
        log_level="info"
    )


if __name__ == "__main__":
    main()
