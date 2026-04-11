class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UserNotFound(AppException):
    def __init__(self, user_id: str):
        super().__init__(
            code="USER_NOT_FOUND",
            message=f"No user found with id {user_id}.",
            status_code=404,
        )


class ParseError(AppException):
    def __init__(self):
        super().__init__(
            code="PARSE_ERROR",
            message="Failed to produce a valid JSON response after maximum retries.",
            status_code=422,
        )


class UnsupportedImageFormat(AppException):
    def __init__(self):
        super().__init__(
            code="UNSUPPORTED_FORMAT",
            message="Image format not supported. Accepted formats: JPEG, PNG, WEBP.",
            status_code=400,
        )


class ImageTooLarge(AppException):
    def __init__(self):
        super().__init__(
            code="IMAGE_TOO_LARGE",
            message="Image exceeds the 10MB size limit.",
            status_code=400,
        )


class ToolCallFailed(AppException):
    def __init__(self):
        super().__init__(
            code="TOOL_CALL_FAILED",
            message="External tool call failed and mock fallback was unavailable.",
            status_code=502,
        )


class UpstreamRateLimited(AppException):
    def __init__(self):
        super().__init__(
            code="UPSTREAM_RATE_LIMITED",
            message="AI provider is temporarily rate-limited. Please retry shortly.",
            status_code=429,
        )


class RateLimitExceededError(AppException):
    def __init__(self):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please wait a minute and try again.",
            status_code=429,
        )


class UpstreamServiceUnavailable(AppException):
    def __init__(self):
        super().__init__(
            code="UPSTREAM_SERVICE_UNAVAILABLE",
            message="AI provider is unavailable for this request. Please retry shortly.",
            status_code=503,
        )


class AgentMaxIterations(AppException):
    def __init__(self):
        super().__init__(
            code="AGENT_MAX_ITERATIONS",
            message="Agent exceeded maximum allowed iterations.",
            status_code=500,
        )


class InvalidInput(AppException):
    def __init__(self, message: str = "Input contains disallowed content."):
        super().__init__(code="INVALID_INPUT", message=message, status_code=400)


class InvalidAge(AppException):
    def __init__(self):
        super().__init__(
            code="INVALID_AGE",
            message="Age must be between 5 and 120.",
            status_code=422,
        )


class InvalidName(AppException):
    def __init__(self):
        super().__init__(
            code="INVALID_NAME",
            message="Name must be between 2 and 50 characters.",
            status_code=422,
        )


class InvalidLocation(AppException):
    def __init__(self):
        super().__init__(
            code="INVALID_LOCATION",
            message="Location must be between 2 and 100 characters.",
            status_code=422,
        )
