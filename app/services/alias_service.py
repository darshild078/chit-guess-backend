import secrets
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.round import GameRound
from app.models.participant import Participant
from app.models.alias import RoundAlias
from app.models.enums import ParticipantRole
from app.utils.cuid import generate_cuid, generate_opaque_id

class AliasService:
    @staticmethod
    async def generate_aliases(db: AsyncSession, round_obj: GameRound) -> List[RoundAlias]:
        """
        Assign anonymous sequential numbers (Player 1, Player 2, etc.)
        and opaque random IDs to all non-owner, active participants.
        Order is shuffled cryptographically each epoch.
        """
        # Fetch active players for the room (exclude owner)
        stmt = (
            select(Participant)
            .where(
                Participant.roomId == round_obj.roomId,
                Participant.role == ParticipantRole.player,
                Participant.removed == False,
            )
            .order_by(Participant.joinedAt.asc())
        )
        result = await db.execute(stmt)
        players = list(result.scalars().all())

        if not players:
            return []

        # Securely shuffle player list
        secure_random = secrets.SystemRandom()
        shuffled_players = list(players)
        secure_random.shuffle(shuffled_players)

        aliases = []
        for idx, player in enumerate(shuffled_players, start=1):
            alias = RoundAlias(
                id=generate_cuid(),
                roundId=round_obj.id,
                aliasEpoch=round_obj.aliasEpoch,
                participantId=player.id,
                aliasNumber=idx,
                opaqueAliasId=generate_opaque_id(),
            )
            db.add(alias)
            aliases.append(alias)

        await db.flush()
        return aliases

    @staticmethod
    async def get_or_create_aliases_for_epoch(db: AsyncSession, round_obj: GameRound) -> List[RoundAlias]:
        stmt = select(RoundAlias).where(
            RoundAlias.roundId == round_obj.id,
            RoundAlias.aliasEpoch == round_obj.aliasEpoch
        ).order_by(RoundAlias.aliasNumber.asc())
        result = await db.execute(stmt)
        existing = list(result.scalars().all())

        if existing:
            return existing

        return await AliasService.generate_aliases(db, round_obj)

    @staticmethod
    async def reshuffle_aliases(db: AsyncSession, round_obj: GameRound) -> List[RoundAlias]:
        round_obj.aliasEpoch += 1
        db.add(round_obj)
        await db.flush()
        return await AliasService.generate_aliases(db, round_obj)

    @staticmethod
    async def get_alias_mapping_by_participant(db: AsyncSession, round_id: str, alias_epoch: int) -> Dict[str, RoundAlias]:
        stmt = select(RoundAlias).where(
            RoundAlias.roundId == round_id,
            RoundAlias.aliasEpoch == alias_epoch
        )
        result = await db.execute(stmt)
        aliases = list(result.scalars().all())
        return {alias.participantId: alias for alias in aliases}

    @staticmethod
    async def resolve_opaque_alias_id(db: AsyncSession, opaque_alias_id: str) -> Optional[RoundAlias]:
        stmt = select(RoundAlias).where(RoundAlias.opaqueAliasId == opaque_alias_id)
        result = await db.execute(stmt)
        return result.scalars().first()
