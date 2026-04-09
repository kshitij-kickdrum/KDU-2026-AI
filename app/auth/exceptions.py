from app.core.exceptions import AppException


class UserAlreadyExists(AppException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_ALREADY_EXISTS",
            message="A user with this email already exists.",
            status_code=409,
        )


class InvalidCredentials(AppException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            status_code=401,
        )


class ForbiddenAction(AppException):
    def __init__(self) -> None:
        super().__init__(
            code="FORBIDDEN",
            message="You do not have permission to perform this action.",
            status_code=403,
        )
