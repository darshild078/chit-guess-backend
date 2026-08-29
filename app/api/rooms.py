from typing import List, Union
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_participant
from app.dependencies.room_member import require_room_member
from app.dependencies.owner import require_owner
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.room import (
    CreateRoomRequest,
    JoinRoomRequest,
    LockRoomRequest,
    RoomCreatedDTO,
    RoomJoinedDTO,
    RoomAvailabilityDTO,
    HostRoomViewDTO,
    PlayerRoomViewDTO,
)
from app.schemas.participant import (
    PlayerActivityItemDTO,
    HostActivityItemDTO,
    HostManagePlayerDTO,
)
from app.schemas.reveal import RevealResultsDTO
from app.services.room_service import RoomService
from app.services.participant_service import ParticipantService
from app.services.round_service import RoundService
from app.services.alias_service import AliasService
from app.services.reveal_service import RevealService
from app.sockets.emitters import (
    emit_room_state_updated,
    emit_player_joined,
    emit_player_left,
    emit_player_removed,
    emit_room_ended,
    emit_player_activity_updated,
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.post("", response_model=ApiResponse[RoomCreatedDTO])
@router.post("/", response_model=ApiResponse[RoomCreatedDTO])
async def create_room(
    payload: CreateRoomRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await RoomService.create_room(
        db,
        host_display_name=payload.hostDisplayName,
        title=payload.title,
        max_players=payload.maxPlayers
    )
    return ApiResponse(data=result, message="Room created successfully.")

@router.post("/join", response_model=ApiResponse[RoomJoinedDTO])
async def join_room(
    payload: JoinRoomRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await RoomService.join_room(
        db,
        room_code=payload.roomCode,
        display_name=payload.displayName
    )
    await emit_player_joined(result.roomId, payload.displayName, 1)
    await emit_room_state_updated(result.roomId)
    return ApiResponse(data=result, message="Joined room successfully.")

@router.get("/code/{roomCode}/availability", response_model=ApiResponse[RoomAvailabilityDTO])
async def check_availability(
    roomCode: str = Path(...),
    db: AsyncSession = Depends(get_db)
):
    result = await RoomService.check_availability(db, roomCode)
    return ApiResponse(data=result)

@router.get("/current", response_model=ApiResponse[Union[HostRoomViewDTO, PlayerRoomViewDTO]])
async def get_current_room(
    participant: Participant = Depends(get_current_participant),
    db: AsyncSession = Depends(get_db)
):
    result = await RoomService.get_room_view(db, participant)
    return ApiResponse(data=result)

@router.post("/{roomId}/leave", response_model=ApiResponse[dict])
async def leave_room(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    await RoomService.leave_room(db, participant)
    await emit_player_left(roomId, participant.displayName, 1)
    await emit_room_state_updated(roomId)
    return ApiResponse(data={"left": True}, message="Left room.")

@router.get("/{roomId}/activity", response_model=ApiResponse[List[Union[PlayerActivityItemDTO, HostActivityItemDTO]]])
async def get_activity(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    result = await ParticipantService.get_player_activity(db, roomId, participant)
    return ApiResponse(data=result)

# Owner Only Endpoints
@router.post("/{roomId}/rounds", response_model=ApiResponse[dict])
async def start_round(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    new_round = await RoundService.start_round(db, roomId)
    await emit_room_state_updated(roomId)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data={"roundNumber": new_round.roundNumber}, message="New round started.")

@router.post("/{roomId}/submissions/open", response_model=ApiResponse[dict])
async def open_submissions(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    await RoundService.open_submissions(db, roomId)
    await emit_room_state_updated(roomId)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data={"submissionsOpen": True}, message="Submissions opened.")

@router.post("/{roomId}/submissions/close", response_model=ApiResponse[dict])
async def close_submissions(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    await RoundService.close_submissions(db, roomId)
    await emit_room_state_updated(roomId)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data={"submissionsClosed": True}, message="Submissions closed.")

@router.post("/{roomId}/aliases/shuffle", response_model=ApiResponse[dict])
async def shuffle_aliases(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    round_obj = await RoundService.get_current_round(db, roomId)
    if round_obj:
        await AliasService.reshuffle_aliases(db, round_obj)
        await emit_player_activity_updated(roomId)
    return ApiResponse(data={"shuffled": True}, message="Aliases reshuffled.")

@router.post("/{roomId}/reveal", response_model=ApiResponse[RevealResultsDTO])
async def reveal_identities(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    results = await RevealService.reveal_identities(db, roomId)
    await emit_room_state_updated(roomId)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data=results, message="Identities revealed.")

@router.get("/{roomId}/results", response_model=ApiResponse[RevealResultsDTO])
async def get_results(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    results = await RevealService.get_revealed_results(db, roomId)
    return ApiResponse(data=results)

@router.get("/{roomId}/players", response_model=ApiResponse[List[HostManagePlayerDTO]])
async def get_players(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    players = await ParticipantService.get_manageable_players(db, roomId)
    return ApiResponse(data=players)

@router.post("/{roomId}/players/{aliasId}/remove", response_model=ApiResponse[dict])
async def remove_player(
    roomId: str = Path(...),
    aliasId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    removed_participant_id = await ParticipantService.remove_player_by_alias(db, roomId, aliasId)
    await emit_player_removed(removed_participant_id)
    await emit_room_state_updated(roomId)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data={"removed": True}, message="Player removed from room.")

@router.post("/{roomId}/lock", response_model=ApiResponse[dict])
async def lock_room(
    payload: LockRoomRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    locked = await RoomService.lock_room(db, roomId, payload.locked)
    await emit_room_state_updated(roomId)
    return ApiResponse(data={"locked": locked}, message=f"Room {'locked' if locked else 'unlocked'}.")

@router.post("/{roomId}/end", response_model=ApiResponse[dict])
async def end_room(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    await RoomService.end_room(db, roomId)
    await emit_room_ended(roomId)
    return ApiResponse(data={"ended": True}, message="Room ended.")
