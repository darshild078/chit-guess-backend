from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.participant import LeaderboardItemDTO

class RoundWordDTO(BaseModel):
    chitId: str
    body: str
    isOwnWord: bool

class ChitGuessItem(BaseModel):
    chitId: str
    guessedParticipantId: str

class SubmitGuessesRequest(BaseModel):
    guesses: List[ChitGuessItem] = Field(min_length=1)

class GuessSummaryItem(BaseModel):
    guesserName: str
    guessedPlayerName: str
    isCorrect: bool

class RoundRevealDetailDTO(BaseModel):
    chitId: str
    body: str
    authorParticipantId: str
    authorDisplayName: str
    correctGuessers: List[str]
    guessesSummary: List[GuessSummaryItem]

class RoundResultsDTO(BaseModel):
    roundNumber: int
    totalRounds: int
    isFinalRound: bool
    chits: List[RoundRevealDetailDTO]
    leaderboard: List[LeaderboardItemDTO]
