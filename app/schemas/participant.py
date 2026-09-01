from typing import Optional
from pydantic import BaseModel

class PlayerActivityItemDTO(BaseModel):
    participantId: str
    displayName: str
    isCurrentPlayer: bool
    hasSubmitted: bool
    hasGuessed: bool = False
    connected: bool
    score: int = 0
    role: str = "player"

class LeaderboardItemDTO(BaseModel):
    participantId: str
    displayName: str
    score: int
    rank: int
    connected: bool
    role: str = "player"

class HostActivityItemDTO(BaseModel):
    alias: str
    aliasId: str
    hasSubmitted: bool
    hasGuessed: bool = False
    connected: bool

class HostManagePlayerDTO(BaseModel):
    aliasId: str
    alias: str
    connected: bool
    hasSubmitted: bool

class RemovePlayerDTO(BaseModel):
    removed: bool = True
