from typing import Optional
from pydantic import BaseModel

class PlayerActivityItemDTO(BaseModel):
    displayName: str
    isCurrentPlayer: bool
    hasSubmitted: bool
    connected: bool

class HostActivityItemDTO(BaseModel):
    alias: str
    aliasId: str
    hasSubmitted: bool
    connected: bool

class HostManagePlayerDTO(BaseModel):
    aliasId: str
    alias: str
    connected: bool
    hasSubmitted: bool
