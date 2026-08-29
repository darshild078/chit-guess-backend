from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.owner import require_owner
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.inbox import (
    AnonymousInboxDTO,
    MarkReadRequest,
    MarkGuessRequest,
)
from app.services.inbox_service import InboxService

router = APIRouter(prefix="/rooms/{roomId}/inbox", tags=["Inbox"])

@router.get("/anonymous", response_model=ApiResponse[AnonymousInboxDTO])
async def get_anonymous_inbox(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    inbox = await InboxService.get_anonymous_inbox(db, roomId)
    return ApiResponse(data=inbox)

@router.patch("/{anonymousChitId}/read", response_model=ApiResponse[dict])
async def mark_read(
    payload: MarkReadRequest,
    roomId: str = Path(...),
    anonymousChitId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    await InboxService.mark_chit_read(db, roomId, anonymousChitId, payload.isRead)
    return ApiResponse(data={"isRead": payload.isRead})

@router.patch("/{anonymousChitId}/guess", response_model=ApiResponse[dict])
async def mark_guess(
    payload: MarkGuessRequest,
    roomId: str = Path(...),
    anonymousChitId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    await InboxService.mark_chit_guessed(db, roomId, anonymousChitId, payload.isGuessed, payload.guessedAliasId)
    return ApiResponse(data={"isGuessed": payload.isGuessed})
