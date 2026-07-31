import pytest
from fastapi import status


def test_health_check_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "database" in data["services"]
    assert "llm_engine" in data["services"]


def test_user_registration_and_login(client):
    # Test Register
    reg_payload = {
        "email": "integration@traceai.enterprise",
        "password": "SecurePassword123!",
        "role": "auditor"
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_201_CREATED
    assert reg_res.json()["email"] == "integration@traceai.enterprise"

    # Test Login
    login_res = client.post(
        "/auth/login",
        data={"username": "integration@traceai.enterprise", "password": "SecurePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == status.HTTP_200_OK
    assert "access_token" in login_res.json()


def test_run_agent_and_get_timeline(client, auditor_token):
    headers = {"Authorization": f"Bearer {auditor_token}"}
    run_payload = {
        "session_id": "api-test-session-uuid",
        "input_text": "Evaluate loan eligibility for applicant IN-2026-991 with PAN ABCDE1234F",
        "requested_loan_amount": 100000.0,
        "annual_income": 95000.0,
        "model_name": "gpt-4-turbo",
        "legal_reasoning_redaction": False
    }
    run_res = client.post("/api/v1/run-agent", json=run_payload, headers=headers)
    assert run_res.status_code == status.HTTP_200_OK
    run_data = run_res.json()
    assert run_data["session_id"] == "api-test-session-uuid"
    assert run_data["risk_level"] in ["low", "medium", "high", "critical"]
    assert run_data["tool_calls_count"] == 3

    # Test Timeline Reconstruction API
    timeline_res = client.get("/api/v1/audit/session/api-test-session-uuid", headers=headers)
    assert timeline_res.status_code == status.HTTP_200_OK
    timeline_data = timeline_res.json()
    assert timeline_data["session_id"] == "api-test-session-uuid"
    assert len(timeline_data["timeline"]) == 1

    # Test Multi-Filter Search API
    search_res = client.get("/api/v1/audit/search?session_id=api-test-session-uuid", headers=headers)
    assert search_res.status_code == status.HTTP_200_OK
    assert len(search_res.json()) >= 1


def test_pii_redaction_and_unredact_api(client, auditor_token):
    headers = {"Authorization": f"Bearer {auditor_token}"}
    redact_res = client.post(
        "/api/v1/redact",
        json={"text": "Applicant email is test.user@enterprise.org and PAN is ABCDE1234F"},
        headers=headers
    )
    assert redact_res.status_code == status.HTTP_200_OK
    redact_data = redact_res.json()
    assert redact_data["total_redactions"] >= 2
    assert "test.user@enterprise.org" not in redact_data["redacted_text"]

    # Test Unredact API as Auditor
    encrypted_token = redact_data["redactions"][0]["original_encrypted"]
    unredact_res = client.post(
        "/api/v1/unredact",
        json={"encrypted_token": encrypted_token},
        headers=headers
    )
    assert unredact_res.status_code == status.HTTP_200_OK
    assert "plaintext_value" in unredact_res.json()
