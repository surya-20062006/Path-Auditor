import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import structlog
from contextvars import ContextVar

# Context variables for trace correlation across async requests
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class CustomJsonFormatter(logging.Formatter):
    """
    Standard Python Logging Formatter emitting RFC3339 timestamped JSON logs.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps({k: v for k, v in log_obj.items() if v is not None})


def get_logger(name: str = "decision_path_auditor") -> structlog.BoundLogger:
    """
    Configures and returns a structured JSON logger.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)


logger = get_logger()
