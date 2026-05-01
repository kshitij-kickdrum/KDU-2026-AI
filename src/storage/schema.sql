PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_history TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    state TEXT DEFAULT 'active' CHECK (state IN ('active', 'requires_user_input', 'completed'))
);

CREATE TABLE IF NOT EXISTS case_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    fact_type TEXT NOT NULL CHECK (fact_type IN ('numerical', 'transactional', 'entity', 'date')),
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_case_facts_session_type
ON case_facts(session_id, fact_type);

CREATE TABLE IF NOT EXISTS delegation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    coordinator_query TEXT NOT NULL,
    sub_agent_name TEXT NOT NULL,
    delegation_order INTEGER NOT NULL,
    context_payload TEXT NOT NULL,
    sub_agent_response TEXT NOT NULL,
    delegated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    tool_name TEXT PRIMARY KEY NOT NULL,
    failure_count INTEGER DEFAULT 0,
    state TEXT DEFAULT 'closed' CHECK (state IN ('closed', 'open', 'half_open')),
    last_failure_at TIMESTAMP NULL,
    last_success_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS tool_invocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    parameters TEXT NOT NULL,
    response_status TEXT NOT NULL CHECK (response_status IN ('success', 'error', 'timeout')),
    response_data TEXT NULL,
    error_message TEXT NULL,
    invoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_tool_invocations_tool_status
ON tool_invocations(tool_name, response_status);

CREATE TABLE IF NOT EXISTS required_fields_schema (
    operation_type TEXT PRIMARY KEY NOT NULL,
    required_fields TEXT NOT NULL,
    field_descriptions TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS missing_fields_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    missing_fields TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS execution_plans (
    plan_id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL,
    plan_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'executing', 'completed', 'failed')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS execution_steps (
    step_id TEXT PRIMARY KEY NOT NULL,
    plan_id TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    description TEXT NOT NULL,
    action_type TEXT NOT NULL,
    parameters TEXT NOT NULL,
    depends_on TEXT NULL,
    expected_output TEXT NOT NULL,
    actual_output TEXT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'executing', 'completed', 'failed', 'skipped')),
    executed_at TIMESTAMP NULL,
    FOREIGN KEY (plan_id) REFERENCES execution_plans(plan_id)
);

CREATE INDEX IF NOT EXISTS idx_execution_steps_plan_order
ON execution_steps(plan_id, step_order);

INSERT OR IGNORE INTO required_fields_schema (
    operation_type,
    required_fields,
    field_descriptions
) VALUES (
    'update_banking_details',
    '["routing_number", "account_number", "account_holder_name"]',
    '{"routing_number":"9 digit routing number","account_number":"Bank account number","account_holder_name":"Name on the account"}'
);

INSERT OR IGNORE INTO required_fields_schema (
    operation_type,
    required_fields,
    field_descriptions
) VALUES (
    'process_card_payment',
    '["card_number", "expiration_date", "cvv", "amount"]',
    '{"card_number":"Payment card number","expiration_date":"Card expiration date","cvv":"Card verification value","amount":"Payment amount"}'
);
