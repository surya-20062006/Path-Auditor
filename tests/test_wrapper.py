import pytest
from audit.wrapper import AuditedAgentExecutor


def test_audited_agent_executor_full_trace():
    executor = AuditedAgentExecutor(model_name="gpt-4-test")
    payload = executor.execute_agent_task(
        session_id="test-session-123",
        user_id="test-user",
        input_text="Check eligibility for user IN-2026-001 with PAN ABCDE1234F",
        legal_reasoning_redaction=False,
        requested_loan_amount=150000.0,
        annual_income=95000.0
    )

    # Validate all 13 core audit parameters are present
    assert payload.run_id is not None
    assert payload.session_id == "test-session-123"
    assert payload.user_id == "test-user"
    assert payload.input_text is not None
    assert payload.redacted_input is not None
    assert payload.final_output is not None
    assert payload.model_name == "gpt-4-test"
    assert payload.confidence_score > 0.0
    assert payload.risk_level in ["low", "medium", "high", "critical"]
    assert payload.status == "success"
    assert payload.start_time is not None
    assert payload.end_time is not None
    assert payload.latency_ms > 0
    assert len(payload.retrieved_contexts) >= 1
    assert len(payload.tool_calls) == 3
    assert len(payload.reasoning_steps) == 3
    assert len(payload.pii_redactions) >= 1
    assert "total_tokens" in payload.model_usage


def test_audited_agent_executor_legal_reasoning_redaction():
    executor = AuditedAgentExecutor(model_name="gpt-4-test")
    payload = executor.execute_agent_task(
        session_id="test-session-456",
        user_id="test-user-2",
        input_text="Evaluate loan of $50,000",
        legal_reasoning_redaction=True
    )

    for step in payload.reasoning_steps:
        assert step["is_summarized"] is True
        assert step["legal_redacted_flag"] is True
        # Verify proprietary thoughts were summarized
        assert "Standard" in step["thought_content"] or "inquiry" in step["thought_content"] or "assessment" in step["thought_content"]
