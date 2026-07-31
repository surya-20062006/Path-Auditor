import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, Field, ConfigDict
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AUDITOR = "auditor"
    DEVELOPER = "developer"
    CUSTOMER = "customer"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RunStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


# ========================================================
# SQLALCHEMY NORMALIZED DATABASE TABLES (11 CORE TABLES)
# ========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), default=UserRole.CUSTOMER.value, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="sessions")
    agent_runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("idx_agent_runs_session_user_time", "session_id", "user_id", "start_time"),
        Index("idx_agent_runs_search_filters", "risk_level", "model_name", "status"),
    )

    run_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    input_text = Column(Text, nullable=False)
    final_output = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    risk_level = Column(String(20), default=RiskLevel.LOW.value, nullable=False, index=True)
    status = Column(String(20), default=RunStatus.SUCCESS.value, nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)

    session = relationship("Session", back_populates="agent_runs")
    user = relationship("User", back_populates="agent_runs")

    retrieved_contexts = relationship("RetrievedContext", back_populates="run", cascade="all, delete-orphan", order_by="RetrievedContext.rank_order")
    tool_calls = relationship("ToolCall", back_populates="run", cascade="all, delete-orphan", order_by="ToolCall.sequence_order")
    reasoning_steps = relationship("ReasoningStep", back_populates="run", cascade="all, delete-orphan", order_by="ReasoningStep.step_index")
    decision_summary = relationship("DecisionSummary", back_populates="run", uselist=False, cascade="all, delete-orphan")
    pii_redactions = relationship("PIIRedaction", back_populates="run", cascade="all, delete-orphan")
    model_usage = relationship("ModelUsage", back_populates="run", uselist=False, cascade="all, delete-orphan")


class RetrievedContext(Base):
    __tablename__ = "retrieved_contexts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    snippet = Column(Text, nullable=False)
    similarity_score = Column(Float, default=0.0, nullable=False)
    rank_order = Column(Integer, default=1, nullable=False)

    run = relationship("AgentRun", back_populates="retrieved_contexts")


class ToolCall(Base):
    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("idx_tool_calls_run_seq", "run_id", "sequence_order"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=True)  # JSON string
    response_output = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    sequence_order = Column(Integer, default=1, nullable=False)

    run = relationship("AgentRun", back_populates="tool_calls")


class ReasoningStep(Base):
    __tablename__ = "reasoning_steps"
    __table_args__ = (
        Index("idx_reasoning_run_step", "run_id", "step_index"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, default=1, nullable=False)
    thought_content = Column(Text, nullable=False)
    is_summarized = Column(Boolean, default=False, nullable=False)
    legal_redacted_flag = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("AgentRun", back_populates="reasoning_steps")


class DecisionSummary(Base):
    __tablename__ = "decision_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plain_english_summary = Column(Text, nullable=False)
    why_decision_happened = Column(Text, nullable=False)
    information_considered = Column(Text, nullable=False)
    tools_used = Column(Text, nullable=False)
    rules_applied = Column(Text, nullable=False)
    outcome = Column(Text, nullable=False)
    regulatory_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("AgentRun", back_populates="decision_summary")


class PIIRedaction(Base):
    __tablename__ = "pii_redactions"
    __table_args__ = (
        Index("idx_pii_redactions_run", "run_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # EMAIL, PHONE, SSN, PAN, PASSPORT, etc.
    original_encrypted = Column(Text, nullable=False)  # AES-256-GCM encrypted string
    redacted_text = Column(String(100), nullable=False)  # e.g., "<REDACTED_EMAIL>"
    start_index = Column(Integer, default=0, nullable=False)
    end_index = Column(Integer, default=0, nullable=False)
    field_path = Column(String(100), default="input_text", nullable=False)

    run = relationship("AgentRun", back_populates="pii_redactions")


class ModelUsage(Base):
    __tablename__ = "model_usages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.run_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)

    run = relationship("AgentRun", back_populates="model_usage")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_timestamp_corr", "timestamp", "correlation_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(100), nullable=True)
    action_details = Column(Text, nullable=True)  # JSON metadata string
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class HealthLog(Base):
    __tablename__ = "health_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # healthy | unhealthy | degraded
    response_time_ms = Column(Integer, default=0, nullable=False)
    details_json = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


# ========================================================
# PYDANTIC VALIDATION & API SCHEMAS
# ========================================================

class UserSchema(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RetrievedContextSchema(BaseModel):
    id: str
    source_name: str
    snippet: str
    similarity_score: float
    rank_order: int
    model_config = ConfigDict(from_attributes=True)


class ToolCallSchema(BaseModel):
    id: str
    tool_name: str
    parameters: Optional[str] = None
    response_output: Optional[str] = None
    execution_time_ms: int
    error_message: Optional[str] = None
    retry_count: int
    sequence_order: int
    model_config = ConfigDict(from_attributes=True)


class ReasoningStepSchema(BaseModel):
    id: str
    step_index: int
    thought_content: str
    is_summarized: bool
    legal_redacted_flag: bool
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class DecisionSummarySchema(BaseModel):
    id: str
    plain_english_summary: str
    why_decision_happened: str
    information_considered: str
    tools_used: str
    rules_applied: str
    outcome: str
    regulatory_explanation: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PIIRedactionSchema(BaseModel):
    id: str
    entity_type: str
    redacted_text: str
    start_index: int
    end_index: int
    field_path: str
    model_config = ConfigDict(from_attributes=True)


class ModelUsageSchema(BaseModel):
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model_config = ConfigDict(from_attributes=True)


class AgentRunDetailSchema(BaseModel):
    run_id: str
    session_id: str
    user_id: str
    input_text: str
    final_output: Optional[str] = None
    model_name: str
    confidence_score: float
    risk_level: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    latency_ms: int
    retrieved_contexts: List[RetrievedContextSchema] = []
    tool_calls: List[ToolCallSchema] = []
    reasoning_steps: List[ReasoningStepSchema] = []
    decision_summary: Optional[DecisionSummarySchema] = None
    pii_redactions: List[PIIRedactionSchema] = []
    model_usage: Optional[ModelUsageSchema] = None
    model_config = ConfigDict(from_attributes=True)


class SessionTimelineSchema(BaseModel):
    session_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    agent_runs: List[AgentRunDetailSchema] = []
    model_config = ConfigDict(from_attributes=True)
