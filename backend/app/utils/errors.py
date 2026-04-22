from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    message: str
    status_code: int = 500

    def __str__(self) -> str:
        return self.message


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message=message, status_code=429)

