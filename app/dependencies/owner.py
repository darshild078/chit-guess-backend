from fastapi import Depends
from app.dependencies.auth import get_current_participant
from app.models.participant import Participant
from app.models.enums import ParticipantRole
from app.errors import forbidden

async def require_owner(
    participant: Participant = Depends(get_current_participant)
) -> Participant:
    if participant.role != ParticipantRole.owner:
        raise forbidden("Only the room host can perform this action.")
    return participant
