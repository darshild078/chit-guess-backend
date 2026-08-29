from typing import Optional, Dict, Any

class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "BAD_REQUEST",
        field_errors: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.field_errors = field_errors

def bad_request(message: str, code: str = "BAD_REQUEST", field_errors: Optional[Dict[str, Any]] = None) -> AppError:
    return AppError(message=message, status_code=400, code=code, field_errors=field_errors)

def unauthorized(message: str = "Please join or create a room to continue.", code: str = "UNAUTHORIZED") -> AppError:
    return AppError(message=message, status_code=401, code=code)

def forbidden(message: str = "Only the room host can perform this action.", code: str = "FORBIDDEN") -> AppError:
    return AppError(message=message, status_code=403, code=code)

def not_found(message: str = "The requested resource was not found.", code: str = "NOT_FOUND") -> AppError:
    return AppError(message=message, status_code=404, code=code)

def conflict(message: str, code: str = "CONFLICT") -> AppError:
    return AppError(message=message, status_code=409, code=code)

def internal_error(message: str = "Something went wrong on our end. Please try again.", code: str = "INTERNAL_ERROR") -> AppError:
    return AppError(message=message, status_code=500, code=code)
