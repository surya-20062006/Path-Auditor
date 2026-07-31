import time
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.core.config import settings
from backend.core.logger import logger
from backend.core.metrics import (
    TOKEN_USAGE_COUNTER, AGENT_RUNS_COUNTER, TOOL_CALLS_COUNTER, AGENT_RUN_LATENCY
)
from audit.redactor import pii_redactor
from tools.agent_tools import ENTERPRISE_TOOLS_REGISTRY


class AuditTracePayload:
    """
    Structured envelope holding the complete 13-point reasoning and execution trace
    to be persisted to PostgreSQL and archived to AWS S3.
    """
    def __init__(
        self,
        run_id: str,
        session_id: str,
        user_id: str,
        input_text: str,
        redacted_input: str,
        final_output: str,
        model_name: str,
        confidence_score: float,
        risk_level: str,
        status: str,
        start_time: datetime,
        end_time: datetime,
        latency_ms: int,
        retrieved_contexts: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        reasoning_steps: List[Dict[str, Any]],
        pii_redactions: List[Dict[str, Any]],
        model_usage: Dict[str, Any],
        error_message: Optional[str] = None
    ):
        self.run_id = run_id
        self.session_id = session_id
        self.user_id = user_id
        self.input_text = input_text
        self.redacted_input = redacted_input
        self.final_output = final_output
        self.model_name = model_name
        self.confidence_score = confidence_score
        self.risk_level = risk_level
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.latency_ms = latency_ms
        self.retrieved_contexts = retrieved_contexts
        self.tool_calls = tool_calls
        self.reasoning_steps = reasoning_steps
        self.pii_redactions = pii_redactions
        self.model_usage = model_usage
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "input_text": self.input_text,
            "redacted_input": self.redacted_input,
            "final_output": self.final_output,
            "model_name": self.model_name,
            "confidence_score": self.confidence_score,
            "risk_level": self.risk_level,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "latency_ms": self.latency_ms,
            "retrieved_contexts": self.retrieved_contexts,
            "tool_calls": self.tool_calls,
            "reasoning_steps": self.reasoning_steps,
            "pii_redactions": self.pii_redactions,
            "model_usage": self.model_usage,
            "error_message": self.error_message,
        }


class AuditedAgentExecutor:
    """
    LangGraph & LangChain Agent Wrapper that automatically captures:
    • User Input
    • Retrieved Context
    • Tool Calls & Parameters
    • Intermediate Reasoning (with legal summary redaction fallback)
    • Final Decision & Output
    • Model, Token Usage, Latency, Errors, Retry Count, Confidence Score & Risk Level
    """

    def __init__(self, model_name: str = settings.DEFAULT_MODEL_NAME, provider: str = settings.DEFAULT_LLM_PROVIDER):
        self.model_name = model_name
        self.provider = provider

    def execute_agent_task(
        self,
        session_id: str,
        user_id: str,
        input_text: str,
        legal_reasoning_redaction: bool = False,
        requested_loan_amount: float = 150000.0,
        annual_income: float = 95000.0
    ) -> AuditTracePayload:
        start_time = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())
        start_perf = time.perf_counter()

        # 1. PII Redaction on User Input
        redacted_input, pii_redactions = pii_redactor.redact_text(input_text, field_path="input_text")

        # 2. Context Retrieval Simulation (Vector DB / Regulatory Document lookup)
        retrieved_contexts = [
            {
                "source_name": "Regulatory Compliance Handbook Section 402(B)",
                "snippet": "Loan requests exceeding 3.5x annual income must undergo strict underwriting review or receive a HIGH risk designation.",
                "similarity_score": 0.94,
                "rank_order": 1
            },
            {
                "source_name": "KYC & AML Directive 2026-EU/US",
                "snippet": "All applicants must present valid identity documentation without active AML watchlist flags prior to loan approval.",
                "similarity_score": 0.89,
                "rank_order": 2
            }
        ]

        tool_calls: List[Dict[str, Any]] = []
        reasoning_steps: List[Dict[str, Any]] = []
        error_message = None
        status = "success"

        try:
            # Step A: Reasoning - Check KYC Verification
            step1_thought = f"Analyzing applicant identity verification for user {user_id}. Executing KYC verification check."
            if legal_reasoning_redaction:
                step1_thought = "Standard regulatory compliance check performed on applicant identification records."
            reasoning_steps.append({
                "step_index": 1,
                "thought_content": step1_thought,
                "is_summarized": legal_reasoning_redaction,
                "legal_redacted_flag": legal_reasoning_redaction,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Execute Tool 1: kyc_verification_check
            t1_start = time.perf_counter()
            t1_params = {"user_id": user_id, "document_type": "PAN"}
            t1_output = ENTERPRISE_TOOLS_REGISTRY["kyc_verification_check"](**t1_params)
            t1_latency_ms = int((time.perf_counter() - t1_start) * 1000)
            tool_calls.append({
                "tool_name": "kyc_verification_check",
                "parameters": json.dumps(t1_params),
                "response_output": json.dumps(t1_output),
                "execution_time_ms": t1_latency_ms,
                "error_message": None,
                "retry_count": 0,
                "sequence_order": 1
            })
            TOOL_CALLS_COUNTER.labels(tool_name="kyc_verification_check", status="success").inc()

            # Step B: Reasoning - Credit Score Lookup
            step2_thought = "Applicant KYC verified. Executing credit bureau lookup to evaluate credit score and DTI ratio."
            if legal_reasoning_redaction:
                step2_thought = "Credit bureau inquiry executed in accordance with Fair Credit Reporting regulations."
            reasoning_steps.append({
                "step_index": 2,
                "thought_content": step2_thought,
                "is_summarized": legal_reasoning_redaction,
                "legal_redacted_flag": legal_reasoning_redaction,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            t2_start = time.perf_counter()
            t2_params = {"user_id": user_id, "loan_amount": requested_loan_amount}
            t2_output = ENTERPRISE_TOOLS_REGISTRY["credit_score_lookup"](**t2_params)
            t2_latency_ms = int((time.perf_counter() - t2_start) * 1000)
            tool_calls.append({
                "tool_name": "credit_score_lookup",
                "parameters": json.dumps(t2_params),
                "response_output": json.dumps(t2_output),
                "execution_time_ms": t2_latency_ms,
                "error_message": None,
                "retry_count": 0,
                "sequence_order": 2
            })
            TOOL_CALLS_COUNTER.labels(tool_name="credit_score_lookup", status="success").inc()

            # Step C: Reasoning - Loan Eligibility Calculator
            credit_score = t2_output["credit_score"]
            step3_thought = f"Credit score retrieved: {credit_score}. Calculating maximum allowable loan and interest tier."
            if legal_reasoning_redaction:
                step3_thought = "Underwriting algorithmic assessment completed using verified credit and income metrics."
            reasoning_steps.append({
                "step_index": 3,
                "thought_content": step3_thought,
                "is_summarized": legal_reasoning_redaction,
                "legal_redacted_flag": legal_reasoning_redaction,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            t3_start = time.perf_counter()
            t3_params = {
                "credit_score": credit_score,
                "annual_income": annual_income,
                "requested_loan": requested_loan_amount
            }
            t3_output = ENTERPRISE_TOOLS_REGISTRY["loan_eligibility_calculator"](**t3_params)
            t3_latency_ms = int((time.perf_counter() - t3_start) * 1000)
            tool_calls.append({
                "tool_name": "loan_eligibility_calculator",
                "parameters": json.dumps(t3_params),
                "response_output": json.dumps(t3_output),
                "execution_time_ms": t3_latency_ms,
                "error_message": None,
                "retry_count": 0,
                "sequence_order": 3
            })
            TOOL_CALLS_COUNTER.labels(tool_name="loan_eligibility_calculator", status="success").inc()

            # Step D: Final Decision Synthesis
            is_eligible = t3_output["is_eligible"]
            risk_level = t3_output["risk_level"]
            interest_rate = t3_output["assigned_interest_rate_pct"]
            confidence_score = 0.96 if is_eligible else 0.92

            if is_eligible:
                final_output = (
                    f"APPROVED: Applicant {user_id} is approved for a loan of ${requested_loan_amount:,.2f} "
                    f"at an annual percentage rate (APR) of {interest_rate}%. Credit Score: {credit_score} ({t2_output['credit_tier']}). "
                    f"Risk classification: {risk_level.upper()}."
                )
            else:
                final_output = (
                    f"DECLINED: Applicant {user_id} does not meet eligibility criteria for a loan of ${requested_loan_amount:,.2f}. "
                    f"Credit Score: {credit_score} ({t2_output['credit_tier']}). Maximum allowable borrowing limit "
                    f"is ${t3_output['max_allowable_loan_usd']:,.2f}. Risk classification: {risk_level.upper()}."
                )

        except Exception as exc:
            status = "error"
            error_message = str(exc)
            final_output = f"ERROR: Agent reasoning failed during tool execution: {error_message}"
            risk_level = "critical"
            confidence_score = 0.0

        end_time = datetime.now(timezone.utc)
        total_latency_ms = int((time.perf_counter() - start_perf) * 1000)

        # Model Token Consumption Calculation
        prompt_tokens = int(len(input_text) * 0.45) + 320
        completion_tokens = int(len(final_output) * 0.45) + 180
        total_tokens = prompt_tokens + completion_tokens
        # Estimate usage cost (e.g., $0.01 per 1K tokens)
        estimated_cost_usd = round((total_tokens / 1000.0) * 0.015, 6)

        model_usage = {
            "model_name": self.model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
        }

        # Update Prometheus Metrics
        TOKEN_USAGE_COUNTER.labels(model_name=self.model_name, token_type="prompt").inc(prompt_tokens)
        TOKEN_USAGE_COUNTER.labels(model_name=self.model_name, token_type="completion").inc(completion_tokens)
        AGENT_RUNS_COUNTER.labels(status=status, risk_level=risk_level, model_name=self.model_name).inc()
        AGENT_RUN_LATENCY.labels(model_name=self.model_name, status=status).observe(total_latency_ms / 1000.0)

        trace_payload = AuditTracePayload(
            run_id=run_id,
            session_id=session_id,
            user_id=user_id,
            input_text=input_text,
            redacted_input=redacted_input,
            final_output=final_output,
            model_name=self.model_name,
            confidence_score=confidence_score,
            risk_level=risk_level,
            status=status,
            start_time=start_time,
            end_time=end_time,
            latency_ms=total_latency_ms,
            retrieved_contexts=retrieved_contexts,
            tool_calls=tool_calls,
            reasoning_steps=reasoning_steps,
            pii_redactions=pii_redactions,
            model_usage=model_usage,
            error_message=error_message
        )

        logger.info(
            "Agent task execution completed",
            run_id=run_id,
            session_id=session_id,
            user_id=user_id,
            status=status,
            risk_level=risk_level,
            latency_ms=total_latency_ms,
            tool_calls_count=len(tool_calls)
        )

        return trace_payload
