from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Tuple

# HTTP & Request Metrics
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# AI Agent & Token Metrics
TOKEN_USAGE_COUNTER = Counter(
    "ai_agent_token_usage_total",
    "Total LLM tokens consumed by agent executions",
    ["model_name", "token_type"]  # token_type: prompt | completion | total
)

AGENT_RUNS_COUNTER = Counter(
    "ai_agent_runs_total",
    "Total AI Agent executions recorded by the auditor",
    ["status", "risk_level", "model_name"]
)

AGENT_RUN_LATENCY = Histogram(
    "ai_agent_execution_duration_seconds",
    "End-to-end AI Agent reasoning execution time",
    ["model_name", "status"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 45.0, 60.0)
)

# Tool & Function Call Metrics
TOOL_CALLS_COUNTER = Counter(
    "ai_agent_tool_calls_total",
    "Count of tool calls executed during reasoning chains",
    ["tool_name", "status"]
)

# PII Redaction Metrics
PII_REDACTION_COUNTER = Counter(
    "pii_redaction_events_total",
    "Count of sensitive PII entities redacted by entity type",
    ["entity_type"]
)

# System Health Gauge
SERVICE_HEALTH_STATUS = Gauge(
    "service_health_status",
    "Service health status gauge (1 = Healthy, 0 = Unhealthy)",
    ["service_name"]
)


def get_metrics_export() -> Tuple[bytes, str]:
    """
    Returns latest prometheus formatted metrics payload and content type.
    """
    return generate_latest(), CONTENT_TYPE_LATEST
