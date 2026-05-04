# AgentKit Orchestration Lab Answers

This document answers the questions from `problem-statement.txt` using the implementation in this repository.

## Phase 1: Loop Detection & Circuit Breaker

### How many retries does the agent attempt before stopping?

The system stops after **3 consecutive failures**.

The threshold is configured in `config/models.yml`:

```yaml
circuit_breaker:
  threshold: 3
  timeout_seconds: 60
```

At runtime, `LoopDetectionAgent.run_circuit_breaker_demo()` invokes the failing `query_internal_database` tool up to the configured threshold. The tool intentionally raises a `RuntimeError("500 internal database error")`. Each failure is recorded by `CircuitBreaker.record_failure()`. Once the failure count reaches 3, the circuit breaker moves to the `open` state.

### How does the Circuit Breaker stop execution after 3 consecutive failures?

The circuit breaker stores failure state in SQLite in the `circuit_breaker_state` table. For each failed tool call:

1. `ToolRuntime.invoke()` calls the tool handler.
2. The handler fails.
3. `ToolRuntime` records the failure through `CircuitBreaker.record_failure(tool_name)`.
4. When the count reaches the threshold, the state becomes `open`.
5. Future calls to that tool are blocked by `CircuitBreaker.ensure_allowed()`.

The fallback response returned to the user is:

```text
I'm unable to access that tool right now due to repeated failures. Please try again later or contact support if the issue persists.
```

### How is loop detection logged?

When the failure count reaches the threshold, `CircuitBreaker.record_failure()` logs:

```text
Loop detected: tool=query_internal_database, failure_count=3, state=OPEN
```

Tool failures and blocked calls are also stored in the `tool_invocations` table.

## Phase 2: Coordinator & Agent Isolation

### How does the system handle "What is John's salary and how much PTO does he have?"

The query is routed to `CoordinatorAgent` by `OrchestrationEngine._route_query()`.

The Coordinator has only delegation tools:

- `delegate_to_finance`
- `delegate_to_hr`
- `analyze_query`

It does not receive salary, PTO, payroll, or HR data tools directly. For this query:

1. The Coordinator identifies that salary belongs to Finance.
2. It calls `delegate_to_finance`.
3. `FinanceAgent` uses `query_employee_salary("John")`, which returns `$85,000`.
4. The Coordinator identifies that PTO belongs to HR.
5. It calls `delegate_to_hr`.
6. `HRAgent` uses `query_pto_balance("John")`, which returns `15 PTO days`.
7. The Coordinator integrates both specialist responses into a final answer.

### How does the Coordinator sequence delegation?

Each delegation call is logged with an incrementing `delegation_order` in the `delegation_logs` table. The order is maintained by `CoordinatorAgent._log_delegation()`.

This gives an auditable sequence such as:

1. FinanceAgent receives the salary task.
2. HRAgent receives the PTO task.
3. Coordinator combines the results.

### Why is tool isolation critical?

Tool isolation reduces prompt bloat because each agent only receives the tools it can actually use. The Finance agent receives finance tools only, the HR agent receives HR tools only, and the Coordinator receives delegation tools only.

This improves reliability because:

- The Coordinator cannot accidentally call low-level domain tools.
- Finance cannot perform HR actions.
- HR cannot perform finance actions.
- The LLM has fewer tool choices, which reduces tool-selection errors.
- Smaller tool lists reduce token usage and keep prompts cheaper.

## Phase 3: Context Passing Between Agents

### How do you pass a structured Context Payload during handoff?

During delegation, `CoordinatorAgent` calls `ContextManager.build_context_payload()`. The payload contains a compact, structured handoff object:

```json
{
  "intent": "update_banking_details",
  "target_agent": "FinanceAgent",
  "entities": {
    "person_names": []
  },
  "parameters": {
    "routing_number": "123456789",
    "numbers": ["123456789"]
  },
  "relevant_facts": {},
  "redacted_fields": [],
  "missing_fields": ["account_number", "account_holder_name"],
  "user_query_summary": "Update my banking details. Routing number is 123456789."
}
```

The exact fields depend on the session state and extracted data.

### How do you ensure only relevant data is passed?

`ContextManager.relevant_facts_for()` filters case facts by target agent:

- `FinanceAgent` receives numerical, transactional, date, and entity facts.
- `HRAgent` receives entity and date facts.
- Other agents receive only the applicable subset.

This prevents unrelated session memory from being sent to a sub-agent.

### How do you ensure full chat history is not transferred?

The payload is explicitly built from extracted entities, parameters, relevant case facts, missing fields, and a short query summary. It does not include `conversation_history`.

`ContextManager.validate_no_history()` rejects payloads containing forbidden keys:

- `conversation_history`
- `history`
- `messages`
- `full_chat_history`

This enforces structured handoff instead of raw chat-history transfer.

## Phase 4: Memory Compaction & Case Facts

### How does the system extract and store numerical data and transactional information?

`MemoryManager.extract_case_facts()` uses local regex extraction before relying on agent calls. It extracts:

- Numerical values such as `$150.00` or `12500.00`
- Transaction IDs such as `TXN-001`, `ORDER-123`, or `INV-456`
- Dates such as `2024-01-15` or `1/15/2024`
- Entities such as person names and account numbers

The structured dictionary looks like:

```json
{
  "numerical": {
    "amounts": ["$150.00"]
  },
  "transactional": {
    "transaction_ids": ["TXN-001"]
  },
  "entity": {
    "person_names": ["John Doe"],
    "account_numbers": ["ACCT-456"]
  },
  "date": {
    "transaction_dates": ["2024-01-15"]
  }
}
```

These facts are persisted in the SQLite `case_facts` table and reloaded with the session.

### How is memory compacted?

Long input is detected by token count, word count, or transaction-document patterns. When compaction is triggered:

1. Case facts are extracted locally.
2. Facts are merged with existing session facts.
3. The long document is replaced in history with a compact marker.
4. `compact_memory()` replaces verbose history with a short system summary.
5. Critical structured facts remain separately stored in `case_facts`.

This means irrelevant later messages like "okay" or "cool" do not erase transaction IDs, amounts, dates, or names.

### How does the missing-fields flagging mechanism work?

Required fields are defined in the `required_fields_schema` table. For `update_banking_details`, the required fields are:

- `routing_number`
- `account_number`
- `account_holder_name`

When the user says:

```text
Update my banking details. Routing number is 123456789.
```

The system extracts `routing_number`, but detects that `account_number` and `account_holder_name` are missing. It inserts a row into `missing_fields_tracking` and marks the session state as:

```text
requires_user_input
```

### How does this prevent data loss and context degradation?

It prevents data loss by storing important facts separately from the compacted conversation summary. Even if the chat history is compressed, the structured `case_facts` table retains transaction IDs, amounts, dates, and entities.

It prevents context degradation by passing only relevant facts into future agent handoffs instead of sending a long, noisy conversation history.

## Phase 5: Hybrid Planner-Executor Workflow

### How do you pass memory between Planner and Executor?

`OrchestrationEngine._run_planner_executor()` builds a shared context payload containing:

- `session_id`
- stored `case_facts`
- planning context
- the generated plan

The Planner receives the task and context, generates structured JSON, and persists it to `execution_plans` and `execution_steps`. The Executor then receives the same session context plus the plan.

### How do you maintain consistency across steps?

Consistency is maintained through persisted execution state:

- Plans are stored in `execution_plans`.
- Individual steps are stored in `execution_steps`.
- Each step has `step_order`, `depends_on`, `status`, `expected_output`, and `actual_output`.
- The Executor sorts steps by `step_order`.
- It checks dependencies before execution.
- Completed steps are skipped if execution resumes.
- Failed steps mark the plan as `failed`.

This makes the workflow resumable and auditable.

### What is the biggest architectural advantage of Planner-Executor vs raw API chaining?

The biggest advantage is separation of concerns.

The Planner decides **what should happen** and produces a structured plan. The Executor decides **how to carry out each step** while respecting dependencies and persisted state.

Compared with raw API chaining, this gives:

- Better observability
- Easier retries and resumes
- Clear step-level failure handling
- Structured validation
- Lower risk of losing state between calls
- More predictable execution for complex workflows

## Cost and Usage Strategy

The implementation follows the cost guidelines by using cheaper models by default:

- `gpt-4o-mini` for Coordinator, Finance, HR, Executor, and summarization
- `o3-mini` for reasoning-heavy Planner and LoopDetectionAgent
- OpenAI as primary provider
- OpenRouter as optional fallback

The system also reduces cost by:

- Limiting tools per agent
- Avoiding full-history handoffs
- Compacting long memory
- Blocking repeated failing tool calls with the circuit breaker
- Enforcing token budgets before SDK calls

