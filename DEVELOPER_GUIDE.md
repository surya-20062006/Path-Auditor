# Decision Path Auditor — Developer Onboarding & Extensibility Guide

## 1. Adding a New Enterprise Tool to the Agent Registry
To allow the AI Agent to execute new financial, medical, or security verification tools, register them in `tools/agent_tools.py`:

```python
# 1. Define your deterministic or external API tool function
def fraud_watchlist_screening(user_id: str, country_code: str) -> dict:
    """
    Checks international OFAC/AML watchlists for the applicant.
    """
    return {
        "user_id": user_id,
        "country": country_code,
        "is_flagged": False,
        "screening_reference": f"SCR-2026-{hash(user_id) % 1000}"
    }

# 2. Register function in the enterprise tools registry
ENTERPRISE_TOOLS_REGISTRY["fraud_watchlist_screening"] = fraud_watchlist_screening
```
The **AuditedAgentExecutor** (`audit/wrapper.py`) will automatically record execution time, JSON input/output parameters, sequence order, and retry counts in the `tool_calls` table.

---

## 2. Extending the Zero-Leakage PII Redactor
To scan for custom regional identifiers (e.g., UK National Insurance Number or Australian TFN), add custom regex recognizers in `audit/redactor.py`:

```python
from presidio_analyzer import Pattern, PatternRecognizer

uk_nino_pattern = Pattern(
    name="UK_NINO_PATTERN",
    regex=r"[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}[0-9]{6}[A-D\s]{1}",
    score=0.85
)
uk_nino_recognizer = PatternRecognizer(
    supported_entity="UK_NINO",
    patterns=[uk_nino_pattern]
)
analyzer.registry.add_recognizer(uk_nino_recognizer)
```

---

## 3. Customizing RBAC & Role Hierarchies
Role permissions are managed via `RoleChecker` decorators in `backend/auth/jwt.py`:
- `@Depends(require_admin)`: Restricted to Admin users.
- `@Depends(require_auditor_or_admin)`: Allowed for Admin and Auditor roles (e.g., `/unredact` PII decryption).
- `@Depends(require_developer_or_above)`: Allowed for Admin, Auditor, and Developer roles.
- `@Depends(get_current_user)`: Authenticated access for any valid JWT bearer token.

---

## 4. Running Tests Locally
```bash
# Execute complete unit, database, and integration test suite
pytest -v

# Generate HTML code coverage report
pytest --cov=audit --cov=backend --cov-report=html

# Launch Locust stress & concurrency load test
locust -f tests/locustfile.py --host=http://localhost:8000
```
