# Decision Path Auditor — Entity-Relationship (ER) Diagram & Database Dictionary

## 1. Complete 11-Table ER Diagram
```mermaid
erDiagram
    USERS ||--o{ SESSIONS : "owns"
    USERS ||--o{ AGENT_RUNS : "initiates"
    USERS ||--o{ AUDIT_LOGS : "acts_in"
    SESSIONS ||--o{ AGENT_RUNS : "contains"
    AGENT_RUNS ||--o{ RETRIEVED_CONTEXTS : "retrieves"
    AGENT_RUNS ||--o{ TOOL_CALLS : "executes"
    AGENT_RUNS ||--o{ REASONING_STEPS : "reasons"
    AGENT_RUNS ||--o| DECISION_SUMMARIES : "generates"
    AGENT_RUNS ||--o{ PII_REDACTIONS : "redacts"
    AGENT_RUNS ||--o| MODEL_USAGE : "consumes"

    USERS {
        uuid id PK
        string email
        string role "admin|auditor|developer|customer"
        string password_hash
        timestamp created_at
    }

    SESSIONS {
        string session_id PK
        uuid user_id FK
        string title
        timestamp created_at
        timestamp updated_at
    }

    AGENT_RUNS {
        uuid run_id PK
        string session_id FK
        uuid user_id FK
        text input_text
        text final_output
        string model_name
        float confidence_score
        string risk_level "low|medium|high|critical"
        string status "success|error|timeout"
        timestamp start_time
        timestamp end_time
        int latency_ms
    }

    RETRIEVED_CONTEXTS {
        uuid id PK
        uuid run_id FK
        string source_name
        text snippet
        float similarity_score
        int rank_order
    }

    TOOL_CALLS {
        uuid id PK
        uuid run_id FK
        string tool_name
        text parameters
        text response_output
        int execution_time_ms
        string error_message
        int retry_count
        int sequence_order
    }

    REASONING_STEPS {
        uuid id PK
        uuid run_id FK
        int step_index
        text thought_content
        boolean is_summarized
        boolean legal_redacted_flag
        timestamp timestamp
    }

    DECISION_SUMMARIES {
        uuid id PK
        uuid run_id FK
        text plain_english_summary
        text why_decision_happened
        text information_considered
        text tools_used
        text rules_applied
        text outcome
        text regulatory_explanation
        timestamp created_at
    }

    PII_REDACTIONS {
        uuid id PK
        uuid run_id FK
        string entity_type
        string original_encrypted
        text redacted_text
        int start_index
        int end_index
        string field_path
    }

    MODEL_USAGE {
        uuid id PK
        uuid run_id FK
        string model_name
        int prompt_tokens
        int completion_tokens
        int total_tokens
        float estimated_cost_usd
    }

    AUDIT_LOGS {
        uuid id PK
        string correlation_id
        string event_type
        uuid actor_id FK
        string entity_type
        string entity_id
        text action_details
        timestamp timestamp
    }

    SYSTEM_METRICS {
        uuid id PK
        string metric_name
        float metric_value
        string dimensions
        timestamp recorded_at
    }
```

## 2. Table Definitions & Compliance Notes
- **`agent_runs`**: Represents an individual atomic AI Agent invocation. Maintains foreign keys to both `users` and `sessions`.
- **`pii_redactions`**: Stores sensitive PII tokens identified by Microsoft Presidio. `original_encrypted` holds the `AES-256-GCM` base64 ciphertext; `redacted_text` holds `<REDACTED_ENTITY>`.
- **`reasoning_steps`**: Captures intermediate thought chains. If `legal_redacted_flag=True`, `thought_content` contains an auditable non-proprietary summary while preserving sequence indexes (`step_index`).
- **`decision_summaries`**: Contains 5-part customer plain English summaries (`why_decision_happened`, `information_considered`, `tools_used`, `rules_applied`, `outcome`) and formal regulatory challenge explanations.
