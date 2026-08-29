from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class SubmitChitRequest(BaseModel):
    body: str = Field(min_length=1, max_length=150)

class EditChitRequest(BaseModel):
    body: str = Field(min_length=1, max_length=150)

class MySubmissionDTO(BaseModel):
    body: str
    submittedAt: datetime
    updatedAt: datetime

class SubmissionStatusDTO(BaseModel):
    hasSubmitted: bool
    canEdit: bool
    canDelete: bool
    canSubmit: bool

class RoundPromptInfoDTO(BaseModel):
    roundNumber: int
    totalRounds: int
    gameMode: str = "confessions"
    prompt: Optional[str] = None
    secretTopic: Optional[str] = None
    secretWord: Optional[str] = None  # None if player is Chameleon!
    isChameleon: bool = False
    wordChoices: List[str] = []
