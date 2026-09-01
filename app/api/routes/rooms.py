from typing import List, Union
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_participant,
    require_owner,
    require_room_member,
)
from app.models.participant import Participant
from app.schemas.common import ApiResponse
from app.schemas.participant import (
    HostManagePlayerDTO,
    PlayerActivityItemDTO,
    RemovePlayerDTO,
)
from app.schemas.room import (
    CreateRoomRequest,
    EndRoomDTO,
    HostRoomViewDTO,
    JoinRoomRequest,
    LeaveRoomDTO,
    LockRoomDTO,
    LockRoomRequest,
    PlayerRoomViewDTO,
    RoomAvailabilityDTO,
    RoomCreatedDTO,
    RoomJoinedDTO,
    RoomSettingsUpdatedDTO,
    StartRoundDTO,
    UpdateRoomSettingsRequest,
)
from app.services.participant_service import (
    get_manageable_players,
    get_player_activity,
    remove_player_by_id,
)
from app.services.room_service import (
    check_availability,
    create_room,
    end_room,
    get_room_view,
    join_room,
    leave_room,
    lock_room,
    update_settings,
)
from app.services.round_service import start_round

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.post("", response_model=ApiResponse[RoomCreatedDTO], status_code=status.HTTP_200_OK)
@router.post("/", response_model=ApiResponse[RoomCreatedDTO], status_code=status.HTTP_200_OK)
async def create_room_endpoint(
    payload: CreateRoomRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoomCreatedDTO]:
    result = await create_room(
        db,
        host_display_name=payload.hostDisplayName,
        title=payload.title,
        max_players=payload.maxPlayers,
        total_rounds=payload.totalRounds,
        game_mode=payload.gameMode,
        prompt_category=payload.promptCategory,
        custom_prompt=payload.customPrompt,
    )
    return ApiResponse(
        data=result,
        message=f"Room created successfully! Mode: {payload.gameMode.capitalize()}.",
    )

@router.post("/join", response_model=ApiResponse[RoomJoinedDTO])
async def join_room_endpoint(
    payload: JoinRoomRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoomJoinedDTO]:
    result = await join_room(
        db,
        room_code=payload.roomCode,
        display_name=payload.displayName,
    )
    return ApiResponse(data=result, message=f"Welcome to the room, {payload.displayName}!")

@router.get("/code/{roomCode}/availability", response_model=ApiResponse[RoomAvailabilityDTO])
async def check_availability_endpoint(
    roomCode: str = Path(...),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoomAvailabilityDTO]:
    result = await check_availability(db, roomCode)
    return ApiResponse(data=result)

@router.get("/current", response_model=ApiResponse[Union[HostRoomViewDTO, PlayerRoomViewDTO]])
async def get_current_room_endpoint(
    participant: Participant = Depends(get_current_participant),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[Union[HostRoomViewDTO, PlayerRoomViewDTO]]:
    result = await get_room_view(db, participant)
    return ApiResponse(data=result)

@router.patch("/{roomId}/settings", response_model=ApiResponse[RoomSettingsUpdatedDTO])
async def update_settings_endpoint(
    payload: UpdateRoomSettingsRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RoomSettingsUpdatedDTO]:
    result = await update_settings(
        db,
        roomId,
        total_rounds=payload.totalRounds,
        max_players=payload.maxPlayers,
        game_mode=payload.gameMode,
        prompt_category=payload.promptCategory,
        custom_prompt=payload.customPrompt,
    )
    return ApiResponse(
        data=result,
        message="Room settings updated successfully.",
    )

@router.post("/{roomId}/leave", response_model=ApiResponse[LeaveRoomDTO])
async def leave_room_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LeaveRoomDTO]:
    result = await leave_room(db, participant)
    return ApiResponse(data=result, message="You have left the room.")

@router.get("/{roomId}/activity", response_model=ApiResponse[List[PlayerActivityItemDTO]])
async def get_activity_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_room_member),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[PlayerActivityItemDTO]]:
    result = await get_player_activity(db, roomId, participant)
    return ApiResponse(data=result)

# Owner Only Endpoints
@router.post("/{roomId}/rounds", response_model=ApiResponse[StartRoundDTO])
async def start_round_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[StartRoundDTO]:
    result = await start_round(db, roomId)
    return ApiResponse(data=result, message=f"Round {result.roundNumber} started!")

@router.post("/{roomId}/next-round", response_model=ApiResponse[StartRoundDTO])
async def start_next_round_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[StartRoundDTO]:
    result = await start_round(db, roomId)
    return ApiResponse(data=result, message=f"Round {result.roundNumber} started!")

@router.get("/{roomId}/players", response_model=ApiResponse[List[HostManagePlayerDTO]])
async def get_players_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[List[HostManagePlayerDTO]]:
    players = await get_manageable_players(db, roomId)
    return ApiResponse(data=players)

@router.post("/{roomId}/players/{aliasId}/remove", response_model=ApiResponse[RemovePlayerDTO])
async def remove_player_endpoint(
    roomId: str = Path(...),
    aliasId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RemovePlayerDTO]:
    result = await remove_player_by_id(db, roomId, aliasId)
    return ApiResponse(data=result, message="Player removed from room.")

@router.post("/{roomId}/lock", response_model=ApiResponse[LockRoomDTO])
async def lock_room_endpoint(
    payload: LockRoomRequest,
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LockRoomDTO]:
    result = await lock_room(db, roomId, payload.locked)
    return ApiResponse(data=result, message=f"Room {'locked' if result.locked else 'unlocked'} successfully.")

@router.post("/{roomId}/end", response_model=ApiResponse[EndRoomDTO])
async def end_room_endpoint(
    roomId: str = Path(...),
    participant: Participant = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[EndRoomDTO]:
    result = await end_room(db, roomId)
    return ApiResponse(data=result, message="Room has been ended by the host.")
