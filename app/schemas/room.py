from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.constants import (
    DEFAULT_MAX_PLAYERS,
    DEFAULT_TOTAL_ROUNDS,
    MAX_DISPLAY_NAME_LEN,
    MAX_PLAYERS,
    MAX_ROUNDS,
    MIN_DISPLAY_NAME_LEN,
    MIN_PLAYERS,
    MIN_ROUNDS,
    ROOM_CODE_LENGTH,
)

class CreateRoomRequest(BaseModel):
    hostDisplayName: str = Field(min_length=MIN_DISPLAY_NAME_LEN, max_length=MAX_DISPLAY_NAME_LEN)
    title: Optional[str] = Field(default=None, max_length=50)
    maxPlayers: int = Field(default=DEFAULT_MAX_PLAYERS, ge=MIN_PLAYERS, le=MAX_PLAYERS)
    totalRounds: int = Field(default=DEFAULT_TOTAL_ROUNDS, ge=MIN_ROUNDS, le=MAX_ROUNDS)
    gameMode: str = Field(default="confessions")  # "confessions", "chameleon", "roasts"
    promptCategory: str = Field(default="general")
    customPrompt: Optional[str] = Field(default=None, max_length=150)

class JoinRoomRequest(BaseModel):
    roomCode: str = Field(min_length=ROOM_CODE_LENGTH, max_length=ROOM_CODE_LENGTH)
    displayName: str = Field(min_length=MIN_DISPLAY_NAME_LEN, max_length=MAX_DISPLAY_NAME_LEN)

class LockRoomRequest(BaseModel):
    locked: bool

class UpdateRoomSettingsRequest(BaseModel):
    totalRounds: Optional[int] = Field(default=None, ge=MIN_ROUNDS, le=MAX_ROUNDS)
    maxPlayers: Optional[int] = Field(default=None, ge=MIN_PLAYERS, le=MAX_PLAYERS)
    gameMode: Optional[str] = Field(default=None)
    promptCategory: Optional[str] = Field(default=None)
    customPrompt: Optional[str] = Field(default=None)

class RoomCreatedDTO(BaseModel):
    roomId: str
    roomCode: str
    participantId: str
    token: str
    role: str = "owner"
    totalRounds: int = 3
    gameMode: str = "confessions"

class RoomJoinedDTO(BaseModel):
    roomId: str
    participantId: str
    token: str
    role: str

class RoomAvailabilityDTO(BaseModel):
    available: bool
    reason: Optional[str] = None

class HostRoomViewDTO(BaseModel):
    roomId: str
    roomCode: str
    title: Optional[str] = None
    status: str
    currentRoundNumber: int
    totalRounds: int
    gameMode: str = "confessions"
    promptCategory: str = "general"
    customPrompt: Optional[str] = None
    playerCount: int
    maxPlayers: int
    locked: bool
    isOwner: bool = True
    expiresAt: datetime

class PlayerRoomViewDTO(BaseModel):
    roomId: str
    roomCode: str
    title: Optional[str] = None
    status: str
    currentRoundNumber: int
    totalRounds: int
    gameMode: str = "confessions"
    promptCategory: str = "general"
    customPrompt: Optional[str] = None
    playerCount: int
    maxPlayers: int
    locked: bool
    isOwner: bool = False
    hostDisplayName: str
    expiresAt: datetime

class RoomSettingsUpdatedDTO(BaseModel):
    totalRounds: int
    maxPlayers: int
    gameMode: str

class LeaveRoomDTO(BaseModel):
    left: bool = True

class StartRoundDTO(BaseModel):
    roundNumber: int

class LockRoomDTO(BaseModel):
    locked: bool

class EndRoomDTO(BaseModel):
    ended: bool = True
