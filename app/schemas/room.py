from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CreateRoomRequest(BaseModel):
    hostDisplayName: str = Field(min_length=2, max_length=20)
    title: Optional[str] = Field(default=None, max_length=50)
    maxPlayers: int = Field(default=10, ge=2, le=30)
    totalRounds: int = Field(default=3, ge=1, le=10)
    gameMode: str = Field(default="confessions") # "confessions", "chameleon", "roasts"
    promptCategory: str = Field(default="general")
    customPrompt: Optional[str] = Field(default=None, max_length=150)

class JoinRoomRequest(BaseModel):
    roomCode: str = Field(min_length=6, max_length=6)
    displayName: str = Field(min_length=2, max_length=20)

class LockRoomRequest(BaseModel):
    locked: bool

class UpdateRoomSettingsRequest(BaseModel):
    totalRounds: Optional[int] = Field(default=None, ge=1, le=10)
    maxPlayers: Optional[int] = Field(default=None, ge=2, le=30)
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
