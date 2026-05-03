# Requirements Document

## Introduction

The CrewAI Research System is an autonomous multi-agent research department that demonstrates orchestration strategies, failure handling, state management, and memory behavior in production-like scenarios. The system coordinates three specialized agents (Researcher, Fact-Checker, Writer) to perform research tasks with resilience to tool failures, external YAML-based configuration, persistent memory, and event-driven workflow execution using CrewAI Flows.

This system serves as a hands-on implementation to explore how multi-agent systems handle unreliable tools, resolve configuration conflicts, manage state across agent interactions, and prevent infinite execution loops.

## Glossary

- **Research_System**: The complete CrewAI-based multi-agent system
- **Researcher_Agent**: Agent responsible for gathering information using search tools
- **Fact_Checker_Agent**: Agent responsible for verifying research accuracy
- **Writer_Agent**: Agent responsible for producing final written output
- **Sequential_Workflow**: CrewAI orchestration where agents execute in fixed order
- **Hierarchical_Workflow**: CrewAI orchestration where a Manager LLM coordinates agent execution
- **Failing_Tool**: Custom tool that throws TimeoutError with 50% probability
- **Agent_Configuration**: YAML file (agents.yaml) defining agent properties
- **Task_Configuration**: YAML file (tasks.yaml) defining task specifications
- **Global_Memory**: CrewAI memory system that persists across executions
- **Flow_State**: Pydantic-based structured state object for intermediate outputs
- **Crew_Flow**: Event-driven workflow implementation using CrewAI Flows
- **Iteration_Counter**: State variable tracking execution cycles to prevent infinite loops
- **LLM_Provider**: Language model service (OpenAI or OpenRouter)
- **Serper_Tool**: SerperDevTool for web search functionality
- **Memory_Storage**: SQLite database for persistent memory

## Requirements

### Requirement 1: Multi-Agent System Architecture

**User Story:** As a system architect, I want a multi-agent research system with three specialized agents, so that research tasks can be decomposed and executed by role-specific agents.

#### Acceptance Criteria

1. THE Research_System SHALL include exactly three agents: Researcher_Agent, Fact_Checker_Agent, and Writer_Agent
2. THE Researcher_Agent SHALL be equipped with Serper_Tool and Failing_Tool
3. THE Fact_Checker_Agent SHALL receive output from Researcher_Agent as input
4. THE Writer_Agent SHALL receive output from Fact_Checker_Agent as input
5. FOR ALL agent configurations, the system SHALL load definitions from Agent_Configuration file
6. FOR ALL task configurations, the system SHALL load definitions from Task_Configuration file

### Requirement 2: LLM Provider Configuration

**User Story:** As a developer, I want flexible LLM provider selection, so that the system can use available API services with cost optimization.

#### Acceptance Criteria

1. THE Research_System SHALL support OpenAI as the primary LLM_Provider
2. THE Research_System SHALL support OpenRouter as fallback LLM_Provider
3. WHEN OpenAI API credentials are available, THE Research_System SHALL use OpenAI models
4. WHEN OpenAI API credentials are unavailable, THE Research_System SHALL use OpenRouter models
5. THE Research_System SHALL use GPT-4o-mini or GPT-3.5 class models for cost optimization
6. THE Research_System SHALL load LLM_Provider credentials from environment variables

### Requirement 3: Orchestration Strategy Support

**User Story:** As a researcher, I want to execute workflows using different orchestration strategies, so that I can observe behavior differences under various coordination approaches.

#### Acceptance Criteria

1. THE Research_System SHALL support Sequential_Workflow execution mode
2. THE Research_System SHALL support Hierarchical_Workflow execution mode
3. WHEN Sequential_Workflow is selected, THE Research_System SHALL execute agents in fixed order: Researcher_Agent → Fact_Checker_Agent → Writer_Agent
4. WHEN Hierarchical_Workflow is selected, THE Research_System SHALL use a Manager LLM to coordinate agent execution
5. FOR ALL orchestration modes, THE Research_System SHALL produce research output
6. THE Research_System SHALL allow runtime selection between Sequential_Workflow and Hierarchical_Workflow

### Requirement 4: Unreliable Tool Implementation

**User Story:** As a system designer, I want a custom tool that fails intermittently, so that I can test failure handling and resilience mechanisms.

#### Acceptance Criteria

1. THE Research_System SHALL include a Failing_Tool as a custom tool
2. WHEN Failing_Tool is invoked, THE Failing_Tool SHALL throw TimeoutError with 50% probability
3. WHEN Failing_Tool is invoked, THE Failing_Tool SHALL return valid output with 50% probability
4. THE Failing_Tool SHALL be assigned to Researcher_Agent
5. THE Research_System SHALL implement automatic retry logic for Failing_Tool
6. WHEN Failing_Tool fails, THE Research_System SHALL retry with exponential backoff
7. THE Research_System SHALL limit Failing_Tool retries to a maximum of 3 attempts

### Requirement 5: YAML-Based Configuration Management

**User Story:** As a configuration manager, I want all agent and task definitions in external YAML files, so that configurations can be modified without code changes.

#### Acceptance Criteria

1. THE Research_System SHALL load all agent definitions from agents.yaml file
2. THE Research_System SHALL load all task definitions from tasks.yaml file
3. THE Agent_Configuration SHALL define agent roles, goals, and backstories
4. THE Task_Configuration SHALL define task descriptions and expected outputs
5. WHEN Agent_Configuration or Task_Configuration is modified, THE Research_System SHALL reflect changes on next execution without code modification
6. THE Research_System SHALL validate Agent_Configuration and Task_Configuration schemas on startup
7. IF Agent_Configuration or Task_Configuration is invalid, THEN THE Research_System SHALL raise a descriptive error message

### Requirement 6: Configuration Conflict Resolution

**User Story:** As a system observer, I want to introduce contradictions between agent backstory and task expected output, so that I can understand how CrewAI resolves configuration conflicts.

#### Acceptance Criteria

1. THE Agent_Configuration SHALL support backstory field for each agent
2. THE Task_Configuration SHALL support expected_output field for each task
3. WHEN agent backstory contradicts task expected_output, THE Research_System SHALL execute the task
4. THE Research_System SHALL document which instruction takes priority: agent backstory or task expected_output
5. FOR ALL task executions with contradictions, THE Research_System SHALL produce output aligned with task expected_output

### Requirement 7: Global Memory System

**User Story:** As a researcher, I want the system to remember previous executions, so that agents can learn from past interactions and improve over time.

#### Acceptance Criteria

1. THE Research_System SHALL enable Global_Memory by setting memory=True
2. THE Research_System SHALL use Memory_Storage (SQLite) for persistent memory
3. WHEN Research_System executes multiple times, THE Global_Memory SHALL persist across executions
4. THE Global_Memory SHALL store agent interactions, decisions, and outputs
5. WHEN an agent executes a task, THE agent SHALL have access to Global_Memory from previous executions
6. THE Research_System SHALL store Memory_Storage in a local database file
7. FOR ALL executions on Day N+1, THE Research_System SHALL access memory from Day N

### Requirement 8: Event-Driven Flow Architecture

**User Story:** As a workflow designer, I want to implement event-driven workflows using CrewAI Flows, so that agent execution can be dynamic and state-dependent.

#### Acceptance Criteria

1. THE Research_System SHALL implement Crew_Flow using CrewAI Flows framework
2. THE Crew_Flow SHALL define a Flow_State class using Pydantic for structured state management
3. THE Flow_State SHALL store intermediate outputs from Researcher_Agent and Fact_Checker_Agent
4. WHEN Fact_Checker_Agent completes verification, THE Crew_Flow SHALL determine next step based on Fact_Checker_Agent output
5. THE Crew_Flow SHALL support conditional branching based on Flow_State values
6. FOR ALL state transitions, THE Crew_Flow SHALL update Flow_State with new values

### Requirement 9: Structured State Management

**User Story:** As a developer, I want structured state objects instead of raw text, so that data can be validated, typed, and easily processed.

#### Acceptance Criteria

1. THE Flow_State SHALL be defined as a Pydantic model
2. THE Flow_State SHALL include field for research_results from Researcher_Agent
3. THE Flow_State SHALL include field for fact_check_status from Fact_Checker_Agent
4. THE Flow_State SHALL include field for Iteration_Counter
5. THE Flow_State SHALL validate all field types at runtime
6. WHEN Flow_State receives invalid data, THE Flow_State SHALL raise a validation error
7. FOR ALL agent outputs stored in Flow_State, THE Research_System SHALL serialize outputs as JSON

### Requirement 10: Infinite Loop Prevention

**User Story:** As a system administrator, I want guardrails to prevent infinite execution loops, so that the system does not consume excessive resources or costs.

#### Acceptance Criteria

1. THE Crew_Flow SHALL maintain an Iteration_Counter in Flow_State
2. THE Crew_Flow SHALL increment Iteration_Counter after each agent execution cycle
3. WHEN Iteration_Counter reaches 3, THE Crew_Flow SHALL terminate execution
4. THE Crew_Flow SHALL return final output when Iteration_Counter limit is reached
5. THE Research_System SHALL log a warning when execution terminates due to Iteration_Counter limit
6. FOR ALL executions, THE Crew_Flow SHALL prevent more than 3 complete research cycles

### Requirement 11: Search Tool Integration

**User Story:** As a researcher, I want web search capabilities, so that agents can gather current information from the internet.

#### Acceptance Criteria

1. THE Researcher_Agent SHALL be equipped with Serper_Tool
2. THE Serper_Tool SHALL use Serper.dev API for web search
3. THE Research_System SHALL load Serper.dev API credentials from environment variables
4. WHEN Researcher_Agent needs information, THE Researcher_Agent SHALL invoke Serper_Tool
5. THE Serper_Tool SHALL return search results to Researcher_Agent
6. THE Research_System SHALL limit Serper_Tool usage to stay within 2,500 free queries per account

### Requirement 12: Error Handling and Logging

**User Story:** As a system operator, I want comprehensive error handling and logging, so that I can diagnose failures and monitor system behavior.

#### Acceptance Criteria

1. WHEN Failing_Tool throws TimeoutError, THE Research_System SHALL log the error with timestamp
2. WHEN retry logic is triggered, THE Research_System SHALL log retry attempt number
3. WHEN Agent_Configuration or Task_Configuration fails validation, THE Research_System SHALL log validation errors
4. WHEN LLM_Provider API call fails, THE Research_System SHALL log the error and retry
5. THE Research_System SHALL log all agent task completions with execution time
6. THE Research_System SHALL log Flow_State transitions in Crew_Flow
7. IF maximum retries are exceeded, THEN THE Research_System SHALL log failure and continue with degraded functionality

### Requirement 13: Cost Optimization

**User Story:** As a budget manager, I want the system to minimize API costs, so that the lab can be completed within free tier limits.

#### Acceptance Criteria

1. THE Research_System SHALL use the cheapest available LLM models (GPT-4o-mini or GPT-3.5 class)
2. THE Research_System SHALL minimize context size in LLM API calls
3. THE Research_System SHALL avoid unnecessary retries beyond configured limits
4. THE Research_System SHALL limit Serper_Tool calls to essential searches only
5. WHEN Hierarchical_Workflow is used, THE Research_System SHALL log cost comparison with Sequential_Workflow
6. THE Research_System SHALL provide cost estimation before execution

### Requirement 14: Development Environment Setup

**User Story:** As a developer, I want clear environment setup instructions, so that I can run the system from scratch.

#### Acceptance Criteria

1. THE Research_System SHALL require Python 3.11 or higher
2. THE Research_System SHALL provide a requirements.txt file with all dependencies
3. THE Research_System SHALL require environment variables: OPENAI_API_KEY, OPENROUTER_API_KEY, SERPER_API_KEY
4. THE Research_System SHALL provide a .env.example file with required environment variable names
5. THE Research_System SHALL validate all required environment variables on startup
6. IF required environment variables are missing, THEN THE Research_System SHALL raise a descriptive error message
7. THE Research_System SHALL include a README.md with setup and execution instructions

### Requirement 15: Execution Modes and Output

**User Story:** As a user, I want to execute the system in different modes and receive clear output, so that I can observe different behaviors and results.

#### Acceptance Criteria

1. THE Research_System SHALL support command-line execution with mode selection
2. THE Research_System SHALL accept command-line argument for orchestration mode: --mode sequential or --mode hierarchical
3. THE Research_System SHALL accept command-line argument for flow execution: --flow
4. WHEN execution completes, THE Research_System SHALL output final research results
5. WHEN execution completes, THE Research_System SHALL output execution statistics: total time, agent execution times, API call counts
6. THE Research_System SHALL save execution results to an output file
7. THE Research_System SHALL display Flow_State at each transition when --flow mode is used
