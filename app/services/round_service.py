from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.room import Room
from app.models.round import GameRound
from app.models.enums import RoomStatus, RoundStatus
from app.utils.cuid import generate_cuid
from app.services.alias_service import AliasService
from app.errors import not_found, bad_request

class RoundService:
    @staticmethod
    async def get_current_round(db: AsyncSession, room_id: str) -> Optional[GameRound]:
        stmt = (
            select(GameRound)
            .where(GameRound.roomId == room_id)
            .order_by(GameRound.roundNumber.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def start_round(db: AsyncSession, room_id: str) -> GameRound:
        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if not room:
            raise not_found("Room not found.")

        new_round_number = room.currentRoundNumber + 1
        room.currentRoundNumber = new_round_number
        room.status = RoomStatus.submissions_open
        db.add(room)

        now = datetime.now(timezone.utc)
        new_round = GameRound(
            id=generate_cuid(),
            roomId=room_id,
            roundNumber=new_round_number,
            status=RoundStatus.submissions_open,
            aliasEpoch=0,
            identitiesRevealed=False,
            submissionsOpenedAt=now,
            createdAt=now,
        )
        db.add(new_round)
        await db.flush()

        # Generate fresh aliases for the new round
        await AliasService.generate_aliases(db, new_round)
        return new_round

    @staticmethod
    async def open_submissions(db: AsyncSession, room_id: str) -> GameRound:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            return await RoundService.start_round(db, room_id)

        now = datetime.now(timezone.utc)
        round_obj.status = RoundStatus.submissions_open
        round_obj.submissionsOpenedAt = now
        db.add(round_obj)

        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if room:
            room.status = RoomStatus.submissions_open
            db.add(room)

        await db.flush()
        return round_obj

    @staticmethod
    async def close_submissions(db: AsyncSession, room_id: str) -> GameRound:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            raise not_found("No active round found to close.")

        now = datetime.now(timezone.utc)
        round_obj.status = RoundStatus.submissions_closed
        round_obj.submissionsClosedAt = now
        db.add(round_obj)

        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if room:
            room.status = RoomStatus.submissions_closed
            db.add(room)

        await db.flush()
        return round_obj
