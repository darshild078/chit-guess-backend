from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class MarkReadRequest(BaseModel):
    isRead: bool

class MarkGuessRequest(BaseModel):
    isGuessed: bool
    guessedAliasId: Optional[str] = None

class AnonymousChitDTO(BaseModel):
    anonymousChitId: str
    alias: str
    body: str
    submittedAt: datetime
    isRead: bool
    isGuessed: bool

class AnonymousInboxDTO(BaseModel):
    roundNumber: int
    aliasEpoch: int
    chits: List[AnonymousChitDTO]

class MarkChitReadDTO(BaseModel):
    isRead: bool

class MarkChitGuessedDTO(BaseModel):
    isGuessed: bool
