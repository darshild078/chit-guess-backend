from fastapi import Depends, Path
from app.dependencies.auth import get_current_participant
from app.models.participant import Participant
from app.errors import forbidden

async def require_room_member(
    roomId: str = Path(...),
    participant: Participant = Depends(get_current_participant)
) -> Participant:
    if participant.roomId != roomId:
        raise forbidden("You are not a member of this room.")
    return participant
