class AgentKitError(Exception):
    """Base exception for orchestration errors."""


class SDKUnavailableError(AgentKitError):
    """Raised when the OpenAI Agents SDK is not installed."""


class TokenBudgetError(AgentKitError):
    """Raised when an input exceeds configured token budget."""


class ToolAccessViolationError(AgentKitError):
    """Raised when an agent attempts to call an unregistered tool."""


class CircuitBreakerOpenError(AgentKitError):
    """Raised when a circuit breaker blocks tool execution."""


class AgentExecutionError(AgentKitError):
    """Raised when an SDK agent run fails."""


class MemoryStorageError(AgentKitError):
    """Raised when session memory cannot be persisted."""


class MissingAPIKeyError(AgentKitError):
    """Raised when no OpenAI API key is configured for live SDK calls."""


class ProviderConnectionError(AgentKitError):
    """Raised when OpenAI/OpenRouter cannot be reached."""
