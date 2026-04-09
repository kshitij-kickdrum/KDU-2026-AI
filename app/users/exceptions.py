from app.core.exceptions import AppException


class UserNotFound(AppException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_NOT_FOUND",
            message="User not found.",
            status_code=404,
        )
