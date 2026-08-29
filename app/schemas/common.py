from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    fieldErrors: Optional[Dict[str, Any]] = None

class ApiErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
