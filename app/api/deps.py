from typing import Optional
from fastapi import Depends, Header, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.constants import ParticipantRole
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import verify_participant_token
from app.models.participant import Participant

async def get_current_participant(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Participant:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        token = request.cookies.get("token")

    if not token:
        raise UnauthorizedException("Please join or create a room to continue.")

    payload = verify_participant_token(token)
    participant_id = payload.get("participantId")
    session_version = payload.get("sessionVersion")

    if not participant_id:
        raise UnauthorizedException("Invalid session. Please rejoin the room.")

    stmt = select(Participant).where(Participant.id == participant_id)
    res = await db.execute(stmt)
    participant = res.scalars().first()

    if not participant or participant.removed:
        raise UnauthorizedException("You have been removed from this room.")

    if participant.sessionVersion != session_version:
        raise UnauthorizedException("Your session has expired. Please rejoin the room.")

    request.state.participant = participant
    return participant

async def require_owner(
    participant: Participant = Depends(get_current_participant),
) -> Participant:
    if participant.role != ParticipantRole.owner:
        raise ForbiddenException("Only the room host can perform this action.")
    return participant

async def require_room_member(
    roomId: str = Path(...),
    participant: Participant = Depends(get_current_participant),
) -> Participant:
    if participant.roomId != roomId:
        raise ForbiddenException("You are not a member of this room.")
    return participant

__all__ = [
    "get_db",
    "get_current_participant",
    "require_owner",
    "require_room_member",
]
