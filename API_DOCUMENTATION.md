# Decision Path Auditor — REST API Reference

All API requests (except `/auth/login`, `/auth/register`, and `/metrics`) require an HTTP Authorization header:
```http
Authorization: Bearer <jwt_access_token>
```

---

## 1. Authentication Endpoints

### `POST /auth/register`
Register a new enterprise user.
```json
// Request Payload
{
  "email": "auditor@traceai.enterprise",
  "password": "AuditorPassword123!",
  "role": "auditor"
}
```

### `POST /auth/login`
Authenticate and obtain access & refresh JWT tokens.
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=auditor@traceai.enterprise&password=AuditorPassword123!
```

---

## 2. AI Agent Execution & Audit Capture

### `POST /api/v1/run-agent`
Execute AI Agent and record complete 13-point reasoning chain.
```json
// Request Payload
{
  "session_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "input_text": "Evaluate loan eligibility for applicant IN-2026-9921 with PAN ABCDE1234F requesting $150,000",
  "requested_loan_amount": 150000.0,
  "annual_income": 95000.0,
  "model_name": "gpt-4-turbo",
  "legal_reasoning_redaction": false
}
```
```json
// Response Payload (200 OK)
{
  "run_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "session_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "final_output": "APPROVED: Applicant test-user is approved for a loan of $150,000.00 at an APR of 8.25%. Risk classification: LOW.",
  "model_name": "gpt-4-turbo",
  "confidence_score": 0.96,
  "risk_level": "low",
  "latency_ms": 385,
  "pii_redacted_input": "Evaluate loan eligibility for applicant IN-2026-9921 with PAN <REDACTED_PAN_INDIA> requesting $150,000",
  "tool_calls_count": 3,
  "decision_summary": {
    "plain_english_summary": "Summary: The AI Agent evaluated the request and made a decision based on verified identity...",
    "why_decision_happened": "The AI Agent evaluated the request against established underwriting thresholds.",
    "outcome": "APPROVED: Applicant is approved for a loan of $150,000.00."
  }
}
```

---

## 3. Audit Reconstructor & Search Endpoints

### `GET /api/v1/audit/session/{session_id}`
Reconstruct causal timeline (`User Input -> Context -> Tools -> Reasoning -> Decision -> Output`).

### `GET /api/v1/audit/search?risk_level=high&query_text=loan`
Multi-filter audit search across all 11 normalized database tables.

---

## 4. Regulatory Explanations & PII Inspection

### `POST /api/v1/audit/regulatory-explanation`
Generate a formal regulatory challenge response document.
```json
{ "session_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d" }
```

### `POST /api/v1/unredact` (RBAC Gated: Admin / Auditor)
Decrypt an AES-256-GCM encrypted token.
```json
{ "encrypted_token": "gcm:base64_encoded_ciphertext_payload..." }
```

---

## 5. Observability & Health

### `GET /api/v1/health`
Returns real-time health checks for PostgreSQL, Redis, LLM provider, AWS S3, and Celery Queue.

### `GET /metrics`
Returns OpenMetrics / Prometheus formatted server metrics.
