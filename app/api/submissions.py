from typing import Optional
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.room_member import require_room_member
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.submission import (
    SubmitChitRequest,
    EditChitRequest,
    MySubmissionDTO,
    SubmissionStatusDTO,
    RoundPromptInfoDTO,
)
from app.services.submission_service import SubmissionService
from app.services.round_service import RoundService
from app.sockets.emitters import emit_player_activity_updated, emit_submission_status

router = APIRouter(prefix="/rooms/{roomId}/submission", tags=["Submissions"])

@router.get("/prompt", response_model=ApiResponse[RoundPromptInfoDTO])
async def get_round_prompt(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    info = await RoundService.get_round_prompt_info(db, roomId, participant.id)
    return ApiResponse(data=info)

@router.get("", response_model=ApiResponse[Optional[MySubmissionDTO]])
@router.get("/", response_model=ApiResponse[Optional[MySubmissionDTO]])
async def get_my_submission(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    submission = await SubmissionService.get_my_submission(db, participant.id, roomId)
    return ApiResponse(data=submission)

@router.get("/status", response_model=ApiResponse[SubmissionStatusDTO])
async def get_submission_status(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    status = await SubmissionService.get_submission_status(db, participant.id, roomId)
    return ApiResponse(data=status)

@router.post("", response_model=ApiResponse[MySubmissionDTO])
@router.post("/", response_model=ApiResponse[MySubmissionDTO])
async def submit_chit(
    payload: SubmitChitRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    submission = await SubmissionService.submit_chit(db, participant.id, roomId, payload.body)
    await emit_player_activity_updated(roomId)
    await emit_submission_status(participant.id, {
        "hasSubmitted": True,
        "canEdit": True,
        "canDelete": True,
        "canSubmit": False
    })
    return ApiResponse(data=submission, message="Submitted successfully!")

@router.patch("", response_model=ApiResponse[MySubmissionDTO])
@router.patch("/", response_model=ApiResponse[MySubmissionDTO])
async def edit_chit(
    payload: EditChitRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    submission = await SubmissionService.edit_chit(db, participant.id, roomId, payload.body)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data=submission, message="Updated successfully.")

@router.delete("", response_model=ApiResponse[dict])
@router.delete("/", response_model=ApiResponse[dict])
async def delete_chit(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    await SubmissionService.delete_chit(db, participant.id, roomId)
    await emit_player_activity_updated(roomId)
    await emit_submission_status(participant.id, {
        "hasSubmitted": False,
        "canEdit": False,
        "canDelete": False,
        "canSubmit": True
    })
    return ApiResponse(data={"deleted": True}, message="Deleted successfully.")
