from typing import Optional
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_room_member
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.submission import (
    DeleteChitDTO,
    EditChitRequest,
    MySubmissionDTO,
    RoundPromptInfoDTO,
    SubmissionStatusDTO,
    SubmitChitRequest,
)
from app.services.round_service import get_round_prompt_info
from app.services.submission_service import (
    delete_chit,
    edit_chit,
    get_my_submission,
    get_submission_status,
    submit_chit,
)

router = APIRouter(prefix="/rooms/{roomId}/submission", tags=["Submissions"])

@router.get("/prompt", response_model=ApiResponse[RoundPromptInfoDTO])
async def get_round_prompt_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoundPromptInfoDTO]:
    info = await get_round_prompt_info(db, roomId, participant.id)
    return ApiResponse(data=info)

@router.get("", response_model=ApiResponse[Optional[MySubmissionDTO]])
@router.get("/", response_model=ApiResponse[Optional[MySubmissionDTO]])
async def get_my_submission_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Optional[MySubmissionDTO]]:
    submission = await get_my_submission(db, participant.id, roomId)
    return ApiResponse(data=submission)

@router.get("/status", response_model=ApiResponse[SubmissionStatusDTO])
async def get_submission_status_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SubmissionStatusDTO]:
    result = await get_submission_status(db, participant.id, roomId)
    return ApiResponse(data=result)

@router.post("", response_model=ApiResponse[MySubmissionDTO])
@router.post("/", response_model=ApiResponse[MySubmissionDTO])
async def submit_chit_endpoint(
    payload: SubmitChitRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MySubmissionDTO]:
    submission = await submit_chit(db, participant.id, roomId, payload.body)
    return ApiResponse(data=submission, message="Submitted successfully!")

@router.patch("", response_model=ApiResponse[MySubmissionDTO])
@router.patch("/", response_model=ApiResponse[MySubmissionDTO])
async def edit_chit_endpoint(
    payload: EditChitRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MySubmissionDTO]:
    submission = await edit_chit(db, participant.id, roomId, payload.body)
    return ApiResponse(data=submission, message="Updated successfully.")

@router.delete("", response_model=ApiResponse[DeleteChitDTO])
@router.delete("/", response_model=ApiResponse[DeleteChitDTO])
async def delete_chit_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DeleteChitDTO]:
    result = await delete_chit(db, participant.id, roomId)
    return ApiResponse(data=result, message="Deleted successfully.")
