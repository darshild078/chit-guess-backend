from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class RevealedChitDTO(BaseModel):
    chitId: str
    senderDisplayName: str
    body: str
    submittedAt: datetime
    guessedDisplayName: Optional[str] = None
    wasCorrect: Optional[bool] = None

class RevealResultsDTO(BaseModel):
    roundNumber: int
    chits: List[RevealedChitDTO]
