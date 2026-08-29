from datetime import datetime
from pydantic import BaseModel, Field

class SubmitChitRequest(BaseModel):
    body: str = Field(min_length=1, max_length=30)

class EditChitRequest(BaseModel):
    body: str = Field(min_length=1, max_length=30)

class MySubmissionDTO(BaseModel):
    body: str
    submittedAt: datetime
    updatedAt: datetime

class SubmissionStatusDTO(BaseModel):
    hasSubmitted: bool
    canEdit: bool
    canDelete: bool
    canSubmit: bool
