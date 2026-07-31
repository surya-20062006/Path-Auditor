import uuid
from locust import HttpUser, task, between


class DecisionPathAuditorLoadTest(HttpUser):
    """
    Locust performance and stress load testing user.
    Simulates high-throughput concurrent agent executions and timeline queries.
    """
    wait_time = between(1, 3)
    access_token = None

    def on_start(self):
        # Register and login test load user
        email = f"loaduser_{uuid.uuid4().hex[:6]}@traceai.enterprise"
        password = "LoadTestPassword123!"
        self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "role": "auditor"
        })
        login_res = self.client.post(
            "/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_res.status_code == 200:
            self.access_token = login_res.json()["access_token"]

    @task(3)
    def test_run_agent_load(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        session_id = str(uuid.uuid4())
        self.client.post("/api/v1/run-agent", json={
            "session_id": session_id,
            "input_text": "Evaluate loan eligibility for applicant IN-2026-9921 with PAN ABCDE1234F requesting $150,000",
            "requested_loan_amount": 150000.0,
            "annual_income": 95000.0,
            "model_name": "gpt-4-turbo",
            "legal_reasoning_redaction": False
        }, headers=headers)

    @task(1)
    def test_health_check_load(self):
        self.client.get("/api/v1/health")

    @task(2)
    def test_search_audit_runs_load(self):
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        self.client.get("/api/v1/audit/search?limit=20", headers=headers)
