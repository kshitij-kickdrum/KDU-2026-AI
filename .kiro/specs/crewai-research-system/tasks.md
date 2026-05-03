# Implementation Plan: CrewAI Multi-Agent Research System

## Overview

Build the system incrementally: project scaffolding first, then isolated core components (tools, state, config, memory), then agent and workflow layers, then the Streamlit UI, and finally integration wiring and tests. Each task builds directly on the previous ones so no code is left orphaned.

All implementation is in **Python 3.11+** using **CrewAI 0.70.0+**, **Pydantic 2.0+**, and **Streamlit 1.35.0+**.

## Tasks

- [ ] 1. Scaffold project structure and tooling
  - Create the full directory tree: `config/`, `src/` (with sub-packages `agents/`, `tools/`, `workflows/`, `state/`, `memory/`, `config/`, `utils/`), `tests/` (with `unit/`, `integration/`, `fixtures/`), `data/logs/`
  - Add `__init__.py` to every Python package directory under `src/` and `tests/`
  - Write `requirements.txt` with pinned versions: `crewai>=0.70.0`, `crewai-tools`, `pydantic>=2.0`, `langchain-openai>=0.2`, `python-dotenv>=1.0`, `PyYAML`
  - Write `requirements-dev.txt`: `pytest>=7.0`, `pytest-cov`, `flake8>=6.0`, `black>=23.0`, `mypy>=1.0`, `hypothesis`
  - Write `pyproject.toml` with `[tool.black]`, `[tool.mypy]`, and `[tool.pytest.ini_options]` sections as specified in the design
  - Write `Makefile` with targets: `install`, `test`, `lint`, `format`, `typecheck`, `ui`
  - Write `.env.example` with all required variable names: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `SERPER_API_KEY`
  - Add `.gitignore` entries for `.env`, `data/memory.db`, `data/logs/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `*.pyc`
  - _Requirements: 14.1, 14.2, 14.4_

- [ ] 2. Implement structured logging utility
  - [ ] 2.1 Create `src/utils/logger.py`
    - Implement `get_logger(name: str) -> logging.Logger` that returns a logger with a structured formatter: `timestamp | level | name | message`
    - Configure a `RotatingFileHandler` writing to `data/logs/research_system.log` and a `StreamHandler` for stdout
    - Ensure log output never includes API key values — document this constraint in a module-level comment
    - _Requirements: 12.1, 12.2, 12.5, 12.6_

- [ ] 3. Implement YAML configuration loader
  - [ ] 3.1 Create `src/config/loader.py`
    - Implement `load_agents_config(path: str) -> dict` and `load_tasks_config(path: str) -> dict` that read and parse the respective YAML files
    - Implement `validate_agents_config(config: dict) -> None` and `validate_tasks_config(config: dict) -> None` that raise `ValueError` with the exact field name and expected format when required keys are missing or have wrong types
    - Implement `get_config_paths() -> tuple[str, str]` that returns absolute paths to `config/agents.yaml` and `config/tasks.yaml` relative to the project root
    - _Requirements: 5.1, 5.2, 5.6, 5.7_

  - [ ]* 3.2 Write unit tests for config loader
    - Test successful load of valid agents.yaml and tasks.yaml
    - Test `ValueError` is raised with descriptive message for missing required fields (`role`, `goal`, `backstory`, `description`, `expected_output`, `agent`)
    - Test that modifying the YAML file and reloading returns updated values (Req 5.5)
    - _Requirements: 5.6, 5.7_

  - [ ]* 3.3 Write property test for YAML hot-reload
    - **Property 3: For any valid YAML modification, next execution reflects the change without code restart**
    - **Validates: Requirements 5.5**
    - Use `hypothesis` to generate arbitrary valid agent config dicts, write them to a temp YAML file, reload, and assert the returned config matches the written values

- [ ] 4. Write YAML configuration files
  - [ ] 4.1 Create `config/agents.yaml`
    - Define `researcher`, `fact_checker`, and `writer` agents with `role`, `goal`, `backstory`, and `tools` fields exactly as specified in the design's data schema section
    - Introduce the intentional contradiction: `researcher` backstory says "You always cite sources" while the `research_task` `expected_output` in tasks.yaml will specify a different format — document this with an inline YAML comment explaining the experiment
    - Add inline comments on each field explaining its purpose
    - _Requirements: 1.5, 5.1, 5.3, 6.1, 6.4_

  - [ ] 4.2 Create `config/tasks.yaml`
    - Define `research_task`, `fact_check_task`, and `writing_task` with `description`, `expected_output`, and `agent` fields as specified in the design
    - Use `{topic}` and `{research_results}` and `{fact_check_details}` as template placeholders
    - Add inline comments on each field
    - _Requirements: 1.6, 5.2, 5.4, 6.2_

- [ ] 5. Implement FlowState Pydantic model
  - [ ] 5.1 Create `src/state/flow_state.py`
    - Define `FlowState(BaseModel)` with all seven fields from the design schema: `research_results`, `fact_check_status`, `fact_check_details`, `iteration_counter`, `final_output`, `execution_start_time`, `last_updated`
    - Apply Pydantic field constraints: `max_length` on string fields, `ge=0, le=3` on `iteration_counter`, `Literal["pending","passed","failed"]` on `fact_check_status`
    - Implement a `model_validator` (or `@validator`) that auto-sets `last_updated` to `datetime.utcnow()` on every update
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 5.2 Write unit tests for FlowState
    - Test default construction produces `iteration_counter=0`, `fact_check_status="pending"`, `final_output=None`
    - Test boundary values: `iteration_counter=3` is valid, `iteration_counter=4` raises `ValidationError`
    - Test `max_length` constraints on `research_results` (10,000), `fact_check_details` (5,000), `final_output` (15,000)
    - Test that `fact_check_status` rejects values outside `["pending","passed","failed"]`
    - _Requirements: 9.5, 9.6_

  - [ ]* 5.3 Write property test for FlowState validation
    - **Property 6: For any invalid FlowState field, Pydantic raises ValidationError**
    - **Validates: Requirements 9.5**
    - Use `hypothesis` strategies to generate out-of-range integers for `iteration_counter`, strings exceeding max lengths, and invalid enum values for `fact_check_status`; assert `ValidationError` is always raised

- [ ] 6. Implement the UnreliableResearchTool and retry decorator
  - [ ] 6.1 Create `src/tools/failing_tool.py`
    - Implement `UnreliableResearchTool` as a CrewAI `BaseTool` subclass with `name`, `description`, and `_run(self, query: str) -> str`
    - In `_run`: validate `query` is 1–500 characters; use `random.random() < 0.5` to decide between raising `TimeoutError("Simulated tool timeout")` and returning `f"Supplemental data for: {query}"`
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 6.2 Create `src/tools/retry.py`
    - Implement `with_exponential_backoff(func, max_retries: int = 3, base_delay: float = 1.0)` that calls `func`, catches `TimeoutError`, waits `base_delay * 2^attempt` seconds between retries (delays: 1s, 2s, 4s), logs each retry attempt number via the structured logger, and after exhausting retries logs a WARNING and returns `None`
    - _Requirements: 4.5, 4.6, 4.7, 12.1, 12.2, 12.7_

  - [ ]* 6.3 Write unit tests for UnreliableResearchTool
    - Mock `random.random` to return 0.1 (< 0.5) and assert `TimeoutError` is raised
    - Mock `random.random` to return 0.9 (≥ 0.5) and assert the return value starts with `"Supplemental data for:"`
    - Test that `query` longer than 500 characters raises a validation error
    - _Requirements: 4.2, 4.3_

  - [ ]* 6.4 Write property test for failure rate
    - **Property 2: For n ≥ 100 Failing Tool invocations, failure rate is 45%–55%**
    - **Validates: Requirements 4.2**
    - Invoke `UnreliableResearchTool._run` 200 times with a fixed query, count `TimeoutError` occurrences, assert the failure rate is between 0.45 and 0.55

  - [ ]* 6.5 Write unit tests for retry decorator
    - Test that after 1 failure + 1 success, the function is called exactly twice and the result is returned
    - Test that after 4 consecutive failures (3 retries exhausted), the function returns `None` and a WARNING is logged
    - Test that retry delays are approximately 1s, 2s, 4s by mocking `time.sleep` and asserting call args
    - _Requirements: 4.6, 4.7_

- [ ] 7. Implement LLM provider selector
  - [ ] 7.1 Create `src/utils/cost_tracker.py`
    - Implement `CostTracker` class with `record_tokens(agent_role: str, prompt_tokens: int, completion_tokens: int)` and `estimate_cost(model: str) -> float` using per-token pricing constants for `gpt-4o-mini` and `gpt-3.5-turbo`
    - Implement `get_summary() -> dict` returning total tokens, per-agent breakdown, and estimated USD cost
    - _Requirements: 13.1, 13.5, 15.5_

  - [ ] 7.2 Create `src/config/loader.py` — add `get_llm_provider()` function
    - Implement `get_llm_provider() -> BaseChatModel` following the exact logic from the design's API contract: check `OPENAI_API_KEY` first, then `OPENROUTER_API_KEY`, raise `EnvironmentError` if neither is set
    - Validate all required environment variables (`OPENAI_API_KEY` or `OPENROUTER_API_KEY`, `SERPER_API_KEY`) on call; raise `EnvironmentError` with descriptive message listing the missing variable name
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 14.3, 14.5, 14.6_

- [ ] 8. Implement memory manager
  - [ ] 8.1 Create `src/memory/manager.py`
    - Implement `MemoryManager` class that opens (or creates) `data/memory.db` on `__init__`
    - Implement `initialize_db()` that creates `agent_memory` and `execution_history` tables with the exact schemas from the design if they don't exist
    - Implement `save_memory(agent_role, task_id, memory_type, content, execution_id)` that inserts a row into `agent_memory` inside a database transaction
    - Implement `load_memory(agent_role: str, execution_id: str | None = None) -> list[dict]` that returns all matching rows
    - Implement `save_execution(execution_id, orchestration_mode, total_duration_sec, iterations_used, final_status, cost_estimate_usd)` that inserts into `execution_history`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [ ]* 8.2 Write unit tests for memory manager
    - Test `initialize_db()` creates both tables when the DB file does not exist
    - Test `save_memory` and `load_memory` round-trip with all field types
    - Test that `save_memory` uses a transaction (mock `sqlite3.Connection` and assert `commit` is called)
    - _Requirements: 7.2, 7.4_

  - [ ]* 8.3 Write property test for memory persistence
    - **Property 4: For any data written to memory in execution N, it is readable in execution N+1**
    - **Validates: Requirements 7.3**
    - Use `hypothesis` to generate arbitrary `agent_role`, `task_id`, `content` strings; write them with one `MemoryManager` instance, create a new instance pointing to the same DB file, and assert the data is retrievable

- [ ] 9. Implement agent factory
  - [ ] 9.1 Create `src/agents/factory.py`
    - Implement `build_agents(agents_config: dict, llm) -> dict[str, Agent]` that constructs `researcher`, `fact_checker`, and `writer` `crewai.Agent` objects from the loaded YAML config
    - Attach `SerperDevTool()` and a retry-wrapped `UnreliableResearchTool` instance to the researcher agent
    - Pass `memory=True` and the provided `llm` to each agent
    - _Requirements: 1.1, 1.2, 1.5, 2.3, 7.1, 11.1_

- [ ] 10. Implement Sequential and Hierarchical workflows
  - [ ] 10.1 Create `src/workflows/sequential.py`
    - Implement `run_sequential(topic: str, agents: dict, tasks_config: dict, memory_manager: MemoryManager, cost_tracker: CostTracker) -> dict` that builds `crewai.Task` objects from YAML config, creates a `Crew` with `process=Process.sequential` and `memory=True`, kicks off execution, persists results via `memory_manager`, and returns a result dict with `final_output`, `execution_id`, `duration_sec`, and cost summary
    - Ensure agent order is Researcher → Fact-Checker → Writer
    - _Requirements: 3.1, 3.3, 3.5, 7.1, 7.3_

  - [ ] 10.2 Create `src/workflows/hierarchical.py`
    - Implement `run_hierarchical(topic: str, agents: dict, tasks_config: dict, llm, memory_manager: MemoryManager, cost_tracker: CostTracker) -> dict` that creates a `Crew` with `process=Process.hierarchical`, `manager_llm=llm`, and `memory=True`
    - Log a cost comparison note after execution using the structured logger
    - _Requirements: 3.2, 3.4, 3.5, 13.5_

  - [ ]* 10.3 Write property test for sequential agent order
    - **Property 1: For any Sequential execution, agent order is always Researcher → Fact-Checker → Writer**
    - **Validates: Requirements 3.3**
    - Mock the three agents' `execute_task` methods to record call order; run `run_sequential` with varied topics (generated by `hypothesis`) and assert the recorded order is always `["researcher", "fact_checker", "writer"]`

- [ ] 11. Implement CrewAI Flow with iteration guard
  - [ ] 11.1 Create `src/workflows/flow.py`
    - Implement `ResearchFlow(Flow[FlowState])` class with `@start()` method `run_research` that executes the Researcher agent and updates `state.research_results` and increments `state.iteration_counter`
    - Implement `@listen(run_research)` method `run_fact_check` that executes the Fact-Checker agent and updates `state.fact_check_status` and `state.fact_check_details`
    - Implement `@router(run_fact_check)` method `route_after_fact_check` that returns `"write"` if `state.fact_check_status == "passed"` or `state.iteration_counter >= 3`, else returns `"retry"`
    - Implement `@listen("write")` method `run_writer` that executes the Writer agent and updates `state.final_output`
    - Implement `@listen("retry")` method `handle_retry` that loops back to `run_research` if `iteration_counter < 3`, otherwise logs a WARNING and terminates with partial results
    - Log each state transition via the structured logger
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 12.6_

  - [ ]* 11.2 Write property test for iteration guard
    - **Property 7: For any flow that would exceed 3 iterations, execution terminates and returns partial results**
    - **Validates: Requirements 10.3**
    - Mock the Fact-Checker to always return `fact_check_status="failed"`; run `ResearchFlow` and assert it terminates after exactly 3 iterations and returns a result dict (not an exception)

  - [ ]* 11.3 Write property test for Writer invocation condition
    - **Property 5: For any fact_check_status == "passed", Writer Agent is invoked next**
    - **Validates: Requirements 8.4**
    - Use `hypothesis` to generate `iteration_counter` values in `[1, 2, 3]`; mock Fact-Checker to return `"passed"` and assert the Writer agent's execute method is called exactly once

- [ ] 12. Implement shared input validation
  - [ ] 12.1 Create `src/utils/validation.py`
    - Implement `validate_topic(topic: str) -> str` that enforces max 500 characters and strips/rejects characters outside alphanumeric + common punctuation; raise `ValueError` with a descriptive message on violation
    - _Requirements: 14.5, 14.6, 15.1_

- [ ] 13. Implement Streamlit UI
  - [ ] 13.1 Create `src/ui/components.py`
    - Implement `render_topic_input() -> tuple[str, str, bool]` that renders a text input for the research topic, a radio/selectbox for mode (`sequential` / `hierarchical` / `flow`), and a Run button; returns `(topic, mode, flow_flag)`
    - Implement `render_agent_output_section()` that creates three `st.expander` containers (one per agent) for streaming output
    - _Requirements: 15.1, 15.2, 15.3_

  - [ ] 13.2 Create `src/ui/flow_state_view.py`
    - Implement `render_flow_state(state: FlowState)` that displays a live-updating panel showing: iteration counter as `st.metric`, fact_check_status as a colored badge (`st.success` / `st.warning` / `st.error`), and a progress bar based on `iteration_counter / 3`
    - Use `st.empty()` placeholders so the panel updates in place without re-rendering the full page
    - _Requirements: 8.4, 10.3_

  - [ ] 13.3 Create `src/ui/stats_panel.py`
    - Implement `render_stats(result: dict)` that displays execution stats in a three-column layout: total duration (seconds), estimated cost (USD), and total API call count using `st.metric`
    - _Requirements: 15.5_

  - [ ] 13.4 Create `src/ui/history_view.py`
    - Implement `render_history(memory_manager: MemoryManager)` that queries `execution_history` from SQLite and renders a `st.dataframe` with columns: execution_id (truncated), orchestration_mode, final_status, total_duration_sec, cost_estimate_usd, created_at
    - Add a row-click expander that shows the full `agent_memory` entries for the selected execution_id
    - _Requirements: 7.3, 7.7_

  - [ ] 13.5 Create `app.py` — Streamlit entry point
    - Set page config: `st.set_page_config(page_title="CrewAI Research System", layout="wide")`
    - Render sidebar with: environment status indicators (green/red dots for `OPENAI_API_KEY`, `SERPER_API_KEY`), and a "History" toggle to show/hide the history viewer
    - On Run button click: validate topic, initialize `MemoryManager` and `CostTracker`, load configs, build agents, dispatch to the selected workflow using `st.spinner`, stream agent outputs using callbacks that write to the appropriate `st.expander`, update the FlowState visualizer after each state transition (for flow mode), and render the stats panel on completion
    - Display the final research document in a `st.markdown` block with a download button (`st.download_button`) to save as `.txt`
    - Handle errors gracefully: display `st.error(message)` for config/env errors, tool failures, and LLM provider failures — never show raw stack traces to the user
    - _Requirements: 14.5, 15.4, 15.5, 15.6_

  - [ ] 13.6 Update `requirements.txt` to add `streamlit>=1.35.0`
  - [ ] 13.7 Update `Makefile` to add `ui: streamlit run app.py` target and remove CLI run targets
  - [ ] 13.8 Update `README.md` to add Streamlit launch instructions: `streamlit run app.py`

- [ ] 14. Checkpoint — wire everything together and verify end-to-end
  - Ensure all imports resolve correctly across all modules including `src/ui/`
  - Run `mypy src/` and fix all type errors
  - Run `flake8 src/` and fix all lint errors
  - Run `black src/ tests/` to enforce formatting
  - Launch `streamlit run app.py` and verify the UI loads without errors
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Write integration tests
  - [ ] 14.1 Create `tests/fixtures/mock_llm.py`
    - Implement `MockLLM` that returns deterministic canned responses for each agent role (researcher returns a fixed research string, fact_checker returns `"passed"` or `"failed"` based on a configurable flag, writer returns a fixed document string)
    - Implement `MockLLMAlwaysFail` that raises `Exception("LLM unavailable")` to test fallback behavior
    - _Requirements: 2.3, 2.4_

  - [ ] 14.2 Create `tests/fixtures/sample_configs.py`
    - Provide `VALID_AGENTS_CONFIG` and `VALID_TASKS_CONFIG` dicts matching the design schemas for use across all tests
    - Provide `INVALID_AGENTS_CONFIG` (missing `role` field) and `INVALID_TASKS_CONFIG` (missing `expected_output`) for error-path tests
    - _Requirements: 5.6, 5.7_

  - [ ] 14.3 Create `tests/integration/test_sequential_workflow.py`
    - Test that `run_sequential` with `MockLLM` completes and returns a dict with `final_output`, `execution_id`, `duration_sec`
    - Test that the result dict's `final_output` is non-empty
    - Test that memory is persisted to SQLite after execution (query `agent_memory` table directly)
    - _Requirements: 3.1, 3.3, 7.3_

  - [ ] 14.4 Create `tests/integration/test_hierarchical_workflow.py`
    - Test that `run_hierarchical` with `MockLLM` completes and returns a result dict
    - Test that a cost comparison log entry is written
    - _Requirements: 3.2, 3.4, 13.5_

  - [ ] 14.5 Create `tests/integration/test_flow_execution.py`
    - Test happy path: `MockLLM` fact_checker returns `"passed"` on first iteration → Writer is called → flow exits with `final_output`
    - Test retry path: `MockLLM` fact_checker returns `"failed"` for 2 iterations then `"passed"` → Writer is called on iteration 3
    - Test max-iteration termination: `MockLLM` fact_checker always returns `"failed"` → flow exits after 3 iterations with a WARNING log and partial results
    - _Requirements: 8.4, 10.3, 10.5_

  - [ ] 14.6 Create `tests/integration/test_memory_persistence.py`
    - Test that data written by one `MemoryManager` instance is readable by a second instance pointing to the same DB file (simulating session N → session N+1)
    - _Requirements: 7.3, 7.7_

  - [ ]* 14.7 Write property test for TimeoutError logging
    - **Property 8: For any TimeoutError from Failing Tool, a structured log entry is written with timestamp**
    - **Validates: Requirements 12.1**
    - Use `hypothesis` to generate arbitrary query strings (1–500 chars); mock `random.random` to always return 0.1 (force failure); invoke the retry wrapper; assert the captured log output contains a timestamp and the word `"TimeoutError"` or `"timeout"`

- [ ] 16. Write README.md
  - Create `README.md` with sections: Prerequisites, Installation, Environment Setup (`.env` variables), Streamlit Usage, Contradiction Experiment (observed behavior of backstory vs. expected_output conflict and explanation of which wins), Architecture Overview, and Running Tests
  - _Requirements: 6.4, 14.7_

- [ ] 17. Final checkpoint — full test suite and coverage
  - Run `pytest tests/ -v --cov=src --cov-report=term-missing` and confirm coverage exceeds 85% across all `src/` modules
  - Fix any failing tests or coverage gaps
  - Run `mypy src/`, `flake8 src/ tests/`, `black --check src/ tests/` and resolve all issues
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use the `hypothesis` library; install via `requirements-dev.txt`
- The contradiction experiment (Req 6) is implemented in task 4 (YAML files) and documented in task 15 (README); CrewAI gives priority to `task.expected_output` over `agent.backstory`
- The `UnreliableResearchTool` retry wrapper (task 6.2) must be applied in the agent factory (task 9.1) — the tool itself does not retry internally
- SQLite `memory.db` is created automatically by `MemoryManager.initialize_db()` on first run (task 8.1)
- Exit codes: 0 = success, 1 = config/env error, 2 = execution failed, 3 = max iteration limit reached
