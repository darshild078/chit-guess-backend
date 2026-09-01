from typing import Any, Dict, Optional

class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        field_errors: Optional[Dict[str, Any]] = None,
        internal_context: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.field_errors = field_errors
        self.internal_context = internal_context

class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Invalid request.",
        error_code: str = "BAD_REQUEST",
        field_errors: Optional[Dict[str, Any]] = None,
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            field_errors=field_errors,
            internal_context=internal_context,
        )

class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Please join or create a room to continue.",
        error_code: str = "UNAUTHORIZED",
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            internal_context=internal_context,
        )

class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        error_code: str = "FORBIDDEN",
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            internal_context=internal_context,
        )

class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "The requested resource was not found.",
        error_code: str = "NOT_FOUND",
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            internal_context=internal_context,
        )

class ConflictException(AppException):
    def __init__(
        self,
        message: str = "A conflict occurred with existing room data.",
        error_code: str = "CONFLICT",
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            internal_context=internal_context,
        )

class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Validation failed. Please check your inputs.",
        error_code: str = "VALIDATION_ERROR",
        field_errors: Optional[Dict[str, Any]] = None,
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code=error_code,
            field_errors=field_errors,
            internal_context=internal_context,
        )

class ServiceUnavailableException(AppException):
    def __init__(
        self,
        message: str = "Service is temporarily unavailable. Please retry in a few moments.",
        error_code: str = "SERVICE_UNAVAILABLE",
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=503,
            error_code=error_code,
            internal_context=internal_context,
        )

class InternalServerErrorException(AppException):
    def __init__(
        self,
        message: str = "An unexpected error occurred. Please try again.",
        error_code: str = "INTERNAL_SERVER_ERROR",
        internal_context: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code=error_code,
            internal_context=internal_context,
        )
