from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.participant import LeaderboardItemDTO

class RoundWordDTO(BaseModel):
    chitId: str
    body: str
    isOwnWord: bool
    authorDisplayName: Optional[str] = None  # Populated in Chameleon mode

class ChitGuessItem(BaseModel):
    chitId: Optional[str] = None  # Optional for chameleon player voting
    guessedParticipantId: str
    isDoubleDown: bool = False

class SubmitGuessesRequest(BaseModel):
    guesses: List[ChitGuessItem] = Field(min_length=1)

class ChameleonGuessWordRequest(BaseModel):
    word: str

class GuessSummaryItem(BaseModel):
    guesserName: str
    guessedPlayerName: str
    isCorrect: bool
    isDoubleDown: bool = False

class RoundRevealDetailDTO(BaseModel):
    chitId: str
    body: str
    authorParticipantId: str
    authorDisplayName: str
    correctGuessers: List[str]
    guessesSummary: List[GuessSummaryItem]
    stealthBonusAwarded: bool = False
    votesCount: int = 0  # For Roast mode

class PlayerBadgeDTO(BaseModel):
    badgeId: str
    title: str
    emoji: str
    description: str
    recipientDisplayName: str
    recipientParticipantId: str

class RoundResultsDTO(BaseModel):
    roundNumber: int
    totalRounds: int
    isFinalRound: bool
    gameMode: str = "confessions"
    prompt: Optional[str] = None
    secretTopic: Optional[str] = None
    secretWord: Optional[str] = None
    chameleonParticipantId: Optional[str] = None
    chameleonDisplayName: Optional[str] = None
    chameleonCaught: Optional[bool] = None
    chameleonEscaped: Optional[bool] = None
    chameleonGuessedWord: Optional[bool] = None
    chits: List[RoundRevealDetailDTO]
    leaderboard: List[LeaderboardItemDTO]
    awards: List[PlayerBadgeDTO] = []

class SubmitGuessesResponseDTO(BaseModel):
    lockedIn: bool = True

class ChameleonGuessResponseDTO(BaseModel):
    isCorrect: bool
