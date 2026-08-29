from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.room import Room
from app.models.round import GameRound
from app.models.participant import Participant
from app.models.chit import ChitMessage
from app.models.guess import RoundGuess
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

        await AliasService.generate_aliases(db, new_round)
        return new_round

    @staticmethod
    async def advance_to_guessing(db: AsyncSession, room_id: str) -> GameRound:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            raise not_found("No active round found to advance to guessing.")

        now = datetime.now(timezone.utc)
        round_obj.status = RoundStatus.guessing
        round_obj.submissionsClosedAt = now
        db.add(round_obj)

        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if room:
            room.status = RoomStatus.guessing
            db.add(room)

        await db.flush()
        return round_obj

    @staticmethod
    async def advance_to_reveal(db: AsyncSession, room_id: str) -> GameRound:
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj:
            raise not_found("No active round found to reveal.")

        now = datetime.now(timezone.utc)
        round_obj.status = RoundStatus.revealed
        round_obj.identitiesRevealed = True
        round_obj.revealedAt = now
        db.add(round_obj)

        stmt = select(Room).where(Room.id == room_id)
        res = await db.execute(stmt)
        room = res.scalars().first()
        if room:
            if room.currentRoundNumber >= room.totalRounds:
                room.status = RoomStatus.completed
            else:
                room.status = RoomStatus.revealed
            db.add(room)

        await db.flush()
        return round_obj

    @staticmethod
    async def check_all_submissions_done(db: AsyncSession, room_id: str) -> bool:
        """Check if all connected, active participants have submitted a chit for current round."""
        round_obj = await RoundService.get_current_round(db, room_id)
        if not round_obj or round_obj.status != RoundStatus.submissions_open:
            return False

        # Active participants count
        stmt_active = select(func.count()).select_from(Participant).where(
            Participant.roomId == room_id,
            Participant.removed == False,
            Participant.connected == True
        )
        res_active = await db.execute(stmt_active)
        total_active = res_active.scalar() or 0

        if total_active <= 0:
            return False

        # Submitted chits count
        stmt_chits = select(func.count()).select_from(ChitMessage).where(
            ChitMessage.roundId == round_obj.id
        )
        res_chits = await db.execute(stmt_chits)
        submitted_count = res_chits.scalar() or 0

        return submitted_count >= total_active
