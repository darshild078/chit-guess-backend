from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.constants import (
    DEFAULT_MAX_PLAYERS,
    DEFAULT_TOTAL_ROUNDS,
    GameMode,
    ParticipantRole,
    PromptCategory,
    ROOM_EXPIRY_HOURS,
    RoomStatus,
)
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.core.logging import log_event
from app.core.security import sign_participant_token
from app.models.participant import Participant
from app.models.room import Room
from app.schemas.room import (
    EndRoomDTO,
    HostRoomViewDTO,
    LeaveRoomDTO,
    LockRoomDTO,
    PlayerRoomViewDTO,
    RoomAvailabilityDTO,
    RoomCreatedDTO,
    RoomJoinedDTO,
    RoomSettingsUpdatedDTO,
)
from app.sockets.emitters import (
    emit_player_joined,
    emit_player_left,
    emit_room_ended,
    emit_room_state_updated,
)
from app.utils.cuid import generate_cuid
from app.utils.room_code import generate_room_code, is_valid_room_code
from app.utils.sanitize import sanitize_display_name

async def create_room(
    db: AsyncSession,
    host_display_name: str,
    title: Optional[str] = None,
    max_players: int = DEFAULT_MAX_PLAYERS,
    total_rounds: int = DEFAULT_TOTAL_ROUNDS,
    game_mode: str = GameMode.confessions.value,
    prompt_category: str = PromptCategory.general.value,
    custom_prompt: Optional[str] = None,
) -> RoomCreatedDTO:
    clean_name = sanitize_display_name(host_display_name)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ROOM_EXPIRY_HOURS)

    # Generate unique room code
    for _ in range(10):
        code = generate_room_code()
        stmt = select(Room).where(Room.code == code)
        res = await db.execute(stmt)
        if not res.scalars().first():
            break
    else:
        code = generate_room_code()

    room_id = generate_cuid()
    owner_id = generate_cuid()

    room = Room(
        id=room_id,
        code=code,
        title=title.strip() if title else None,
        status=RoomStatus.lobby,
        ownerParticipantId=owner_id,
        maxPlayers=max_players,
        totalRounds=total_rounds,
        gameMode=game_mode or GameMode.confessions.value,
        promptCategory=prompt_category or PromptCategory.general.value,
        customPrompt=custom_prompt.strip() if custom_prompt else None,
        locked=False,
        currentRoundNumber=0,
        expiresAt=expires_at,
        createdAt=now,
        updatedAt=now,
    )
    db.add(room)

    owner = Participant(
        id=owner_id,
        roomId=room_id,
        displayName=clean_name,
        role=ParticipantRole.owner,
        score=0,
        connected=True,
        removed=False,
        sessionVersion=1,
        joinedAt=now,
        lastSeenAt=now,
    )
    db.add(owner)
    await db.flush()

    token = sign_participant_token(
        participant_id=owner_id,
        room_id=room_id,
        role=ParticipantRole.owner.value,
        session_version=1,
    )

    log_event(
        action="create_room",
        status="success",
        room_id=room_id,
        user_id=owner_id,
        message=f"Room {code} created successfully",
    )

    return RoomCreatedDTO(
        roomId=room_id,
        roomCode=code,
        participantId=owner_id,
        token=token,
        role=ParticipantRole.owner.value,
        totalRounds=total_rounds,
        gameMode=room.gameMode,
    )

async def join_room(
    db: AsyncSession,
    room_code: str,
    display_name: str,
) -> RoomJoinedDTO:
    clean_code = (room_code or "").strip().upper()
    if not is_valid_room_code(clean_code):
        raise BadRequestException("Invalid room code format. Room codes must be exactly 6 uppercase letters and numbers.")

    clean_name = sanitize_display_name(display_name)
    now = datetime.now(timezone.utc)

    stmt = select(Room).where(Room.code == clean_code)
    res = await db.execute(stmt)
    room = res.scalars().first()

    if not room:
        raise NotFoundException("Room not found. Please verify the 6-letter room code with the host.")

    if room.status == RoomStatus.ended:
        raise BadRequestException("This room has ended. The host has concluded the game.")

    if room.expiresAt < now:
        raise BadRequestException("This room has expired after 24 hours of inactivity. Please create or join a new room.")

    if room.locked:
        raise BadRequestException("This room is currently locked by the host and cannot accept new players.")

    stmt_part = select(Participant).where(
        Participant.roomId == room.id,
        Participant.displayName == clean_name,
    )
    res_part = await db.execute(stmt_part)
    existing_part = res_part.scalars().first()

    if existing_part:
        if existing_part.removed:
            raise BadRequestException("You have been removed from this room by the host and cannot rejoin.")

        existing_part.connected = True
        existing_part.lastSeenAt = now
        existing_part.sessionVersion += 1
        db.add(existing_part)
        await db.flush()

        token = sign_participant_token(
            participant_id=existing_part.id,
            room_id=room.id,
            role=existing_part.role.value,
            session_version=existing_part.sessionVersion,
        )

        log_event(
            action="rejoin_room",
            status="success",
            room_id=room.id,
            user_id=existing_part.id,
            message=f"Player {clean_name} reconnected to room {clean_code}",
        )

        await emit_player_joined(room.id, clean_name, 1)
        await emit_room_state_updated(room.id)

        return RoomJoinedDTO(
            roomId=room.id,
            participantId=existing_part.id,
            token=token,
            role=existing_part.role.value,
        )

    stmt_count = select(func.count()).select_from(Participant).where(
        Participant.roomId == room.id,
        Participant.removed == False,
    )
    count_res = await db.execute(stmt_count)
    current_count = count_res.scalar() or 0

    if current_count >= room.maxPlayers:
        raise BadRequestException(f"This room is full (maximum limit of {room.maxPlayers} players reached).")

    new_id = generate_cuid()
    new_player = Participant(
        id=new_id,
        roomId=room.id,
        displayName=clean_name,
        role=ParticipantRole.player,
        score=0,
        connected=True,
        removed=False,
        sessionVersion=1,
        joinedAt=now,
        lastSeenAt=now,
    )
    db.add(new_player)
    await db.flush()

    token = sign_participant_token(
        participant_id=new_id,
        room_id=room.id,
        role=ParticipantRole.player.value,
        session_version=1,
    )

    log_event(
        action="join_room",
        status="success",
        room_id=room.id,
        user_id=new_id,
        message=f"Player {clean_name} joined room {clean_code}",
    )

    await emit_player_joined(room.id, clean_name, 1)
    await emit_room_state_updated(room.id)

    return RoomJoinedDTO(
        roomId=room.id,
        participantId=new_id,
        token=token,
        role=ParticipantRole.player.value,
    )

async def check_availability(db: AsyncSession, room_code: str) -> RoomAvailabilityDTO:
    clean_code = (room_code or "").strip().upper()
    if not is_valid_room_code(clean_code):
        return RoomAvailabilityDTO(available=False, reason="Invalid room code format.")

    stmt = select(Room).where(Room.code == clean_code)
    res = await db.execute(stmt)
    room = res.scalars().first()

    if not room:
        return RoomAvailabilityDTO(available=False, reason="Room does not exist.")

    now = datetime.now(timezone.utc)
    if room.status == RoomStatus.ended:
        return RoomAvailabilityDTO(available=False, reason="This room has ended.")

    if room.expiresAt < now:
        return RoomAvailabilityDTO(available=False, reason="This room has expired.")

    if room.locked:
        return RoomAvailabilityDTO(available=False, reason="This room is currently locked.")

    stmt_count = select(func.count()).select_from(Participant).where(
        Participant.roomId == room.id,
        Participant.removed == False,
    )
    count_res = await db.execute(stmt_count)
    current_count = count_res.scalar() or 0

    if current_count >= room.maxPlayers:
        return RoomAvailabilityDTO(available=False, reason=f"Room is full ({room.maxPlayers} max players).")

    return RoomAvailabilityDTO(available=True)

async def get_room_view(
    db: AsyncSession,
    participant: Participant,
) -> Union[HostRoomViewDTO, PlayerRoomViewDTO]:
    stmt = select(Room).where(Room.id == participant.roomId)
    res = await db.execute(stmt)
    room = res.scalars().first()

    if not room:
        raise NotFoundException("Room not found. It may have been ended or deleted.")

    stmt_count = select(func.count()).select_from(Participant).where(
        Participant.roomId == room.id,
        Participant.removed == False,
        Participant.connected == True,
    )
    count_res = await db.execute(stmt_count)
    player_count = count_res.scalar() or 0

    if participant.role == ParticipantRole.owner:
        return HostRoomViewDTO(
            roomId=room.id,
            roomCode=room.code,
            title=room.title,
            status=room.status.value,
            currentRoundNumber=room.currentRoundNumber,
            totalRounds=room.totalRounds,
            gameMode=room.gameMode or GameMode.confessions.value,
            promptCategory=room.promptCategory or PromptCategory.general.value,
            customPrompt=room.customPrompt,
            playerCount=player_count,
            maxPlayers=room.maxPlayers,
            locked=room.locked,
            isOwner=True,
            expiresAt=room.expiresAt,
        )
    else:
        stmt_host = select(Participant.displayName).where(
            Participant.roomId == room.id,
            Participant.role == ParticipantRole.owner,
        )
        res_host = await db.execute(stmt_host)
        host_name = res_host.scalar() or "Host"

        return PlayerRoomViewDTO(
            roomId=room.id,
            roomCode=room.code,
            title=room.title,
            status=room.status.value,
            currentRoundNumber=room.currentRoundNumber,
            totalRounds=room.totalRounds,
            gameMode=room.gameMode or GameMode.confessions.value,
            promptCategory=room.promptCategory or PromptCategory.general.value,
            customPrompt=room.customPrompt,
            playerCount=player_count,
            maxPlayers=room.maxPlayers,
            locked=room.locked,
            isOwner=False,
            hostDisplayName=host_name,
            expiresAt=room.expiresAt,
        )

async def leave_room(db: AsyncSession, participant: Participant) -> LeaveRoomDTO:
    participant.connected = False
    participant.lastSeenAt = datetime.now(timezone.utc)
    db.add(participant)
    await db.flush()

    await emit_player_left(participant.roomId, participant.displayName, 1)
    await emit_room_state_updated(participant.roomId)

    return LeaveRoomDTO(left=True)

async def lock_room(db: AsyncSession, room_id: str, locked: bool) -> LockRoomDTO:
    stmt = select(Room).where(Room.id == room_id)
    res = await db.execute(stmt)
    room = res.scalars().first()
    if not room:
        raise NotFoundException("Room not found.")

    room.locked = locked
    db.add(room)
    await db.flush()

    await emit_room_state_updated(room_id)
    return LockRoomDTO(locked=locked)

async def update_settings(
    db: AsyncSession,
    room_id: str,
    total_rounds: Optional[int] = None,
    max_players: Optional[int] = None,
    game_mode: Optional[str] = None,
    prompt_category: Optional[str] = None,
    custom_prompt: Optional[str] = None,
) -> RoomSettingsUpdatedDTO:
    stmt = select(Room).where(Room.id == room_id)
    res = await db.execute(stmt)
    room = res.scalars().first()
    if not room:
        raise NotFoundException("Room not found.")

    if total_rounds is not None:
        room.totalRounds = total_rounds
    if max_players is not None:
        room.maxPlayers = max_players
    if game_mode is not None:
        room.gameMode = game_mode
    if prompt_category is not None:
        room.promptCategory = prompt_category
    if custom_prompt is not None:
        room.customPrompt = custom_prompt.strip() if custom_prompt else None

    db.add(room)
    await db.flush()

    await emit_room_state_updated(room_id)

    return RoomSettingsUpdatedDTO(
        totalRounds=room.totalRounds,
        maxPlayers=room.maxPlayers,
        gameMode=room.gameMode,
    )

async def end_room(db: AsyncSession, room_id: str) -> EndRoomDTO:
    stmt = select(Room).where(Room.id == room_id)
    res = await db.execute(stmt)
    room = res.scalars().first()
    if not room:
        raise NotFoundException("Room not found.")

    room.status = RoomStatus.ended
    db.add(room)
    await db.flush()

    await emit_room_ended(room_id)
    return EndRoomDTO(ended=True)


