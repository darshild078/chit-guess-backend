from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.room import Room
from app.models.participant import Participant
from app.models.round import GameRound
from app.models.enums import RoomStatus, ParticipantRole, RoundStatus
from app.schemas.room import (
    RoomCreatedDTO,
    RoomJoinedDTO,
    RoomAvailabilityDTO,
    HostRoomViewDTO,
    PlayerRoomViewDTO,
)
from app.utils.room_code import generate_room_code, is_valid_room_code
from app.utils.jwt_helper import sign_participant_token
from app.utils.cuid import generate_cuid
from app.utils.sanitize import sanitize_display_name
from app.errors import bad_request, not_found, conflict, forbidden

class RoomService:
    @staticmethod
    async def create_room(
        db: AsyncSession,
        host_display_name: str,
        title: Optional[str] = None,
        max_players: int = 10
    ) -> RoomCreatedDTO:
        clean_name = sanitize_display_name(host_display_name)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=24)

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
            session_version=1
        )

        return RoomCreatedDTO(
            roomId=room_id,
            roomCode=code,
            participantId=owner_id,
            token=token,
            role=ParticipantRole.owner.value
        )

    @staticmethod
    async def join_room(
        db: AsyncSession,
        room_code: str,
        display_name: str
    ) -> RoomJoinedDTO:
        clean_code = (room_code or "").strip().upper()
        if not is_valid_room_code(clean_code):
            raise bad_request("Invalid room code format. Please check and try again.")

        clean_name = sanitize_display_name(display_name)
        now = datetime.now(timezone.utc)

        stmt = select(Room).where(Room.code == clean_code)
        res = await db.execute(stmt)
        room = res.scalars().first()

        if not room:
            raise not_found("Room not found. Please check your room code.")

        if room.status == RoomStatus.ended:
            raise bad_request("This room has ended. Please join an active room.")

        if room.expiresAt < now:
            raise bad_request("This room has expired. Please create or join a new room.")

        if room.locked:
            raise bad_request("This room is currently locked by the host.")

        # Check existing participant by name in this room
        stmt_part = select(Participant).where(
            Participant.roomId == room.id,
            Participant.displayName == clean_name
        )
        res_part = await db.execute(stmt_part)
        existing_part = res_part.scalars().first()

        if existing_part:
            if existing_part.removed:
                raise bad_request("You have been removed from this room.")
            
            # Reconnect existing participant
            existing_part.connected = True
            existing_part.lastSeenAt = now
            existing_part.sessionVersion += 1
            db.add(existing_part)
            await db.flush()

            token = sign_participant_token(
                participant_id=existing_part.id,
                room_id=room.id,
                role=existing_part.role.value,
                session_version=existing_part.sessionVersion
            )

            return RoomJoinedDTO(
                roomId=room.id,
                participantId=existing_part.id,
                token=token,
                role=existing_part.role.value
            )

        # Count active non-owner participants
        stmt_count = select(func.count()).select_from(Participant).where(
            Participant.roomId == room.id,
            Participant.role == ParticipantRole.player,
            Participant.removed == False
        )
        count_res = await db.execute(stmt_count)
        current_count = count_res.scalar() or 0

        if current_count >= room.maxPlayers:
            raise bad_request("Room is currently full. Please try joining another room.")

        new_id = generate_cuid()
        new_player = Participant(
            id=new_id,
            roomId=room.id,
            displayName=clean_name,
            role=ParticipantRole.player,
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
            session_version=1
        )

        return RoomJoinedDTO(
            roomId=room.id,
            participantId=new_id,
            token=token,
            role=ParticipantRole.player.value
        )

    @staticmethod
    async def check_availability(db: AsyncSession, room_code: str) -> RoomAvailabilityDTO:
        clean_code = (room_code or "").strip().upper()
        if not is_valid_room_code(clean_code):
            return RoomAvailabilityDTO(available=False, reason="Invalid room code.")

        stmt = select(Room).where(Room.code == clean_code)
        res = await db.execute(stmt)
        room = res.scalars().first()

        if not room:
            return RoomAvailabilityDTO(available=False, reason="Room not found.")

        now = datetime.now(timezone.utc)
        if room.status == RoomStatus.ended:
            return RoomAvailabilityDTO(available=False, reason="Room has ended.")

        if room.expiresAt < now:
            return RoomAvailabilityDTO(available=False, reason="Room has expired.")

        if room.locked:
            return RoomAvailabilityDTO(available=False, reason="Room is locked.")

        stmt_count = select(func.count()).select_from(Participant).where(
            Participant.roomId == room.id,
            Participant.role == ParticipantRole.player,
            Participant.removed == False
        )
        count_res = await db.execute(stmt_count)
        current_count = count_res.scalar() or 0

        if current_count >= room.maxPlayers:
            return RoomAvailabilityDTO(available=False, reason="Room is full.")

        return RoomAvailabilityDTO(available=True)

    @staticmethod
    async def get_room_view(
        db: AsyncSession,
        participant: Participant
    ) -> Union[HostRoomViewDTO, PlayerRoomViewDTO]:
        stmt = select(Room).where(Room.id == participant.roomId)
        res = await db.execute(stmt)
        room = res.scalars().first()

        if not room:
            raise not_found("Room not found.")

        # Count active players
        stmt_count = select(func.count()).select_from(Participant).where(
            Participant.roomId == room.id,
            Participant.role == ParticipantRole.player,
            Participant.removed == False,
            Participant.connected == True
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
                playerCount=player_count,
                maxPlayers=room.maxPlayers,
                locked=room.locked,
                isOwner=True,
                expiresAt=room.expiresAt
            )
        else:
            # Find host name
            stmt_host = select(Participant.displayName).where(
                Participant.roomId == room.id,
                Participant.role == ParticipantRole.owner
            )
            res_host = await db.execute(stmt_host)
            host_name = res_host.scalar() or "Host"

            return PlayerRoomViewDTO(
                roomId=room.id,
                roomCode=room.code,
                title=room.title,
                status=room.status.value,
                currentRoundNumber=room.currentRoundNumber,
                playerCount=player_count,
                maxPlayers=room.maxPlayers,
                locked=room.locked,
                isOwner=False,
                hostDisplayName=host_name,
                expiresAt=room.expiresAt
            )

    @staticmethod
    async def leave_room(db: AsyncSession, participant: Participant) -> None:
        participant.connected = False
        participant.lastSeenAt = datetime.now(timezone.utc)
        db.add(participant)
        await db.flush()

    @staticmethod
    async def lock_room(db: AsyncSession, room_id: str, locked: bool) -> bool:
        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if not room:
            raise not_found("Room not found.")

        room.locked = locked
        db.add(room)
        await db.flush()
        return locked

    @staticmethod
    async def end_room(db: AsyncSession, room_id: str) -> None:
        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if not room:
            raise not_found("Room not found.")

        room.status = RoomStatus.ended
        db.add(room)
        await db.flush()
