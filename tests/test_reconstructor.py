import pytest
from audit.wrapper import AuditedAgentExecutor
from audit.reconstructor import DecisionPathReconstructor
from backend.api.agent import persist_trace_to_db


def test_decision_path_reconstructor_timeline(db_session):
    executor = AuditedAgentExecutor(model_name="gpt-4-test")
    payload = executor.execute_agent_task(
        session_id="recon-session-789",
        user_id="test-user-recon",
        input_text="Evaluate loan for user",
        legal_reasoning_redaction=False
    )

    # Persist trace to SQLite DB
    persist_trace_to_db(db_session, payload)

    # Reconstruct timeline
    timeline_data = DecisionPathReconstructor.reconstruct_session_timeline(db_session, session_id="recon-session-789")

    assert timeline_data is not None
    assert timeline_data["session_id"] == "recon-session-789"
    assert len(timeline_data["timeline"]) == 1

    run_timeline = timeline_data["timeline"][0]
    stages = [item["stage"] for item in run_timeline["causal_flow"]]

    # Verify chronological sequence of causal stages
    assert "USER_INPUT" in stages
    assert "RETRIEVED_CONTEXT" in stages
    assert "TOOL_CALL" in stages
    assert "REASONING_STEP" in stages
    assert "DECISION_SUMMARY" in stages
    assert "FINAL_OUTPUT" in stages
