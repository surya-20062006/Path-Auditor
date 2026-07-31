import uuid
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.postgres import get_db
from backend.models.schema import (
    User, Session as DBSession, AgentRun, RetrievedContext, ToolCall,
    ReasoningStep, DecisionSummary, PIIRedaction, ModelUsage, AuditLog
)
from backend.auth.jwt import get_current_user
from backend.core.logger import logger
from audit.wrapper import AuditedAgentExecutor, AuditTracePayload
from audit.summarizer import summarizer_generator

router = APIRouter(tags=["AI Agent Execution"])


class AgentRunRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Existing session UUID or leave blank for new session")
    input_text: str = Field(..., description="Prompt or query for the AI Agent")
    model_name: str = Field(default="gpt-4-turbo", description="OpenAI GPT-4.1 | Claude | Gemini")
    legal_reasoning_redaction: bool = Field(default=False, description="Redact intermediate proprietary thoughts into summaries")
    requested_loan_amount: float = Field(default=150000.0, description="Loan amount in USD")
    annual_income: float = Field(default=95000.0, description="Applicant annual income in USD")


class AgentRunResponse(BaseModel):
    run_id: str
    session_id: str
    final_output: str
    model_name: str
    confidence_score: float
    risk_level: str
    latency_ms: int
    pii_redacted_input: str
    tool_calls_count: int
    decision_summary: Dict[str, str]


def persist_trace_to_db(db: Session, payload: AuditTracePayload) -> DecisionSummary:
    """
    Synchronously persist complete 13-point audit trace into 11 normalized Postgres tables.
    """
    # 1. Ensure Session exists
    session_obj = db.query(DBSession).filter(DBSession.session_id == payload.session_id).first()
    if not session_obj:
        session_obj = DBSession(
            session_id=payload.session_id,
            user_id=payload.user_id,
            title=f"Session - {payload.input_text[:35]}..."
        )
        db.add(session_obj)

    # 2. Insert AgentRun
    run_obj = AgentRun(
        run_id=payload.run_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
        input_text=payload.input_text,
        final_output=payload.final_output,
        model_name=payload.model_name,
        confidence_score=payload.confidence_score,
        risk_level=payload.risk_level,
        status=payload.status,
        start_time=payload.start_time,
        end_time=payload.end_time,
        latency_ms=payload.latency_ms
    )
    db.add(run_obj)

    # 3. Insert Retrieved Contexts
    for ctx in payload.retrieved_contexts:
        db.add(RetrievedContext(
            run_id=payload.run_id,
            source_name=ctx["source_name"],
            snippet=ctx["snippet"],
            similarity_score=ctx.get("similarity_score", 0.0),
            rank_order=ctx.get("rank_order", 1)
        ))

    # 4. Insert Tool Calls
    for tc in payload.tool_calls:
        db.add(ToolCall(
            run_id=payload.run_id,
            tool_name=tc["tool_name"],
            parameters=tc["parameters"],
            response_output=tc["response_output"],
            execution_time_ms=tc["execution_time_ms"],
            error_message=tc.get("error_message"),
            retry_count=tc.get("retry_count", 0),
            sequence_order=tc.get("sequence_order", 1)
        ))

    # 5. Insert Reasoning Steps
    for step in payload.reasoning_steps:
        db.add(ReasoningStep(
            run_id=payload.run_id,
            step_index=step["step_index"],
            thought_content=step["thought_content"],
            is_summarized=step.get("is_summarized", False),
            legal_redacted_flag=step.get("legal_redacted_flag", False)
        ))

    # 6. Insert PII Redactions
    for pii in payload.pii_redactions:
        db.add(PIIRedaction(
            run_id=payload.run_id,
            entity_type=pii["entity_type"],
            original_encrypted=pii["original_encrypted"],
            redacted_text=pii["redacted_text"],
            start_index=pii.get("start_index", 0),
            end_index=pii.get("end_index", 0),
            field_path=pii.get("field_path", "input_text")
        ))

    # 7. Insert Model Usage
    usage_dict = payload.model_usage
    db.add(ModelUsage(
        run_id=payload.run_id,
        model_name=usage_dict["model_name"],
        prompt_tokens=usage_dict["prompt_tokens"],
        completion_tokens=usage_dict["completion_tokens"],
        total_tokens=usage_dict["total_tokens"],
        estimated_cost_usd=usage_dict["estimated_cost_usd"]
    ))

    # 8. Generate & Insert Plain English Decision Summary
    summary_data = summarizer_generator.generate_plain_english_summary(payload)
    decision_summary = DecisionSummary(
        run_id=payload.run_id,
        plain_english_summary=summary_data["plain_english_summary"],
        why_decision_happened=summary_data["why_decision_happened"],
        information_considered=summary_data["information_considered"],
        tools_used=summary_data["tools_used"],
        rules_applied=summary_data["rules_applied"],
        outcome=summary_data["outcome"]
    )
    db.add(decision_summary)

    # 9. Log Audit Trail Record
    db.add(AuditLog(
        correlation_id=payload.run_id,
        event_type="AGENT_EXECUTION_AUDIT",
        actor_id=payload.user_id,
        entity_type="AgentRun",
        entity_id=payload.run_id,
        action_details=f"Captured {len(payload.tool_calls)} tool calls and {len(payload.pii_redactions)} PII redactions. Risk: {payload.risk_level.upper()}"
    ))

    db.commit()
    return decision_summary


@router.post("/run-agent", response_model=AgentRunResponse)
def execute_agent_and_record_trace(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Primary agent execution endpoint.
    Automatically captures input, context, tools, reasoning, token usage, latency, and risk classification.
    """
    session_id = request.session_id or str(uuid.uuid4())
    executor = AuditedAgentExecutor(model_name=request.model_name)

    trace_payload = executor.execute_agent_task(
        session_id=session_id,
        user_id=current_user.id,
        input_text=request.input_text,
        legal_reasoning_redaction=request.legal_reasoning_redaction,
        requested_loan_amount=request.requested_loan_amount,
        annual_income=request.annual_income
    )

    summary_obj = persist_trace_to_db(db, trace_payload)

    return AgentRunResponse(
        run_id=trace_payload.run_id,
        session_id=trace_payload.session_id,
        final_output=trace_payload.final_output,
        model_name=trace_payload.model_name,
        confidence_score=trace_payload.confidence_score,
        risk_level=trace_payload.risk_level,
        latency_ms=trace_payload.latency_ms,
        pii_redacted_input=trace_payload.redacted_input,
        tool_calls_count=len(trace_payload.tool_calls),
        decision_summary={
            "plain_english_summary": summary_obj.plain_english_summary,
            "why_decision_happened": summary_obj.why_decision_happened,
            "outcome": summary_obj.outcome
        }
    )
