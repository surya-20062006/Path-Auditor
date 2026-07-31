from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.models.schema import (
    Session as DBSession, AgentRun, RetrievedContext, ToolCall,
    ReasoningStep, DecisionSummary, PIIRedaction, ModelUsage
)
from backend.core.logger import logger


class DecisionPathReconstructor:
    """
    Enterprise causal chain reconstructor.
    Reconstructs the complete chronological timeline:
    User Input -> Retrieved Context -> Tool Calls -> Reasoning -> Decision -> Final Output
    """

    @staticmethod
    def reconstruct_session_timeline(db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Query DB for session_id and return fully reconstructed causal timeline JSON.
        """
        session_obj = (
            db.query(DBSession)
            .filter(DBSession.session_id == session_id)
            .first()
        )
        if not session_obj:
            logger.warning("Session not found during timeline reconstruction", session_id=session_id)
            return None

        runs = (
            db.query(AgentRun)
            .filter(AgentRun.session_id == session_id)
            .order_by(AgentRun.start_time.asc())
            .all()
        )

        timeline_runs: List[Dict[str, Any]] = []
        for r in runs:
            timeline_runs.append(DecisionPathReconstructor.reconstruct_run_timeline(db, r.run_id))

        return {
            "session_id": session_obj.session_id,
            "user_id": session_obj.user_id,
            "title": session_obj.title or f"Audit Session {session_id[:8]}",
            "created_at": session_obj.created_at.isoformat(),
            "updated_at": session_obj.updated_at.isoformat(),
            "timeline": timeline_runs
        }

    @staticmethod
    def reconstruct_run_timeline(db: Session, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Reconstructs the exact causal flow for a single AgentRun.
        """
        run = (
            db.query(AgentRun)
            .filter(AgentRun.run_id == run_id)
            .first()
        )
        if not run:
            return None

        retrieved_contexts = (
            db.query(RetrievedContext)
            .filter(RetrievedContext.run_id == run_id)
            .order_by(RetrievedContext.rank_order.asc())
            .all()
        )
        tool_calls = (
            db.query(ToolCall)
            .filter(ToolCall.run_id == run_id)
            .order_by(ToolCall.sequence_order.asc())
            .all()
        )
        reasoning_steps = (
            db.query(ReasoningStep)
            .filter(ReasoningStep.run_id == run_id)
            .order_by(ReasoningStep.step_index.asc())
            .all()
        )
        summary = (
            db.query(DecisionSummary)
            .filter(DecisionSummary.run_id == run_id)
            .first()
        )
        pii_items = (
            db.query(PIIRedaction)
            .filter(PIIRedaction.run_id == run_id)
            .all()
        )
        usage = (
            db.query(ModelUsage)
            .filter(ModelUsage.run_id == run_id)
            .first()
        )

        # Build chronological causal flow timeline
        flow_sequence = []
        flow_sequence.append({
            "stage": "USER_INPUT",
            "timestamp": run.start_time.isoformat(),
            "content": run.input_text,
            "pii_redactions_count": len(pii_items)
        })

        if retrieved_contexts:
            flow_sequence.append({
                "stage": "RETRIEVED_CONTEXT",
                "timestamp": run.start_time.isoformat(),
                "items": [
                    {
                        "id": c.id,
                        "source_name": c.source_name,
                        "snippet": c.snippet,
                        "similarity_score": c.similarity_score,
                        "rank_order": c.rank_order
                    }
                    for c in retrieved_contexts
                ]
            })

        for tc in tool_calls:
            flow_sequence.append({
                "stage": "TOOL_CALL",
                "sequence_order": tc.sequence_order,
                "tool_name": tc.tool_name,
                "parameters": tc.parameters,
                "response_output": tc.response_output,
                "execution_time_ms": tc.execution_time_ms,
                "retry_count": tc.retry_count,
                "error_message": tc.error_message
            })

        for step in reasoning_steps:
            flow_sequence.append({
                "stage": "REASONING_STEP",
                "step_index": step.step_index,
                "thought_content": step.thought_content,
                "is_summarized": step.is_summarized,
                "timestamp": step.timestamp.isoformat()
            })

        if summary:
            flow_sequence.append({
                "stage": "DECISION_SUMMARY",
                "why_decision_happened": summary.why_decision_happened,
                "information_considered": summary.information_considered,
                "tools_used": summary.tools_used,
                "rules_applied": summary.rules_applied,
                "outcome": summary.outcome,
                "regulatory_explanation": summary.regulatory_explanation
            })

        flow_sequence.append({
            "stage": "FINAL_OUTPUT",
            "timestamp": (run.end_time or run.start_time).isoformat(),
            "content": run.final_output,
            "confidence_score": run.confidence_score,
            "risk_level": run.risk_level,
            "latency_ms": run.latency_ms
        })

        return {
            "run_id": run.run_id,
            "session_id": run.session_id,
            "user_id": run.user_id,
            "model_name": run.model_name,
            "risk_level": run.risk_level,
            "status": run.status,
            "start_time": run.start_time.isoformat(),
            "end_time": (run.end_time or run.start_time).isoformat(),
            "latency_ms": run.latency_ms,
            "causal_flow": flow_sequence,
            "model_usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
                "estimated_cost_usd": usage.estimated_cost_usd if usage else 0.0
            } if usage else None
        }


reconstructor = DecisionPathReconstructor()
