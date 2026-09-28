from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_TRANSITION = "INVALID_TRANSITION"
    STALE_VERSION = "STALE_VERSION"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidTransitionError(AppError):
    def __init__(self, message: str):
        super().__init__(ErrorCode.INVALID_TRANSITION, message, status_code=400)


class StaleVersionError(AppError):
    def __init__(self, message: str):
        super().__init__(ErrorCode.STALE_VERSION, message, status_code=409)


class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(ErrorCode.NOT_FOUND, message, status_code=404)