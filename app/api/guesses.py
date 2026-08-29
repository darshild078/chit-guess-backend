from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.room_member import require_room_member
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.guess import (
    RoundWordDTO,
    SubmitGuessesRequest,
    RoundResultsDTO,
)
from app.schemas.participant import LeaderboardItemDTO
from app.services.guess_service import GuessService
from app.services.round_service import RoundService
from app.sockets.emitters import (
    emit_round_revealed,
    emit_game_completed,
    emit_player_activity_updated,
)

router = APIRouter(prefix="/rooms/{roomId}", tags=["Guesses & Results"])

@router.get("/round/words", response_model=ApiResponse[List[RoundWordDTO]])
async def get_round_words(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    words = await GuessService.get_round_words(db, participant.id, roomId)
    return ApiResponse(data=words)

@router.post("/round/guesses", response_model=ApiResponse[dict])
async def submit_guesses(
    payload: SubmitGuessesRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    await GuessService.submit_guesses(db, participant.id, roomId, payload.guesses)
    await emit_player_activity_updated(roomId)

    # Check if all participants have submitted guesses -> auto-reveal!
    all_guessed = await GuessService.check_all_guesses_submitted(db, roomId)
    if all_guessed:
        results = await GuessService.calculate_and_reveal_scores(db, roomId)
        if results.isFinalRound:
            await emit_game_completed(roomId, results.model_dump(mode="json"))
        else:
            await emit_round_revealed(roomId, results.model_dump(mode="json"))

    return ApiResponse(
        data={"lockedIn": True},
        message="Guesses locked in! Waiting for other players..."
    )

@router.get("/round/results", response_model=ApiResponse[RoundResultsDTO])
async def get_round_results(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    results = await GuessService.calculate_and_reveal_scores(db, roomId)
    return ApiResponse(data=results)

@router.get("/leaderboard", response_model=ApiResponse[List[LeaderboardItemDTO]])
async def get_leaderboard(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    leaderboard = await GuessService.get_leaderboard(db, roomId)
    return ApiResponse(data=leaderboard)
