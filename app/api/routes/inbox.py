from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_owner
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.inbox import (
    AnonymousInboxDTO,
    MarkChitGuessedDTO,
    MarkChitReadDTO,
    MarkGuessRequest,
    MarkReadRequest,
)
from app.services.inbox_service import (
    get_anonymous_inbox,
    mark_chit_guessed,
    mark_chit_read,
)

router = APIRouter(prefix="/rooms/{roomId}/inbox", tags=["Inbox"])

@router.get("/anonymous", response_model=ApiResponse[AnonymousInboxDTO])
async def get_anonymous_inbox_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AnonymousInboxDTO]:
    inbox = await get_anonymous_inbox(db, roomId)
    return ApiResponse(data=inbox)

@router.patch("/{anonymousChitId}/read", response_model=ApiResponse[MarkChitReadDTO])
async def mark_read_endpoint(
    payload: MarkReadRequest,
    roomId: str = Path(...),
    anonymousChitId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MarkChitReadDTO]:
    result = await mark_chit_read(db, roomId, anonymousChitId, payload.isRead)
    return ApiResponse(data=result)

@router.patch("/{anonymousChitId}/guess", response_model=ApiResponse[MarkChitGuessedDTO])
async def mark_guess_endpoint(
    payload: MarkGuessRequest,
    roomId: str = Path(...),
    anonymousChitId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MarkChitGuessedDTO]:
    result = await mark_chit_guessed(db, roomId, anonymousChitId, payload.isGuessed, payload.guessedAliasId)
    return ApiResponse(data=result)
