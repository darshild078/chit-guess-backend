from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_room_member
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.guess import (
    ChameleonGuessResponseDTO,
    ChameleonGuessWordRequest,
    RoundResultsDTO,
    RoundWordDTO,
    SubmitGuessesRequest,
    SubmitGuessesResponseDTO,
)
from app.schemas.participant import LeaderboardItemDTO
from app.services.guess_service import (
    calculate_and_reveal_scores,
    get_leaderboard,
    get_round_words,
    submit_chameleon_word_guess,
    submit_guesses,
)

router = APIRouter(prefix="/rooms/{roomId}", tags=["Guesses & Results"])

@router.get("/round/words", response_model=ApiResponse[List[RoundWordDTO]])
async def get_round_words_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[RoundWordDTO]]:
    words = await get_round_words(db, participant.id, roomId)
    return ApiResponse(data=words)

@router.post("/round/guesses", response_model=ApiResponse[SubmitGuessesResponseDTO])
async def submit_guesses_endpoint(
    payload: SubmitGuessesRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SubmitGuessesResponseDTO]:
    result = await submit_guesses(db, participant.id, roomId, payload.guesses)
    return ApiResponse(
        data=result,
        message="Guesses locked in! Waiting for other players...",
    )

@router.post("/round/chameleon-guess", response_model=ApiResponse[ChameleonGuessResponseDTO])
async def chameleon_guess_word_endpoint(
    payload: ChameleonGuessWordRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ChameleonGuessResponseDTO]:
    result = await submit_chameleon_word_guess(db, participant.id, roomId, payload.word)
    return ApiResponse(
        data=result,
        message="Correct! You stole the secret word!" if result.isCorrect else "Incorrect! The secret word was not guessed.",
    )

@router.get("/round/results", response_model=ApiResponse[RoundResultsDTO])
async def get_round_results_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoundResultsDTO]:
    results = await calculate_and_reveal_scores(db, roomId)
    return ApiResponse(data=results)

@router.get("/leaderboard", response_model=ApiResponse[List[LeaderboardItemDTO]])
async def get_leaderboard_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[LeaderboardItemDTO]]:
    leaderboard = await get_leaderboard(db, roomId)
    return ApiResponse(data=leaderboard)
