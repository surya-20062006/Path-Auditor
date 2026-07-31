import pytest
from audit.wrapper import AuditedAgentExecutor
from audit.summarizer import summarizer_generator
from backend.api.agent import persist_trace_to_db


def test_plain_english_summary_generation():
    executor = AuditedAgentExecutor(model_name="gpt-4-test")
    payload = executor.execute_agent_task(
        session_id="summary-session-001",
        user_id="test-user-sum",
        input_text="Evaluate loan eligibility",
        legal_reasoning_redaction=False
    )

    summary_dict = summarizer_generator.generate_plain_english_summary(payload)
    assert "plain_english_summary" in summary_dict
    assert "why_decision_happened" in summary_dict
    assert "tools_used" in summary_dict
    assert "rules_applied" in summary_dict
    assert "kyc_verification_check" in summary_dict["tools_used"]


def test_regulatory_challenge_explanation_generation(db_session):
    executor = AuditedAgentExecutor(model_name="gpt-4-test")
    payload = executor.execute_agent_task(
        session_id="reg-session-002",
        user_id="test-user-reg",
        input_text="Evaluate loan eligibility for applicant",
        legal_reasoning_redaction=False
    )
    persist_trace_to_db(db_session, payload)

    challenge_doc = summarizer_generator.generate_regulatory_challenge_explanation(db_session, session_id="reg-session-002")
    assert challenge_doc is not None
    assert "REGULATORY DECISION AUDIT EXPLANATION" in challenge_doc["regulatory_response_document"]
    assert challenge_doc["session_id"] == "reg-session-002"
