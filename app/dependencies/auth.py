from typing import Optional
from fastapi import Request, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.participant import Participant
from app.utils.jwt_helper import verify_participant_token
from app.errors import unauthorized

async def get_current_participant(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db)
) -> Participant:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    
    if not token:
        # Check cookie
        token = request.cookies.get("token")

    if not token:
        raise unauthorized("Please join or create a room to continue.")

    payload = verify_participant_token(token)
    participant_id = payload.get("participantId")
    session_version = payload.get("sessionVersion")

    if not participant_id:
        raise unauthorized("Invalid session. Please rejoin the room.")

    stmt = select(Participant).where(Participant.id == participant_id)
    res = await db.execute(stmt)
    participant = res.scalars().first()

    if not participant or participant.removed:
        raise unauthorized("You have been removed from this room.")

    if participant.sessionVersion != session_version:
        raise unauthorized("Your session has expired. Please rejoin the room.")

    # Attach participant to request state for easy access
    request.state.participant = participant
    return participant
