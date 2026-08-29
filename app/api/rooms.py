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
    UpdateRoomSettingsRequest,
    RoomCreatedDTO,
    RoomJoinedDTO,
    RoomAvailabilityDTO,
    HostRoomViewDTO,
    PlayerRoomViewDTO,
)
from app.schemas.participant import (
    PlayerActivityItemDTO,
    HostManagePlayerDTO,
    LeaderboardItemDTO,
)
from app.services.room_service import RoomService
from app.services.participant_service import ParticipantService
from app.services.round_service import RoundService
from app.services.guess_service import GuessService
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
        max_players=payload.maxPlayers,
        total_rounds=payload.totalRounds,
        game_mode=payload.gameMode,
        prompt_category=payload.promptCategory,
        custom_prompt=payload.customPrompt
    )
    return ApiResponse(data=result, message=f"Room created successfully! Mode: {payload.gameMode.capitalize()}.")

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
    return ApiResponse(data=result, message=f"Welcome to the room, {payload.displayName}!")

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

@router.patch("/{roomId}/settings", response_model=ApiResponse[dict])
async def update_settings(
    payload: UpdateRoomSettingsRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    room = await RoomService.update_settings(
        db,
        roomId,
        total_rounds=payload.totalRounds,
        max_players=payload.maxPlayers,
        game_mode=payload.gameMode,
        prompt_category=payload.promptCategory,
        custom_prompt=payload.customPrompt
    )
    await emit_room_state_updated(roomId)
    return ApiResponse(
        data={"totalRounds": room.totalRounds, "maxPlayers": room.maxPlayers, "gameMode": room.gameMode},
        message="Room settings updated successfully."
    )

@router.post("/{roomId}/leave", response_model=ApiResponse[dict])
async def leave_room(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db)
):
    await RoomService.leave_room(db, participant)
    await emit_player_left(roomId, participant.displayName, 1)
    await emit_room_state_updated(roomId)
    return ApiResponse(data={"left": True}, message="You have left the room.")

@router.get("/{roomId}/activity", response_model=ApiResponse[List[PlayerActivityItemDTO]])
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
    return ApiResponse(data={"roundNumber": new_round.roundNumber}, message=f"Round {new_round.roundNumber} started!")

@router.post("/{roomId}/next-round", response_model=ApiResponse[dict])
async def start_next_round(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    new_round = await RoundService.start_round(db, roomId)
    await emit_room_state_updated(roomId)
    await emit_player_activity_updated(roomId)
    return ApiResponse(data={"roundNumber": new_round.roundNumber}, message=f"Round {new_round.roundNumber} started!")

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
    removed_participant_id = await ParticipantService.remove_player_by_id(db, roomId, aliasId)
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
    return ApiResponse(data={"locked": locked}, message=f"Room {'locked' if locked else 'unlocked'} successfully.")

@router.post("/{roomId}/end", response_model=ApiResponse[dict])
async def end_room(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db)
):
    await RoomService.end_room(db, roomId)
    await emit_room_ended(roomId)
    return ApiResponse(data={"ended": True}, message="Room has been ended by the host.")
