from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: T

class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    data: None = None
    error_code: str
